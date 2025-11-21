"""模型管理 API

提供模型管理相关的 API 端点：
- /api/models: 获取可用模型列表
- /api/vaes: 获取可用 VAE 列表
- /api/schedulers: 获取可用采样器列表
- /api/models/switch: 切换模型
- /api/vae/switch: 切换 VAE
- /api/scheduler/set: 设置采样器
- /api/health: 健康检查
- /api/acceleration: 获取加速信息
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config.settings import get_settings
from app.api import canvas
from app.services.runtime import get_canvas_service, get_realtime_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["models"])


class ModelInfo(BaseModel):
    """模型信息"""
    id: str
    name: str
    description: Optional[str] = None
    loaded: bool = False


class VaeInfo(BaseModel):
    """VAE 信息"""
    id: str
    name: str
    description: Optional[str] = None
    loaded: bool = False


class SchedulerInfo(BaseModel):
    """采样器信息"""
    id: str
    name: str
    description: Optional[str] = None
    loaded: bool = False


class SwitchModelRequest(BaseModel):
    """切换模型请求"""
    model_id: str
    vae_id: Optional[str] = None
    scheduler_id: Optional[str] = None


class SwitchVaeRequest(BaseModel):
    """切换 VAE 请求"""
    vae_id: str


class SetSchedulerRequest(BaseModel):
    """设置采样器请求"""
    scheduler: str


@router.get("/models")
async def list_models():
    """获取可用模型列表"""
    settings = get_settings()
    current_model_id = settings.model.model_id
    
    models = []
    for m in settings.model.available_models:
        model = m.copy()
        model["loaded"] = (m["id"] == current_model_id)
        models.append(model)
        
    return {"models": models}


@router.get("/vaes")
async def list_vaes():
    """获取可用 VAE 列表"""
    settings = get_settings()
    # 假设当前 VAE ID 存储在某处，这里暂时没有明确的配置项
    # 我们可能需要添加一个配置项，或者从 pipeline 中获取
    # 暂时假设第一个是默认的，或者如果能获取到 pipeline 实例最好
    
    current_vae_id = "madebyollin/taesd" # 默认

    pipe = _get_diffusers_pipe()
    if pipe is not None:
        current_vae_id = getattr(pipe, "vae_id", current_vae_id)
    
    # 如果能获取到 pipeline 信息
    # 注意：StreamDiffusionWrapper 内部可能没有直接暴露 vae_id
    
    vaes = []
    for v in settings.model.available_vaes:
        vae = v.copy()
        # 简单的逻辑：如果 id 匹配则标记为 loaded
        # 这里暂时无法准确获取当前 VAE，除非我们在 settings 中也存储 vae_id
        vae["loaded"] = (v["id"] == current_vae_id)
        vaes.append(vae)
        
    return {"vaes": vaes}


@router.get("/schedulers")
async def list_schedulers():
    """获取可用采样器列表"""
    settings = get_settings()
    
    # 同样，我们需要知道当前的 scheduler
    current_scheduler_id = "euler_a" # 默认
    
    schedulers = []
    for s in settings.model.available_schedulers:
        scheduler = s.copy()
        scheduler["loaded"] = (s["id"] == current_scheduler_id)
        schedulers.append(scheduler)
        
    return {"schedulers": schedulers}


@router.post("/models/switch")
async def switch_model(request: SwitchModelRequest):
    """切换模型"""
    settings = get_settings()
    
    # 验证模型
    if not any(m["id"] == request.model_id for m in settings.model.available_models):
        raise HTTPException(status_code=404, detail=f"Model not found: {request.model_id}")
        
    try:
        from diffusers import (
            EulerAncestralDiscreteScheduler, 
            EulerDiscreteScheduler, 
            DDIMScheduler, 
            LCMScheduler
        )
        
        # 更新配置
        settings.model.model_id = request.model_id
        
        # 触发重载 (传入 VAE ID 如果有)
        await canvas.reload_canvas_pipeline(request.model_id, request.vae_id)
        
        # 如果提供了 scheduler_id，设置 scheduler
        if request.scheduler_id:
            pipe = _get_diffusers_pipe()
            if pipe is None:
                raise HTTPException(status_code=503, detail="Pipeline not initialized")
            scheduler_config = pipe.scheduler.config
            
            if request.scheduler_id == "euler_a":
                pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(scheduler_config)
            elif request.scheduler_id == "euler":
                pipe.scheduler = EulerDiscreteScheduler.from_config(scheduler_config)
            elif request.scheduler_id == "ddim":
                pipe.scheduler = DDIMScheduler.from_config(scheduler_config)
            elif request.scheduler_id == "lcm":
                pipe.scheduler = LCMScheduler.from_config(scheduler_config)
        
        return {"success": True, "message": f"Switched to model {request.model_id}"}
        
    except Exception as e:
        logger.error(f"Failed to switch model: {e}")
        return {"success": False, "message": str(e)}


@router.post("/vae/switch")
async def switch_vae(request: SwitchVaeRequest):
    """切换 VAE"""
    settings = get_settings()
    
    # 验证 VAE
    if not any(v["id"] == request.vae_id for v in settings.model.available_vaes):
        raise HTTPException(status_code=404, detail=f"VAE not found: {request.vae_id}")
        
    try:
        # 获取当前模型 ID
        current_model_id = settings.model.model_id
        
        # 触发重载，传入新的 VAE ID
        await canvas.reload_canvas_pipeline(current_model_id, request.vae_id)
        
        return {"success": True, "message": f"Switched to VAE {request.vae_id}"}
        
    except Exception as e:
        logger.error(f"Failed to switch VAE: {e}")
        return {"success": False, "message": str(e)}


@router.post("/scheduler/set")
async def set_scheduler(request: SetSchedulerRequest):
    """设置采样器"""
    settings = get_settings()
    
    # 验证采样器
    if not any(s["id"] == request.scheduler for s in settings.model.available_schedulers):
        raise HTTPException(status_code=404, detail=f"Scheduler not found: {request.scheduler}")
        
    try:
        from diffusers import (
            EulerAncestralDiscreteScheduler, 
            EulerDiscreteScheduler, 
            DDIMScheduler, 
            LCMScheduler
        )
        
        pipe = _get_diffusers_pipe()
        if pipe is None:
            raise HTTPException(status_code=503, detail="Pipeline not initialized")
        
        scheduler_config = pipe.scheduler.config
        
        if request.scheduler == "euler_a":
            pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(scheduler_config)
        elif request.scheduler == "euler":
            pipe.scheduler = EulerDiscreteScheduler.from_config(scheduler_config)
        elif request.scheduler == "ddim":
            pipe.scheduler = DDIMScheduler.from_config(scheduler_config)
        elif request.scheduler == "lcm":
            pipe.scheduler = LCMScheduler.from_config(scheduler_config)
        else:
            return {"success": False, "message": f"Unsupported scheduler: {request.scheduler}"}
            
        return {"success": True, "message": f"Switched to scheduler {request.scheduler}"}
        
    except Exception as e:
        logger.error(f"Failed to set scheduler: {e}")
        return {"success": False, "message": str(e)}


@router.get("/health")
async def health_check():
    """健康检查端点
    
    Returns:
        健康状态
    """
    canvas_initialized = get_canvas_service().get_pipeline() is not None
    realtime_initialized = get_realtime_state()

    return {
        "status": "healthy",
        "canvas_initialized": canvas_initialized,
        "realtime_initialized": realtime_initialized,
    }


@router.get("/acceleration")
async def get_acceleration_info():
    """获取加速方式信息
    
    返回当前使用的加速方式（TensorRT/xformers/none）及其详细信息。
    
    Returns:
        加速方式信息字典
    """
    pipeline = get_canvas_service().get_pipeline()
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")

    try:
        engine = getattr(pipeline, "engine", None)
        if engine and hasattr(engine, "get_acceleration_info"):
            return engine.get_acceleration_info()
        return {"status": "unknown", "message": "Engine not available"}
    except Exception as e:
        logger.error(f"获取加速信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get acceleration info: {e}")


def _get_diffusers_pipe():
    try:
        pipeline = get_canvas_service().get_pipeline()
    except RuntimeError:
        return None

    if pipeline is None or not hasattr(pipeline, "stream"):
        return None

    try:
        return pipeline.stream.stream.pipe
    except AttributeError:
        return None


def get_realtime_state() -> bool:
    try:
        return get_realtime_service().get_pipeline() is not None
    except RuntimeError:
        return False
