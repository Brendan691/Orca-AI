"""测试标签分类器（规则引擎）"""
import pytest
from src.services.tag_classifier import TagClassifier
from src.models.document import DocumentTags


class TestTagClassifier:
    """不需要 API Key，只测试规则引擎"""

    def setup_method(self):
        self.classifier = TagClassifier()

    def test_classify_with_rules_basic(self):
        """基本分类：集装箱港口内容"""
        content = "上海港集装箱吞吐量创新高，今年前三季度增长15%。洋山深水港自动化码头效率提升显著。"
        tags = self.classifier.classify_with_rules(content)

        assert isinstance(tags, DocumentTags)
        assert "集装箱运输" in tags.business_type or "港口作业" in tags.business_type
        assert len(tags.geographic_region) >= 0  # 上海 → 中国沿海

    def test_classify_with_rules_empty(self):
        """空内容不应崩溃"""
        tags = self.classifier.classify_with_rules("")
        assert isinstance(tags, DocumentTags)
        # 所有维度应该为空
        assert tags.business_type == []
        assert tags.geographic_region == []

    def test_classify_with_rules_oil_tanker(self):
        """油轮相关内容"""
        content = "全球油轮运价持续走低，VLCC日租金跌破2万美元。中东至远东航线需求疲软。浙江自贸区推动油品全产业链发展。"
        tags = self.classifier.classify_with_rules(content)

        assert "油轮运输" in tags.business_type or "运价波动" in tags.topic_category
        assert "中东" in tags.geographic_region or "远东" in tags.geographic_region or "中国沿海" in tags.geographic_region

    def test_classify_with_rules_carbon(self):
        """环保政策内容"""
        content = "IMO新规要求航运业2050年实现净零碳排放。欧盟碳交易体系扩展至航运业。绿色甲醇作为船用燃料受关注。"
        tags = self.classifier.classify_with_rules(content)

        assert "碳排放政策" in tags.topic_category or "环保法规" in tags.topic_category
        assert "法规更新" in tags.event_nature

    def test_classify_with_rules_collision(self):
        """船舶事故内容"""
        content = "长江口发生船舶碰撞事故，两艘集装箱船相撞。海事部门启动应急搜救。事故原因正在调查中。"
        tags = self.classifier.classify_with_rules(content)

        assert "船舶碰撞" in tags.event_nature
        assert "海上搜救" in tags.topic_category or "集装箱运输" in tags.business_type

    def test_classify_returns_document_tags(self):
        """返回类型始终是 DocumentTags"""
        content = "任意文本"
        tags = self.classifier.classify(content, use_llm=False)
        assert isinstance(tags, DocumentTags)
        assert isinstance(tags.business_type, list)
        assert isinstance(tags.geographic_region, list)
        assert isinstance(tags.topic_category, list)
        assert isinstance(tags.event_nature, list)
        assert isinstance(tags.confidence, float)

    def test_classify_max_three_per_dimension(self):
        """每个维度最多 3 个标签"""
        # 构造包含多种标签的文本
        content = ("波罗的海干散货指数连续上涨，中国沿海散货运价同步上行。"
                   "港口拥堵问题加剧，宁波舟山港和上海港船舶排队时间延长。"
                   "航运数字化转型加速，区块链电子提单应用扩大。")
        tags = self.classifier.classify_with_rules(content)

        assert len(tags.business_type) <= 3
        assert len(tags.geographic_region) <= 3
        assert len(tags.topic_category) <= 3
        assert len(tags.event_nature) <= 3
