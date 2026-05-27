"""AI 内容生成服务 — 航运周报 / 风险预警 / 公约更新解读"""
from datetime import datetime, timedelta

from openai import OpenAI

from ..core.config import settings
from .embedding_service import embedding_service
from .chroma_store import chroma_store
from .search_service import search_service


class ReportGenerator:
    """海事报告自动生成器"""

    REPORT_TYPES = {
        "weekly_shipping": {
            "name": "周度航运市场简报",
            "system_prompt": """你是一位资深的航运市场分析师。请根据提供的参考资料和互联网信息，生成一份专业的《周度航运市场简报》。

报告需包含以下章节：
1. **本周运价概览**：集装箱/散货/油轮运价变化趋势
2. **港口动态**：主要港口拥堵、罢工、天气影响
3. **政策法规**：本周重要海事政策更新
4. **市场热点**：本周重大航运事件
5. **下周展望**：风险提示与趋势预判

语言专业、数据准确、引用来源。格式使用 Markdown。""",
        },
        "risk_alert": {
            "name": "航线风险预警报告",
            "system_prompt": """你是一位航运安全与风险管理专家。请根据提供的参考资料，生成一份《航线风险预警报告》。

报告需包含：
1. **高风险区域**：战争/海盗/制裁影响区域
2. **港口风险**：拥堵、罢工、天气预警
3. **地缘政治**：影响航运的国际事件
4. **安全建议**：具体应对措施

聚焦于风险和安全，提供可操作的建议。格式使用 Markdown。""",
        },
        "convention_update": {
            "name": "国际海事公约更新解读",
            "system_prompt": """你是一位国际海事法规专家。请根据提供的参考资料，生成一份《国际海事公约更新解读》。

报告需包含：
1. **最新公约动态**：IMO 等组织的新规/修订
2. **重点解读**：对行业影响最大的条款
3. **合规建议**：航运企业应如何应对
4. **生效时间线**：关键日期提醒

语言准确、引用权威来源、避免误导。格式使用 Markdown。""",
        },
    }

    def __init__(self):
        self._client = None
        self.model = settings.CHAT_MODEL

    @property
    def client(self):
        if self._client is None:
            self._client = OpenAI(
                api_key=settings.DASHSCOPE_API_KEY,
                base_url=settings.DASHSCOPE_BASE_URL,
            )
        return self._client

    async def generate(self, report_type: str, time_range: str = "week") -> dict:
        """生成报告"""
        report_config = self.REPORT_TYPES.get(report_type)
        if not report_config:
            return {"success": False, "title": "", "content": f"不支持的报告类型: {report_type}", "sources": []}

        # 确定时间范围
        days = {"week": 7, "month": 30, "quarter": 90}.get(time_range, 7)
        date_start = datetime.now() - timedelta(days=days)
        date_str = date_start.strftime("%Y-%m-%d")

        # 构建搜索查询
        search_queries = self._get_search_queries(report_type)

        # 从知识库检索相关内容
        knowledge_context = ""
        for query in search_queries[:2]:
            try:
                q_embedding = embedding_service.embed_text(query)
                hits = chroma_store.search(query_embedding=q_embedding, top_k=3)
                if hits:
                    knowledge_context += "\n[知识库相关内容]\n"
                    for h in hits:
                        knowledge_context += f"- {h['title']}: {h['content'][:300]}...\n"
            except Exception:
                pass

        # 联网搜索
        internet_context = ""
        for query in search_queries[:2]:
            ctx = await search_service.search_and_format(query, num=3)
            internet_context += ctx

        # 合并上下文
        full_context = f"时间范围: {date_str} 至今 ({time_range})\n\n{knowledge_context}\n{internet_context}"

        if len(full_context) < 200:
            return {
                "success": False,
                "title": report_config["name"],
                "content": "知识库和互联网中暂无足够信息生成此报告。请先收藏更多相关文档。",
                "sources": [],
            }

        # 调用 LLM 生成报告
        title_prompt = f"请为一份{report_config['name']}生成一个简洁的标题（含日期范围）。只输出标题，不要其他内容。"
        title_resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": title_prompt}],
            temperature=0.3, max_tokens=50,
        )
        title = title_resp.choices[0].message.content.strip()

        content_resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": report_config["system_prompt"]},
                {"role": "user", "content": f"参考资料：\n{full_context}\n\n请生成报告："},
            ],
            temperature=0.3, max_tokens=3000,
        )
        content = content_resp.choices[0].message.content.strip()

        return {
            "success": True,
            "title": title,
            "content": content,
            "sources": [],
            "generated_at": datetime.now().isoformat(),
        }

    def _get_search_queries(self, report_type: str) -> list[str]:
        if report_type == "weekly_shipping":
            return [
                "本周集装箱运价指数 SCFI CCFI 最新",
                "全球港口拥堵 航运新闻 本周",
                "国际航运政策 法规更新 最新",
                "航运市场热点 船舶事故 最新一周",
            ]
        elif report_type == "risk_alert":
            return [
                "红海 航运安全 最新风险",
                "全球海盗袭击 航运 最新",
                "港口罢工 天气预警 航运",
            ]
        elif report_type == "convention_update":
            return [
                "IMO 国际海事组织 最新公约 修订",
                "MARPOL SOLAS 最新修正案",
                "航运碳排放 欧盟ETS 最新政策",
            ]
        return ["航运 海事 最新新闻"]


report_generator = ReportGenerator()
