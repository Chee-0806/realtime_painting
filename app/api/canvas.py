"""画板专用 API - RESTful 规范

资源结构：
- /api/canvas/sessions - 会话资源集合
  - POST /api/canvas/sessions - 创建会话
  - GET /api/canvas/sessions/{session_id} - 获取会话信息
  - DELETE /api/canvas/sessions/{session_id} - 删除会话
  - WS /api/canvas/sessions/{session_id}/ws - WebSocket 连接
  - GET /api/canvas/sessions/{session_id}/stream - 图像流
  - GET /api/canvas/sessions/{session_id}/queue - 队列状态
- /api/canvas/settings - 配置资源
- /api/canvas/queue - 全局队列资源
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
from app.connection_manager import ConnectionManager, ServerFullException
from app.pipelines.img2img import Pipeline
from app.api.session_base import SessionAPI

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/canvas", tags=["canvas"])

# 使用 SessionAPI 来复用 canvas/realtime 的共用逻辑
session = SessionAPI()


_canvas_pipeline: Pipeline | None = None
_canvas_config: dict | None = None
_canvas_conn_manager: ConnectionManager | None = None


def init_canvas_api(pipeline: Pipeline, config: dict):
    """初始化画板 API（委托给 SessionAPI）"""
    global _canvas_pipeline, _canvas_config, _canvas_conn_manager, session
    session.init_api(pipeline, config, ConnectionManager)
    _canvas_pipeline = session._pipeline
    _canvas_config = session._config
    _canvas_conn_manager = session._conn_manager
    logger.debug("画板 API 已初始化")


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
    """创建画板会话 - RESTful: POST /api/canvas/sessions"""
    return await session.create_session()


@router.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: uuid.UUID):
    """获取会话信息 - RESTful: GET /api/canvas/sessions/{session_id}"""
    return await session.get_session(session_id)


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: uuid.UUID):
    """删除会话 - RESTful: DELETE /api/canvas/sessions/{session_id}"""
    return await session.delete_session(session_id)


@router.websocket("/sessions/{session_id}/ws")
async def canvas_websocket(session_id: uuid.UUID, websocket: WebSocket):
    """画板 WebSocket 连接 - RESTful: WS /api/canvas/sessions/{session_id}/ws"""
    # delegate to SessionAPI websocket handler
    return await session.websocket_handler(session_id, websocket)


## websocket handling delegated to SessionAPI


@router.get("/sessions/{session_id}/stream")
async def canvas_stream(session_id: uuid.UUID, request: Request):
    """画板图像流 - RESTful: GET /api/canvas/sessions/{session_id}/stream"""
    if _canvas_conn_manager is None or _canvas_pipeline is None:
        raise HTTPException(status_code=503, detail="Canvas API not initialized")
    
    return await session.stream_endpoint(session_id, request)


@router.get("/sessions/{session_id}/queue")
async def get_session_queue(session_id: uuid.UUID):
    """获取会话队列状态 - RESTful: GET /api/canvas/sessions/{session_id}/queue"""
    return await session.get_session_queue(session_id)


async def shutdown_canvas_api():
    """Shutdown helper: disconnect all users and cleanup pipeline resources."""
    return await session.shutdown_api()
@router.get("/settings")
async def canvas_settings():
    """获取画板设置 - RESTful: GET /api/canvas/settings"""
    return await session.settings()


@router.get("/queue")
async def canvas_queue():
    """获取全局队列状态 - RESTful: GET /api/canvas/queue"""
    return await session.queue()

