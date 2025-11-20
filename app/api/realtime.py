"""实时生成专用 API - RESTful 规范

资源结构：
- /api/realtime/sessions - 会话资源集合
  - POST /api/realtime/sessions - 创建会话
  - GET /api/realtime/sessions/{session_id} - 获取会话信息
  - DELETE /api/realtime/sessions/{session_id} - 删除会话
  - WS /api/realtime/sessions/{session_id}/ws - WebSocket 连接
  - GET /api/realtime/sessions/{session_id}/stream - 图像流
  - GET /api/realtime/sessions/{session_id}/queue - 队列状态
- /api/realtime/settings - 配置资源
- /api/realtime/queue - 全局队列资源
"""

from fastapi import APIRouter, WebSocket, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
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
    
    logger.debug("实时生成 API 已初始化")


class SessionCreateResponse(BaseModel):
    """创建会话响应"""
    session_id: str
    message: str = "Session created"


class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str
    is_connected: bool
    queue_size: int = 0


@router.post("/sessions", response_model=SessionCreateResponse)
async def create_session():
    """创建实时生成会话 - RESTful: POST /api/realtime/sessions"""
    session_id = str(uuid.uuid4())
    return SessionCreateResponse(session_id=session_id)


@router.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: uuid.UUID):
    """获取会话信息 - RESTful: GET /api/realtime/sessions/{session_id}"""
    if _realtime_conn_manager is None:
        raise HTTPException(status_code=503, detail="Realtime API not initialized")
    
    is_connected = _realtime_conn_manager.check_user(session_id)
    queue_size = 0
    if is_connected:
        # 获取队列大小（简化实现）
        queue_size = 1 if is_connected else 0
    
    return SessionInfo(
        session_id=str(session_id),
        is_connected=is_connected,
        queue_size=queue_size
    )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: uuid.UUID):
    """删除会话 - RESTful: DELETE /api/realtime/sessions/{session_id}"""
    if _realtime_conn_manager is None:
        raise HTTPException(status_code=503, detail="Realtime API not initialized")
    
    await _realtime_conn_manager.disconnect(session_id)
    return {"message": "Session deleted", "session_id": str(session_id)}


@router.websocket("/sessions/{session_id}/ws")
async def realtime_websocket(session_id: uuid.UUID, websocket: WebSocket):
    """实时生成 WebSocket 连接 - RESTful: WS /api/realtime/sessions/{session_id}/ws"""
    if _realtime_conn_manager is None:
        await websocket.close(code=503, reason="Realtime API not initialized")
        return
    
    try:
        await _realtime_conn_manager.connect(
            session_id, websocket, _realtime_config.get("max_queue_size", 0) if _realtime_config else 0
        )
        await handle_realtime_websocket_data(session_id)
    except ServerFullException as e:
        logger.error(f"Server Full: {e}")
    finally:
        await _realtime_conn_manager.disconnect(session_id)
        logger.debug(f"实时生成用户断开: {session_id}")


async def handle_realtime_websocket_data(session_id: uuid.UUID):
    """处理实时生成 WebSocket 数据 - 完全照搬 StreamDiffusion 原始实现"""
    if _realtime_conn_manager is None or not _realtime_conn_manager.check_user(session_id):
        return HTTPException(status_code=404, detail="Session not found")
    
    last_time = time.time()
    try:
        while True:
            # 超时检查
            if (
                _realtime_config and _realtime_config.get("timeout", 0) > 0
                and time.time() - last_time > _realtime_config.get("timeout", 0)
            ):
                await _realtime_conn_manager.send_json(
                    session_id,
                    {
                        "status": "timeout",
                        "message": "Your session has ended",
                    },
                )
                await _realtime_conn_manager.disconnect(session_id)
                return
            
            # 完全照搬原始实现：先接收 next_frame 消息
            data = await _realtime_conn_manager.receive_json(session_id)
            if data["status"] == "next_frame":
                if _realtime_pipeline is None:
                    continue
                
                info = _realtime_pipeline.Info()
                # 然后接收 params JSON
                params = await _realtime_conn_manager.receive_json(session_id)
                params = _realtime_pipeline.InputParams(**params)
                params = SimpleNamespace(**params.dict())
                
                if info.input_mode == "image":
                    # 最后接收图像 bytes
                    image_data = await _realtime_conn_manager.receive_bytes(session_id)
                    if len(image_data) == 0:
                        await _realtime_conn_manager.send_json(
                            session_id, {"status": "send_frame"}
                        )
                        continue
                    params.image = bytes_to_pil(image_data)
                
                await _realtime_conn_manager.update_data(session_id, params)

    except Exception as e:
        logger.error(f"Websocket Error: {e}, {session_id}")
        await _realtime_conn_manager.disconnect(session_id)


@router.get("/sessions/{session_id}/stream")
async def realtime_stream(session_id: uuid.UUID, request: Request):
    """实时生成图像流 - RESTful: GET /api/realtime/sessions/{session_id}/stream"""
    if _realtime_conn_manager is None or _realtime_pipeline is None:
        raise HTTPException(status_code=503, detail="Realtime API not initialized")
    
    try:
        async def generate():
            # 完全照搬原始实现，简单直接
            frame_count = 0
            while True:
                await _realtime_conn_manager.send_json(
                    session_id, {"status": "send_frame"}
                )
                params = await _realtime_conn_manager.get_latest_data(session_id)
                if params is None:
                    continue
                image = _realtime_pipeline.predict(params)
                if image is None:
                    continue
                frame = pil_to_frame(image)
                frame_count += 1
                
                # 每100帧输出一次统计（仅在debug模式）
                if frame_count % 100 == 0 and logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"实时生成流处理: {frame_count} 帧")
                
                yield frame

        return StreamingResponse(
            generate(),
            media_type="multipart/x-mixed-replace;boundary=frame",
            headers={"Cache-Control": "no-cache"},
        )
    except Exception as e:
        logger.error(f"Streaming Error: {e}, {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/sessions/{session_id}/queue")
async def get_session_queue(session_id: uuid.UUID):
    """获取会话队列状态 - RESTful: GET /api/realtime/sessions/{session_id}/queue"""
    if _realtime_conn_manager is None:
        return JSONResponse({"queue_size": 0})
    
    # 简化实现：如果会话存在，返回1，否则返回0
    queue_size = 1 if _realtime_conn_manager.check_user(session_id) else 0
    return JSONResponse({"queue_size": queue_size})


@router.get("/settings")
async def realtime_settings():
    """获取实时生成设置 - RESTful: GET /api/realtime/settings"""
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
    """获取全局队列状态 - RESTful: GET /api/realtime/queue"""
    if _realtime_conn_manager is None:
        return JSONResponse({"queue_size": 0})
    
    queue_size = _realtime_conn_manager.get_user_count()
    return JSONResponse({"queue_size": queue_size})
