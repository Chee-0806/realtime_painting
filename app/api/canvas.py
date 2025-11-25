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
from pydantic import BaseModel
import logging
import uuid
from typing import List, Dict, Any, Optional

from app.config import get_config
from app.services.runtime import get_canvas_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/canvas", tags=["canvas"])


class SessionCreateResponse(BaseModel):
    """创建会话响应"""
    session_id: str
    message: str = "Session created"


class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str
    is_connected: bool
    queue_size: int = 0


class ControlNetConfig(BaseModel):
    """ControlNet 配置"""
    type: str
    image: str
    weight: float = 1.0
    guidance_start: float = 0.0
    guidance_end: float = 1.0
    canny_low_threshold: Optional[int] = 50
    canny_high_threshold: Optional[int] = 100


class MultiControlNetRequest(BaseModel):
    """多 ControlNet 生成请求"""
    prompt: str
    negative_prompt: str = ""
    controlnet_configs: List[ControlNetConfig]
    num_inference_steps: int = 20
    guidance_scale: float = 7.5
    width: int = 512
    height: int = 512
    seed: Optional[int] = None


@router.post("/sessions", response_model=SessionCreateResponse)
async def create_session():
    """创建画板会话 - RESTful: POST /api/canvas/sessions"""
    session_api = await _get_session_api()
    return await session_api.create_session()


@router.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: uuid.UUID):
    """获取会话信息 - RESTful: GET /api/canvas/sessions/{session_id}"""
    session_api = await _get_session_api()
    return await session_api.get_session(session_id)


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: uuid.UUID):
    """删除会话 - RESTful: DELETE /api/canvas/sessions/{session_id}"""
    session_api = await _get_session_api()
    return await session_api.delete_session(session_id)


@router.websocket("/sessions/{session_id}/ws")
async def canvas_websocket(session_id: uuid.UUID, websocket: WebSocket):
    """画板 WebSocket 连接 - RESTful: WS /api/canvas/sessions/{session_id}/ws"""
    # delegate to SessionAPI websocket handler
    session_api = await _get_session_api()
    return await session_api.websocket_handler(session_id, websocket)


## websocket handling delegated to SessionAPI


@router.get("/sessions/{session_id}/stream")
async def canvas_stream(session_id: uuid.UUID, request: Request):
    """画板图像流 - RESTful: GET /api/canvas/sessions/{session_id}/stream"""
    session_api = await _get_session_api()
    return await session_api.stream_endpoint(session_id, request)


@router.get("/sessions/{session_id}/queue")
async def get_session_queue(session_id: uuid.UUID):
    """获取会话队列状态 - RESTful: GET /api/canvas/sessions/{session_id}/queue"""
    session_api = await _get_session_api()
    return await session_api.get_session_queue(session_id)


async def shutdown_canvas_api():
    """Shutdown helper: disconnect all users and cleanup pipeline resources."""
    return await get_canvas_service().shutdown()


async def reload_canvas_pipeline(model_id: str, vae_id: str | None = None):
    """重新加载画板 Pipeline（供外部调用，避免循环导入）。

    该函数会先关闭现有 pipeline，然后使用新的配置创建并初始化 pipeline。
    """
    config = get_config()
    config.model.model_id = model_id

    overrides = {"model_id": model_id}
    overrides["vae_id"] = vae_id

    await get_canvas_service().reload(overrides=overrides, persist=True)


@router.get("/settings")
async def canvas_settings():
    """获取画板设置 - RESTful: GET /api/canvas/settings"""
    session_api = await _get_session_api()
    return await session_api.settings()


@router.get("/queue")
async def canvas_queue():
    """获取全局队列状态 - RESTful: GET /api/canvas/queue"""
    session_api = await _get_session_api()
    return await session_api.queue()


@router.post("/controlnet/generate")
async def canvas_controlnet_generate(request: MultiControlNetRequest):
    """
    Canvas ControlNet 生成端点

    支持单个或多个 ControlNet 的图像生成
    """
    try:
        logger.info(f"Canvas ControlNet 生成请求: {len(request.controlnet_configs)} 个 ControlNet")

        # 获取 canvas service
        canvas_service = get_canvas_service()

        # 转换 ControlNet 配置为字典格式
        controlnet_dicts = []
        for cn_config in request.controlnet_configs:
            controlnet_dicts.append({
                "type": cn_config.type,
                "image": cn_config.image,
                "weight": cn_config.weight,
                "guidance_start": cn_config.guidance_start,
                "guidance_end": cn_config.guidance_end,
                "canny_low_threshold": cn_config.canny_low_threshold,
                "canny_high_threshold": cn_config.canny_high_threshold
            })

        # 构建生成参数
        generation_params = {
            "prompt": request.prompt,
            "negative_prompt": request.negative_prompt,
            "controlnet_configs": controlnet_dicts,
            "num_inference_steps": request.num_inference_steps,
            "guidance_scale": request.guidance_scale,
            "width": request.width,
            "height": request.height,
            "seed": request.seed,
        }

        # 这里需要调用 canvas pipeline 的生成方法
        # 具体实现取决于你的 canvas service 架构

        # 暂时返回成功响应（实际实现中需要调用真实的生成逻辑）
        return {
            "success": True,
            "message": f"收到 {len(controlnet_dicts)} 个 ControlNet 生成请求",
            "controlnet_count": len(controlnet_dicts),
            "controlnet_types": [cn["type"] for cn in controlnet_dicts]
        }

    except Exception as e:
        logger.error(f"Canvas ControlNet 生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


async def _get_session_api():
    try:
        return await get_canvas_service().get_api()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Canvas API not initialized") from exc

