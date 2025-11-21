from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request

import logging
import uuid
import time
from types import SimpleNamespace
import asyncio
import os
import mimetypes
import torch

from app.config.settings import get_settings
from app.pipelines.img2img import Pipeline
from app.pipelines.realtime_pipeline import RealtimePipeline
from app.api import models
from app.api import realtime
from app.api import canvas

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

# 从配置文件读取设置
settings = get_settings()

async def reload_canvas_pipeline(model_id: str, vae_id: str = None):
    """重新加载画板 Pipeline"""
    global canvas_config

    logger.info(f"重新加载画板 Pipeline: {model_id}" + (f", VAE: {vae_id}" if vae_id else ""))

    # 1. 先清理现有的 canvas API 资源（如果有）
    try:
        await canvas.shutdown_canvas_api()
    except Exception:
        pass

    # 2. 更新配置
    canvas_config["model_id"] = model_id
    if vae_id is not None:
        canvas_config["vae_id"] = vae_id
    else:
        if "vae_id" in canvas_config:
            del canvas_config["vae_id"]

    # 3. 重新初始化
    try:
        new_pipeline = Pipeline(canvas_config, device, torch_dtype)
        canvas.init_canvas_api(new_pipeline, canvas_config)
        logger.debug("画板 Pipeline 重新加载完成")
    except Exception as e:
        logger.error(f"画板 Pipeline 初始化失败: {e}")
        raise e

# 初始化画板 Pipeline
canvas_config = {
    "max_queue_size": settings.server.max_queue_size,
    "timeout": settings.server.timeout,
    "use_safety_checker": settings.server.use_safety_checker,
    "use_tiny_vae": settings.pipeline.use_tiny_vae,
    "acceleration": settings.model.acceleration,
    "engine_dir": settings.model.engine_dir,
    "model_id": settings.model.model_id,
    # 性能配置
    "enable_similar_image_filter": settings.performance.enable_similar_image_filter,
    "similar_image_filter_threshold": settings.performance.similar_image_filter_threshold,
    "similar_image_filter_max_skip_frame": settings.performance.similar_image_filter_max_skip_frame,
}

# 注册路由
app.include_router(models.router)
app.include_router(canvas.router)
app.include_router(realtime.router)


@app.on_event("startup")
async def startup_event():
    """在应用启动时创建并初始化 pipelines 与 API。"""
    # 初始化画板 pipeline
    try:
        canvas_pipeline = Pipeline(canvas_config, device, torch_dtype)
        canvas.init_canvas_api(canvas_pipeline, canvas_config)
        logger.debug("画板 Pipeline 初始化完成")
    except Exception as e:
        logger.error(f"画板 Pipeline 初始化失败: {e}")

    # 初始化 realtime pipeline
    try:
        realtime_pipeline = RealtimePipeline(realtime_config, device, torch_dtype)
        realtime.init_realtime_api(realtime_pipeline, realtime_config)
        logger.debug("实时 Pipeline 初始化完成")
    except Exception as e:
        logger.error(f"实时 Pipeline 初始化失败: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时断开连接并释放资源。"""
    try:
        await canvas.shutdown_canvas_api()
    except Exception:
        pass
    try:
        await realtime.shutdown_realtime_api()
    except Exception:
        pass

# 初始化实时生成 Pipeline
realtime_config = {
    "max_queue_size": settings.server.max_queue_size,
    "timeout": settings.server.timeout,
    "use_safety_checker": settings.server.use_safety_checker,
    "use_tiny_vae": settings.pipeline.use_tiny_vae,
    "acceleration": settings.model.acceleration,
    "engine_dir": settings.model.engine_dir,
    "model_id": settings.model.model_id,
    # 实时生成专用性能配置
    "enable_similar_image_filter": True,  # 默认启用
    "similar_image_filter_threshold": 0.98,
    "similar_image_filter_max_skip_frame": 10,
    "max_fps": 30,
}

# 如果配置文件中指定了实时生成配置，使用配置文件的值
if settings.realtime and 'performance' in settings.realtime:
    realtime_perf = settings.realtime['performance']
    if realtime_perf:
        realtime_config.update({
            "enable_similar_image_filter": realtime_perf.get("enable_similar_image_filter", True),
            "similar_image_filter_threshold": realtime_perf.get("similar_image_filter_threshold", 0.98),
            "similar_image_filter_max_skip_frame": realtime_perf.get("similar_image_filter_max_skip_frame", 10),
            "max_fps": realtime_perf.get("max_fps", 30),
        })

# realtime pipeline is initialized in startup_event

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=False,
        log_level="warning",
    )
