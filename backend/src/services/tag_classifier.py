"""标签分类服务 - 基于LLM + 规则引擎的海事四维标签分类"""
import json
import re
from typing import Dict, List

import yaml
from openai import OpenAI

from ..core.config import config
from ..models.document import DocumentTags


class TagClassifier:
    """海事文档标签分类器"""

    def __init__(self):
        self.model = config.CHAT_MODEL
        self._client = None

        # 加载标签配置
        with open(config.TAGS_CONFIG_PATH, "r", encoding="utf-8") as f:
            tag_config = yaml.safe_load(f)

        self.dimensions = {}
        for dim in tag_config.get("dimensions", []):
            self.dimensions[dim["name"]] = {
                "display_name": dim["display_name"],
                "values": dim["values"],
            }

        self.prompt_template = tag_config.get("tag_classification_prompt", "")

        # 构建规则引擎关键词映射
        self.keyword_rules = self._build_keyword_rules()

    @property
    def client(self):
        """延迟创建 OpenAI 客户端（避免无 API Key 时导入失败）"""
        if self._client is None:
            self._client = OpenAI(
                api_key=config.DASHSCOPE_API_KEY,
                base_url=config.DASHSCOPE_BASE_URL,
            )
        return self._client

    def _build_keyword_rules(self) -> Dict[str, Dict[str, List[str]]]:
        """构建关键词规则映射

        为每个标签预定义一组关键词，用于规则引擎快速匹配
        """
        rules = {}
        for dim_name, dim_info in self.dimensions.items():
            rules[dim_name] = {}
            for value in dim_info["values"]:
                # 为每个标签生成关键词
                keywords = [value]  # 标签本身
                # 添加常见同义词或简称
                if value == "集装箱运输":
                    keywords.extend(["集装箱", "箱运", "container"])
                elif value == "散货运输":
                    keywords.extend(["散货", "bulk"])
                elif value == "油轮运输":
                    keywords.extend(["油轮", "油船", "原油", "tanker"])
                elif value == "运价波动":
                    keywords.extend(["运价", "运费", "费率", "price"])
                elif value == "港口拥堵":
                    keywords.extend(["拥堵", "堵塞", "congestion"])
                elif value == "碳排放政策":
                    keywords.extend(["碳排放", "碳中和", "绿色航运", "低碳", "碳税"])
                elif value == "船舶碰撞":
                    keywords.extend(["碰撞", "撞船", "collision"])
                elif value == "罢工影响":
                    keywords.extend(["罢工", "停工", "strike"])
                elif value == "法规更新":
                    keywords.extend(["法规", "法律", "新规", "regulation"])
                elif value == "远东":
                    keywords.extend(["中国", "日本", "韩国", "东亚"])
                elif value == "中国沿海":
                    keywords.extend(["上海", "宁波", "深圳", "广州", "天津", "青岛", "大连", "厦门"])
                elif value == "欧洲":
                    keywords.extend(["欧盟", "欧洲", "EU", "Europe"])
                elif value == "北美":
                    keywords.extend(["美国", "加拿大", "北美", "USA"])

                rules[dim_name][value] = keywords

        return rules

    def classify_with_llm(self, content: str) -> DocumentTags:
        """使用LLM进行标签分类

        Args:
            content: 文档内容

        Returns:
            DocumentTags 分类结果
        """
        # 截取前2000字作为分类输入（避免过长）
        truncated = content[:2000]

        # 构建提示词
        prompt = self.prompt_template.format(
            business_type_list="\n".join(f"  - {v}" for v in self.dimensions["business_type"]["values"]),
            geographic_region_list="\n".join(f"  - {v}" for v in self.dimensions["geographic_region"]["values"]),
            topic_category_list="\n".join(f"  - {v}" for v in self.dimensions["topic_category"]["values"]),
            event_nature_list="\n".join(f"  - {v}" for v in self.dimensions["event_nature"]["values"]),
            content=truncated,
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个专业的海事航运领域分类专家。请严格按照JSON格式输出。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,  # 低温度，提高确定性
            max_tokens=500,
        )

        result_text = response.choices[0].message.content

        # 解析JSON
        try:
            # 尝试提取JSON块
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group()

            result = json.loads(result_text)

            return DocumentTags(
                business_type=result.get("business_type", []),
                geographic_region=result.get("geographic_region", []),
                topic_category=result.get("topic_category", []),
                event_nature=result.get("event_nature", []),
                confidence=result.get("confidence", 0.0),
            )
        except (json.JSONDecodeError, Exception) as e:
            # 解析失败，回退到规则引擎
            print(f"LLM解析失败，回退到规则引擎: {e}")
            return self.classify_with_rules(content)

    def classify_with_rules(self, content: str) -> DocumentTags:
        """使用规则引擎进行标签分类（LLM失败时的回退）

        Args:
            content: 文档内容

        Returns:
            DocumentTags 分类结果
        """
        content_lower = content.lower()
        tags = DocumentTags()

        for dim_name, tag_rules in self.keyword_rules.items():
            matched = []
            for tag_value, keywords in tag_rules.items():
                for kw in keywords:
                    if kw.lower() in content_lower:
                        matched.append(tag_value)
                        break

            # 每个维度最多保留3个
            matched = matched[:3]

            if dim_name == "business_type":
                tags.business_type = matched
            elif dim_name == "geographic_region":
                tags.geographic_region = matched
            elif dim_name == "topic_category":
                tags.topic_category = matched
            elif dim_name == "event_nature":
                tags.event_nature = matched

        # 计算置信度：匹配到的标签数 / 总维度数
        total_matched = sum([
            len(tags.business_type),
            len(tags.geographic_region),
            len(tags.topic_category),
            len(tags.event_nature),
        ])
        tags.confidence = min(total_matched / 8, 1.0)  # 归一化

        return tags

    def classify(self, content: str, use_llm: bool = True) -> DocumentTags:
        """分类入口

        优先使用LLM，失败后回退到规则引擎
        """
        if use_llm and config.DASHSCOPE_API_KEY:
            try:
                return self.classify_with_llm(content)
            except Exception as e:
                print(f"LLM分类失败: {e}, 使用规则引擎")
                return self.classify_with_rules(content)
        else:
            return self.classify_with_rules(content)


# 全局实例
tag_classifier = TagClassifier()
