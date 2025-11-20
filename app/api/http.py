"""HTTP API 路由

提供 REST API 端点：
- /api/settings: 获取配置信息
- /api/queue: 获取队列状态
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config.settings import Settings
from app.core.session import SessionManager

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api", tags=["api"])


class SettingsResponse(BaseModel):
    """配置响应模型"""
    input_params: dict
    info: dict
    max_queue_size: int
    page_content: str


class QueueResponse(BaseModel):
    """队列状态响应模型"""
    queue_size: int


# 全局变量（将在应用启动时设置）
_settings: Optional[Settings] = None
_session_manager: Optional[SessionManager] = None


def set_dependencies(settings: Settings, session_manager: SessionManager):
    """
    设置依赖项（在应用启动时调用）
    
    Args:
        settings: 配置对象
        session_manager: 会话管理器
    """
    global _settings, _session_manager
    _settings = settings
    _session_manager = session_manager
    logger.info("HTTP API 依赖项已设置")


@router.get("/settings", response_model=SettingsResponse)
async def get_settings():
    """
    获取后端配置信息
    
    返回包含参数定义、Pipeline 信息等的配置，
    用于前端动态渲染参数控制界面。
    
    Returns:
        配置响应对象
    """
    if _settings is None:
        raise HTTPException(status_code=500, detail="Settings not initialized")
    
    try:
        # 使用 Settings 的方法生成响应
        response = _settings.get_api_settings_response()
        
        logger.debug("返回配置信息")
        return response
    
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get settings: {e}")


@router.get("/queue", response_model=QueueResponse)
async def get_queue_status():
    """
    获取当前队列状态
    
    返回当前活跃会话数量（作为队列大小的代理）。
    
    Returns:
        队列状态响应对象
    """
    if _session_manager is None:
        raise HTTPException(status_code=500, detail="Session manager not initialized")
    
    try:
        # 获取活跃会话数量
        queue_size = await _session_manager.get_active_session_count()
        
        logger.debug(f"队列大小: {queue_size}")
        return {"queue_size": queue_size}
    
    except Exception as e:
        logger.error(f"获取队列状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get queue status: {e}")


@router.get("/sessions")
async def get_sessions():
    """
    获取所有会话信息（调试端点）
    
    Returns:
        会话信息列表
    """
    if _session_manager is None:
        raise HTTPException(status_code=500, detail="Session manager not initialized")
    
    try:
        sessions = await _session_manager.get_all_session_info()
        return {"sessions": sessions, "count": len(sessions)}
    
    except Exception as e:
        logger.error(f"获取会话信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {e}")


@router.get("/sessions/{user_id}")
async def get_session_info(user_id: str):
    """
    获取特定会话信息（调试端点）
    
    Args:
        user_id: 用户 ID
        
    Returns:
        会话信息
    """
    if _session_manager is None:
        raise HTTPException(status_code=500, detail="Session manager not initialized")
    
    try:
        session_info = await _session_manager.get_session_info(user_id)
        
        if session_info is None:
            raise HTTPException(status_code=404, detail=f"Session not found: {user_id}")
        
        return session_info
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session info: {e}")


@router.get("/health")
async def health_check():
    """
    健康检查端点
    
    Returns:
        健康状态
    """
    return {
        "status": "healthy",
        "settings_initialized": _settings is not None,
        "session_manager_initialized": _session_manager is not None
    }


@router.get("/acceleration")
async def get_acceleration_info():
    """
    获取加速方式信息
    
    返回当前使用的加速方式（TensorRT/xformers/none）及其详细信息。
    
    Returns:
        加速方式信息字典，包含：
        - configured: 配置的加速方式
        - actual: 实际使用的加速方式
        - tensorrt_enabled: 是否启用了 TensorRT
        - tensorrt_engines: TensorRT 引擎文件数量
        - unet_type: UNet 模型类型
        - vae_type: VAE 模型类型
    """
    # 从 main.py 导入全局 pipeline
    from app.main import pipeline
    
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        # 获取引擎的加速信息
        if hasattr(pipeline, 'engine'):
            acceleration_info = pipeline.engine.get_acceleration_info()
            return acceleration_info
        else:
            return {
                "status": "unknown",
                "message": "Engine not available"
            }
    
    except Exception as e:
        logger.error(f"获取加速信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get acceleration info: {e}")
