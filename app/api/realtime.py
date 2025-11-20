"""实时生成专用 API

完全照搬 StreamDiffusion demo/realtime-img2img/main.py 的实现
"""

from fastapi import APIRouter, WebSocket, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
import logging
import uuid
import time
from types import SimpleNamespace
import asyncio
import torch

from app.config.settings import get_settings
from app.util import pil_to_frame, bytes_to_pil
from app.api.realtime_connection_manager import RealtimeConnectionManager, ServerFullException
from app.pipelines.realtime_pipeline import RealtimePipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/realtime", tags=["realtime"])

# 全局变量（在应用启动时初始化）
_realtime_pipeline: RealtimePipeline | None = None
_realtime_config: dict | None = None
_realtime_conn_manager: RealtimeConnectionManager | None = None


def init_realtime_api(pipeline: RealtimePipeline, config: dict):
    """初始化实时生成 API
    
    Args:
        pipeline: 实时生成 Pipeline 实例
        config: 配置字典
    """
    global _realtime_pipeline, _realtime_config, _realtime_conn_manager
    
    _realtime_pipeline = pipeline
    _realtime_config = config
    _realtime_conn_manager = RealtimeConnectionManager()
    
    logger.info("实时生成 API 已初始化（使用 StreamDiffusion 原始实现）")


@router.websocket("/ws/{user_id}")
async def realtime_websocket(user_id: uuid.UUID, websocket: WebSocket):
    """实时生成 WebSocket 连接 - 完全照搬 StreamDiffusion 原始实现"""
    if _realtime_conn_manager is None:
        await websocket.close(code=503, reason="Realtime API not initialized")
        return
    
    try:
        await _realtime_conn_manager.connect(
            user_id, websocket, _realtime_config.get("max_queue_size", 0) if _realtime_config else 0
        )
        await handle_realtime_websocket_data(user_id)
    except ServerFullException as e:
        logger.error(f"Server Full: {e}")
    finally:
        await _realtime_conn_manager.disconnect(user_id)
        logger.info(f"User disconnected: {user_id}")


async def handle_realtime_websocket_data(user_id: uuid.UUID):
    """处理实时生成 WebSocket 数据 - 完全照搬 StreamDiffusion 原始实现"""
    if _realtime_conn_manager is None or not _realtime_conn_manager.check_user(user_id):
        return HTTPException(status_code=404, detail="User not found")
    
    last_time = time.time()
    try:
        while True:
            # 超时检查
            if (
                _realtime_config and _realtime_config.get("timeout", 0) > 0
                and time.time() - last_time > _realtime_config.get("timeout", 0)
            ):
                await _realtime_conn_manager.send_json(
                    user_id,
                    {
                        "status": "timeout",
                        "message": "Your session has ended",
                    },
                )
                await _realtime_conn_manager.disconnect(user_id)
                return
            
            # 完全照搬原始实现：先接收 next_frame 消息
            data = await _realtime_conn_manager.receive_json(user_id)
            if data["status"] == "next_frame":
                if _realtime_pipeline is None:
                    continue
                
                info = _realtime_pipeline.Info()
                # 然后接收 params JSON
                params = await _realtime_conn_manager.receive_json(user_id)
                params = _realtime_pipeline.InputParams(**params)
                params = SimpleNamespace(**params.dict())
                
                if info.input_mode == "image":
                    # 最后接收图像 bytes
                    image_data = await _realtime_conn_manager.receive_bytes(user_id)
                    if len(image_data) == 0:
                        await _realtime_conn_manager.send_json(
                            user_id, {"status": "send_frame"}
                        )
                        continue
                    params.image = bytes_to_pil(image_data)
                
                await _realtime_conn_manager.update_data(user_id, params)

    except Exception as e:
        logger.error(f"Websocket Error: {e}, {user_id}")
        await _realtime_conn_manager.disconnect(user_id)


@router.get("/stream/{user_id}")
async def realtime_stream(user_id: uuid.UUID, request: Request):
    """实时生成图像流 - 完全照搬 StreamDiffusion 原始实现"""
    if _realtime_conn_manager is None or _realtime_pipeline is None:
        raise HTTPException(status_code=503, detail="Realtime API not initialized")
    
    try:
        async def generate():
            # 完全照搬原始实现，简单直接
            while True:
                last_time = time.time()
                await _realtime_conn_manager.send_json(
                    user_id, {"status": "send_frame"}
                )
                params = await _realtime_conn_manager.get_latest_data(user_id)
                if params is None:
                    continue
                image = _realtime_pipeline.predict(params)
                if image is None:
                    continue
                frame = pil_to_frame(image)
                yield frame
                if _realtime_config and _realtime_config.get("debug", False):
                    logger.debug(f"Time taken: {time.time() - last_time}")

        return StreamingResponse(
            generate(),
            media_type="multipart/x-mixed-replace;boundary=frame",
            headers={"Cache-Control": "no-cache"},
        )
    except Exception as e:
        logger.error(f"Streaming Error: {e}, {user_id}")
        raise HTTPException(status_code=404, detail="User not found")


@router.get("/settings")
async def realtime_settings():
    """获取实时生成设置 - 完全照搬 StreamDiffusion 原始实现"""
    if _realtime_pipeline is None:
        raise HTTPException(status_code=503, detail="Realtime pipeline not initialized")
    
    info_schema = _realtime_pipeline.Info.schema()
    info = _realtime_pipeline.Info()
    page_content = info.page_content if info.page_content else ""
    
    input_params = _realtime_pipeline.InputParams.schema()
    
    return JSONResponse(
        {
            "info": info_schema,
            "input_params": input_params,
            "max_queue_size": _realtime_config.get("max_queue_size", 0) if _realtime_config else 0,
            "page_content": page_content,
        }
    )


@router.get("/queue")
async def realtime_queue():
    """获取实时生成队列状态"""
    if _realtime_conn_manager is None:
        return JSONResponse({"queue_size": 0})
    
    queue_size = _realtime_conn_manager.get_user_count()
    return JSONResponse({"queue_size": queue_size})
