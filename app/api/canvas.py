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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/canvas", tags=["canvas"])

# 全局变量（在应用启动时初始化）
_canvas_pipeline: Pipeline | None = None
_canvas_config: dict | None = None
_canvas_conn_manager: ConnectionManager | None = None


def init_canvas_api(pipeline: Pipeline, config: dict):
    """初始化画板 API
    
    Args:
        pipeline: 画板 Pipeline 实例
        config: 配置字典
    """
    global _canvas_pipeline, _canvas_config, _canvas_conn_manager
    
    _canvas_pipeline = pipeline
    _canvas_config = config
    _canvas_conn_manager = ConnectionManager()
    
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
    session_id = str(uuid.uuid4())
    return SessionCreateResponse(session_id=session_id)


@router.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: uuid.UUID):
    """获取会话信息 - RESTful: GET /api/canvas/sessions/{session_id}"""
    if _canvas_conn_manager is None:
        raise HTTPException(status_code=503, detail="Canvas API not initialized")
    
    is_connected = _canvas_conn_manager.check_user(session_id)
    queue_size = 0
    if is_connected:
        queue_size = 1 if is_connected else 0
    
    return SessionInfo(
        session_id=str(session_id),
        is_connected=is_connected,
        queue_size=queue_size
    )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: uuid.UUID):
    """删除会话 - RESTful: DELETE /api/canvas/sessions/{session_id}"""
    if _canvas_conn_manager is None:
        raise HTTPException(status_code=503, detail="Canvas API not initialized")
    
    await _canvas_conn_manager.disconnect(session_id)
    return {"message": "Session deleted", "session_id": str(session_id)}


@router.websocket("/sessions/{session_id}/ws")
async def canvas_websocket(session_id: uuid.UUID, websocket: WebSocket):
    """画板 WebSocket 连接 - RESTful: WS /api/canvas/sessions/{session_id}/ws"""
    if _canvas_conn_manager is None:
        await websocket.close(code=503, reason="Canvas API not initialized")
        return
    
    try:
        await _canvas_conn_manager.connect(
            session_id, websocket, _canvas_config.get("max_queue_size", 0) if _canvas_config else 0
        )
        await handle_canvas_websocket_data(session_id)
    except ServerFullException:
        pass
    finally:
        await _canvas_conn_manager.disconnect(session_id)


async def handle_canvas_websocket_data(session_id: uuid.UUID):
    """处理画板 WebSocket 数据"""
    if _canvas_conn_manager is None or not _canvas_conn_manager.check_user(session_id):
        return HTTPException(status_code=404, detail="Session not found")
    
    last_time = time.time()
    try:
        while True:
            if (
                _canvas_config and _canvas_config.get("timeout", 0) > 0
                and time.time() - last_time > _canvas_config.get("timeout", 0)
            ):
                await _canvas_conn_manager.send_json(
                    session_id,
                    {
                        "status": "timeout",
                        "message": "Your session has ended",
                    },
                )
                await _canvas_conn_manager.disconnect(session_id)
                return
            
            # 接收消息（支持二进制和JSON两种格式）
            data, image_data = await _canvas_conn_manager.receive_message(session_id)
            if not data or not isinstance(data, dict):
                continue
            
            if data.get("status") == "next_frame":
                if _canvas_pipeline is None:
                    await asyncio.sleep(0.1)
                    continue
                
                info = _canvas_pipeline.Info()
                # connection_manager 已经把 params 展开到顶层了
                # 所以直接从 data 中提取参数，排除 status 字段
                params_dict = {k: v for k, v in data.items() if k != "status"}
                
                if not params_dict:
                    logger.warning(f"收到 next_frame 但没有参数: session_id={session_id}")
                    continue
                
                params = _canvas_pipeline.InputParams(**params_dict)
                params = SimpleNamespace(**params.dict())
                if info.input_mode == "image":
                    if len(image_data) == 0:
                        await _canvas_conn_manager.send_json(
                            session_id, {"status": "send_frame"}
                        )
                        continue
                    params.image = bytes_to_pil(image_data)
                
                await _canvas_conn_manager.update_data(session_id, params)

    except Exception as e:
        logger.error(f"Websocket Error: {e}")
        await _canvas_conn_manager.disconnect(session_id)


@router.get("/sessions/{session_id}/stream")
async def canvas_stream(session_id: uuid.UUID, request: Request):
    """画板图像流 - RESTful: GET /api/canvas/sessions/{session_id}/stream"""
    if _canvas_conn_manager is None or _canvas_pipeline is None:
        raise HTTPException(status_code=503, detail="Canvas API not initialized")
    
    try:
        async def generate():
            frame_count = 0
            while True:
                await _canvas_conn_manager.send_json(
                    session_id, {"status": "send_frame"}
                )
                params = await _canvas_conn_manager.get_latest_data(session_id)
                if params is None:
                    continue
                if _canvas_pipeline is None:
                    await asyncio.sleep(0.01)
                    continue
                
                image = _canvas_pipeline.predict(params)
                if image is None:
                    logger.warning(f"图像生成失败: session_id={session_id}")
                    continue
                
                frame = pil_to_frame(image)
                frame_count += 1
                
                # 每100帧输出一次统计（debug级别）
                if frame_count % 100 == 0:
                    logger.debug(f"画板流处理: {frame_count} 帧")
                
                yield frame

        return StreamingResponse(
            generate(),
            media_type="multipart/x-mixed-replace;boundary=frame",
            headers={"Cache-Control": "no-cache"},
        )
    except Exception as e:
        logger.error(f"Streaming Error: {e}")
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/sessions/{session_id}/queue")
async def get_session_queue(session_id: uuid.UUID):
    """获取会话队列状态 - RESTful: GET /api/canvas/sessions/{session_id}/queue"""
    if _canvas_conn_manager is None:
        return JSONResponse({"queue_size": 0})
    
    queue_size = 1 if _canvas_conn_manager.check_user(session_id) else 0
    return JSONResponse({"queue_size": queue_size})


@router.get("/settings")
async def canvas_settings():
    """获取画板设置 - RESTful: GET /api/canvas/settings"""
    if _canvas_pipeline is None:
        raise HTTPException(status_code=503, detail="Canvas pipeline not initialized")
    
    info_schema = _canvas_pipeline.Info.schema()
    info = _canvas_pipeline.Info()
    page_content = info.page_content if info.page_content else ""
    
    input_params = _canvas_pipeline.InputParams.schema()
    
    return JSONResponse(
        {
            "info": info_schema,
            "input_params": input_params,
            "max_queue_size": _canvas_config.get("max_queue_size", 0) if _canvas_config else 0,
            "page_content": page_content,
        }
    )


@router.get("/queue")
async def canvas_queue():
    """获取全局队列状态 - RESTful: GET /api/canvas/queue"""
    if _canvas_conn_manager is None:
        return JSONResponse({"queue_size": 0})
    
    queue_size = _canvas_conn_manager.get_user_count()
    return JSONResponse({"queue_size": queue_size})

