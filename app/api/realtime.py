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
from pydantic import BaseModel
import logging
import uuid

from app.services.runtime import get_realtime_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/realtime", tags=["realtime"])


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
    session_api = await _get_session_api()
    return await session_api.create_session()


@router.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: uuid.UUID):
    """获取会话信息 - RESTful: GET /api/realtime/sessions/{session_id}"""
    session_api = await _get_session_api()
    return await session_api.get_session(session_id)


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: uuid.UUID):
    """删除会话 - RESTful: DELETE /api/realtime/sessions/{session_id}"""
    session_api = await _get_session_api()
    return await session_api.delete_session(session_id)


@router.websocket("/sessions/{session_id}/ws")
async def realtime_websocket(session_id: uuid.UUID, websocket: WebSocket):
    """实时生成 WebSocket 连接 - RESTful: WS /api/realtime/sessions/{session_id}/ws"""
    session_api = await _get_session_api()
    return await session_api.websocket_handler(session_id, websocket)


## websocket handling delegated to SessionAPI


@router.get("/sessions/{session_id}/stream")
async def realtime_stream(session_id: uuid.UUID, request: Request):
    """实时生成图像流 - RESTful: GET /api/realtime/sessions/{session_id}/stream"""
    session_api = await _get_session_api()
    return await session_api.stream_endpoint(session_id, request)


@router.get("/sessions/{session_id}/queue")
async def get_session_queue(session_id: uuid.UUID):
    """获取会话队列状态 - RESTful: GET /api/realtime/sessions/{session_id}/queue"""
    session_api = await _get_session_api()
    return await session_api.get_session_queue(session_id)


@router.get("/settings")
async def realtime_settings():
    """获取实时生成设置 - RESTful: GET /api/realtime/settings"""
    session_api = await _get_session_api()
    return await session_api.settings()


@router.get("/queue")
async def realtime_queue():
    """获取全局队列状态 - RESTful: GET /api/realtime/queue"""
    session_api = await _get_session_api()
    return await session_api.queue()


async def shutdown_realtime_api():
    """Shutdown helper: disconnect all users and cleanup realtime pipeline resources."""
    return await get_realtime_service().shutdown()


async def _get_session_api():
    try:
        return await get_realtime_service().get_api()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Realtime API not initialized") from exc
