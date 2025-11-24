from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import logging
import asyncio
import mimetypes
import torch

from app.config.settings import get_settings
from app.api import models
from app.api import realtime
from app.api import canvas
from app.services.runtime import (
    setup_session_services,
    list_services,
)

# fix mime error on windows
mimetypes.add_type("application/javascript", ".js")

# 从配置加载日志级别
settings = get_settings()
log_level = getattr(logging, settings.logging.level.upper(), logging.INFO)
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI()

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch_dtype = torch.float16

setup_session_services(settings, device, torch_dtype)

# 注册路由
app.include_router(models.router)
app.include_router(canvas.router)
app.include_router(realtime.router)


@app.on_event("startup")
async def startup_event():
    """在应用启动时准备服务，但不立即加载模型（懒加载模式）。"""
    logger.info("应用启动完成 - 服务将以懒加载模式初始化模型")
    # 不在启动时加载模型，而是在首次使用时加载


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时断开连接并释放资源。"""
    await asyncio.gather(*(svc.shutdown() for svc in list_services()))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=False,
        log_level="warning",
    )
