"""FastAPI主入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import config
from .api.routes import router

app = FastAPI(
    title="小鲸OrcaAI",
    description="AI驱动的一站式海事知识管理工具后端服务",
    version="0.1.0",
)

# CORS配置（允许Chrome Extension访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "小鲸OrcaAI",
        "version": "0.1.0",
        "description": "AI驱动的一站式海事知识管理工具",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=config.APP_HOST,
        port=config.APP_PORT,
        reload=config.APP_DEBUG,
    )
