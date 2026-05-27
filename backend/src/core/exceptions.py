"""异常层次结构（参考 OmniBox AppException 模式）"""


class OrcaAIError(Exception):
    """所有异常的基类"""
    def __init__(self, message: str, detail: str = ""):
        self.message = message
        self.detail = detail
        super().__init__(message)


class ConfigError(OrcaAIError):
    """配置错误（缺失 API Key 等）"""
    pass


class APIError(OrcaAIError):
    """外部 API 调用错误（LLM、Embedding 等）"""
    pass


class DocumentError(OrcaAIError):
    """文档处理错误"""
    pass


class SearchError(OrcaAIError):
    """检索错误"""
    pass


class StorageError(OrcaAIError):
    """向量数据库/存储错误"""
    pass
