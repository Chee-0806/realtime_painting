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
from app.api.session_base import SessionAPI

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/realtime", tags=["realtime"])

# 使用 SessionAPI 以复用 canvas/realtime 共用逻辑
session = SessionAPI()


_realtime_pipeline: RealtimePipeline | None = None
_realtime_config: dict | None = None
_realtime_conn_manager: RealtimeConnectionManager | None = None


def init_realtime_api(pipeline: RealtimePipeline, config: dict):
    """初始化实时生成 API（委托给 SessionAPI）

    Args:
        pipeline: 实时生成 Pipeline 实例
        config: 配置字典
    """
    global _realtime_pipeline, _realtime_config, _realtime_conn_manager, session
    session.init_api(pipeline, config, RealtimeConnectionManager)
    _realtime_pipeline = session._pipeline
    _realtime_config = session._config
    _realtime_conn_manager = session._conn_manager
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
    return await session.create_session()


@router.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: uuid.UUID):
    """获取会话信息 - RESTful: GET /api/realtime/sessions/{session_id}"""
    return await session.get_session(session_id)


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: uuid.UUID):
    """删除会话 - RESTful: DELETE /api/realtime/sessions/{session_id}"""
    return await session.delete_session(session_id)


@router.websocket("/sessions/{session_id}/ws")
async def realtime_websocket(session_id: uuid.UUID, websocket: WebSocket):
    """实时生成 WebSocket 连接 - RESTful: WS /api/realtime/sessions/{session_id}/ws"""
    return await session.websocket_handler(session_id, websocket)


## websocket handling delegated to SessionAPI


@router.get("/sessions/{session_id}/stream")
async def realtime_stream(session_id: uuid.UUID, request: Request):
    """实时生成图像流 - RESTful: GET /api/realtime/sessions/{session_id}/stream"""
    if _realtime_conn_manager is None or _realtime_pipeline is None:
        raise HTTPException(status_code=503, detail="Realtime API not initialized")
    
    return await session.stream_endpoint(session_id, request)


@router.get("/sessions/{session_id}/queue")
async def get_session_queue(session_id: uuid.UUID):
    """获取会话队列状态 - RESTful: GET /api/realtime/sessions/{session_id}/queue"""
    return await session.get_session_queue(session_id)


@router.get("/settings")
async def realtime_settings():
    """获取实时生成设置 - RESTful: GET /api/realtime/settings"""
    return await session.settings()


@router.get("/queue")
async def realtime_queue():
    """获取全局队列状态 - RESTful: GET /api/realtime/queue"""
    return await session.queue()


async def shutdown_realtime_api():
    """Shutdown helper: disconnect all users and cleanup realtime pipeline resources."""
    return await session.shutdown_api()
