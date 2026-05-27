"""结构化日志配置（参考 OmniBox JSON 日志模式）"""
import logging
import sys
from datetime import datetime, timezone


def setup_logging(level: str = "INFO", json_format: bool = False) -> None:
    """配置全局日志

    Args:
        level: 日志级别 (DEBUG/INFO/WARNING/ERROR)
        json_format: 是否使用 JSON 格式（生产环境开启）
    """
    if json_format:
        import json

        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                }
                if record.exc_info and record.exc_info[1]:
                    log_entry["exception"] = str(record.exc_info[1])
                return json.dumps(log_entry, ensure_ascii=False)

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        root = logging.getLogger()
        root.handlers = [handler]
    else:
        logging.basicConfig(
            level=getattr(logging, level.upper(), logging.INFO),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            stream=sys.stdout,
        )

    # 抑制第三方库的噪声日志
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logging.getLogger("orcaai").setLevel(getattr(logging, level.upper(), logging.INFO))
