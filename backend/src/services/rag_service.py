"""RAG问答服务 - 检索增强生成"""
import json
from typing import List, Dict, Any, Optional

from openai import OpenAI

from ..core.config import config
from ..models.document import ChatRequest, ChatResponse
from .embedding_service import embedding_service
from .chroma_store import chroma_store
from .hybrid_search import hybrid_search


class RAGService:
    """RAG问答服务"""

    def __init__(self):
        self._client = None
        self.model = config.CHAT_MODEL
        self.top_k = config.TOP_K

    @property
    def client(self):
        """延迟创建 OpenAI 客户端（避免无 API Key 时导入失败）"""
        if self._client is None:
            self._client = OpenAI(
                api_key=config.DASHSCOPE_API_KEY,
                base_url=config.DASHSCOPE_BASE_URL,
            )
        return self._client

    def chat(self, request: ChatRequest) -> ChatResponse:
        """知识库问答

        Args:
            request: 聊天请求

        Returns:
            ChatResponse 包含回答和来源
        """
        # 1. 将查询向量化
        query_embedding = embedding_service.embed_text(request.message)

        # 2. 向量检索
        hits = chroma_store.search(
            query_embedding=query_embedding,
            top_k=self.top_k * 2,  # 检索更多，后续用混合排序筛选
            doc_filter=request.doc_filter,
        )

        if not hits:
            return ChatResponse(
                answer="知识库中暂未找到相关内容。请尝试上传相关文档后再提问。",
                sources=[],
                confidence=0.0,
            )

        # 3. 混合相似度重排序
        reranked = self._rerank(hits, request.message, request.tag_filter)

        # 4. 取Top-K
        top_results = reranked[:self.top_k]

        # 5. 构建Prompt上下文
        context = self._build_context(top_results)

        # 6. 调用LLM生成回答
        answer = self._generate_answer(request.message, context)

        # 7. 组装响应
        sources = [
            {
                "doc_id": r.doc_id,
                "title": r.title,
                "content": r.content[:200] + "..." if len(r.content) > 200 else r.content,
                "score": r.score,
                "url": getattr(r, 'url', ''),
            }
            for r in top_results
        ]

        # 计算置信度：Top1得分的sigmoid变换
        confidence = 1 / (1 + 2.718 ** (-5 * (top_results[0].score - 0.6)))

        return ChatResponse(
            answer=answer,
            sources=sources,
            confidence=round(min(confidence, 1.0), 2),
        )

    def _rerank(
        self,
        hits: List[Dict[str, Any]],
        query: str,
        tag_filter: Optional[Any],
    ) -> List[Any]:
        """使用混合相似度对检索结果重排序"""
        from ..models.document import SearchResult, DocumentTags

        results = []
        for hit in hits:
            # 计算各维度得分
            vector_score = hybrid_search.compute_vector_score(hit.get("distance", 0.5))
            keyword_score = hybrid_search.compute_keyword_score(query, hit.get("content", ""))
            time_score = hybrid_search.compute_time_score(hit.get("created_at", ""))

            tags = hit.get("tags", {})
            tag_score = hybrid_search.compute_tag_score(
                tag_filter if isinstance(tag_filter, DocumentTags) else None,
                tags,
            )

            # 融合得分
            fused_score = hybrid_search.fuse_scores(
                vector_score, keyword_score, time_score, tag_score,
            )

            result = SearchResult(
                doc_id=hit.get("doc_id", ""),
                title=hit.get("title", ""),
                content=hit.get("content", ""),
                score=round(fused_score, 4),
                vector_score=round(vector_score, 4),
                keyword_score=round(keyword_score, 4),
                time_score=round(time_score, 4),
                tag_score=round(tag_score, 4),
                tags=DocumentTags(
                    business_type=tags.get("business_type", []),
                    geographic_region=tags.get("geographic_region", []),
                    topic_category=tags.get("topic_category", []),
                    event_nature=tags.get("event_nature", []),
                ),
            )
            results.append(result)

        # 按融合得分降序
        results.sort(key=lambda x: x.score, reverse=True)
        return results

    def _build_context(self, results: List[Any]) -> str:
        """构建RAG上下文"""
        context_parts = []
        for i, r in enumerate(results, 1):
            part = f"[文档{i}] {r.title}\n{r.content}\n"
            if r.tags:
                tags_str = (
                    f"标签: 业务-{','.join(r.tags.business_type[:2])} | "
                    f"区域-{','.join(r.tags.geographic_region[:2])} | "
                    f"主题-{','.join(r.tags.topic_category[:2])}"
                )
                part += f"{tags_str}\n"
            context_parts.append(part)

        return "\n".join(context_parts)

    def _generate_answer(self, question: str, context: str) -> str:
        """调用LLM生成回答"""
        system_prompt = """你是一位专业的海事航运领域知识助手。请根据提供的参考资料回答用户问题。

要求：
1. 回答必须基于提供的参考资料，不要编造信息
2. 如果参考资料不足以回答问题，请明确说明
3. 回答要专业、准确、简洁
4. 适当引用参考文档的编号，如"根据文档1..."
5. 如果涉及多个方面，请分点说明
"""

        user_prompt = f"""参考资料：
{context}

用户问题：{question}

请基于以上参考资料回答问题："""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1500,
        )

        return response.choices[0].message.content.strip()


# 全局实例
rag_service = RAGService()
