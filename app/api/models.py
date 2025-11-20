"""模型管理 API

提供模型管理相关的 API 端点：
- /api/models: 获取可用模型列表
- /api/models/switch: 切换当前使用的模型
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.config.settings import get_settings, reload_settings
from app.core.engine import StreamDiffusionEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", tags=["models"])


class ModelInfo(BaseModel):
    """模型信息"""
    id: str
    name: str
    description: Optional[str] = None


class SwitchModelRequest(BaseModel):
    """切换模型请求"""
    model_id: str


@router.get("", response_model=List[ModelInfo])
async def list_models():
    """获取可用模型列表"""
    settings = get_settings()
    return settings.model.available_models


@router.post("/switch")
async def switch_model(request: SwitchModelRequest):
    """切换模型
    
    更新配置文件并触发模型重新加载。
    注意：这会暂时中断服务。
    """
    settings = get_settings()
    
    # 验证模型是否存在
    model_exists = False
    for model in settings.model.available_models:
        if model["id"] == request.model_id:
            model_exists = True
            break
    
    if not model_exists:
        raise HTTPException(status_code=404, detail=f"Model not found: {request.model_id}")
    
    try:
        # 更新配置（这里只是更新内存中的配置，实际应用可能需要持久化到文件）
        # 在这个演示中，我们假设配置是临时的，或者由外部工具管理
        # 如果需要持久化，可以写入 config.yaml
        
        # 触发重载
        # 由于 FastAPI 的依赖注入机制，我们需要一种方式通知 main.py 重载 pipeline
        # 这里我们使用一个简单的回调机制或者直接引用 main 中的 reload 函数
        # 为了解耦，我们可以在 main.py 中注册一个回调
        
        from app.main import reload_pipeline
        
        # 异步执行重载，避免阻塞请求
        # 但为了让前端知道何时完成，我们也可以同步执行（如果时间允许）
        # 模型加载可能需要几秒钟，同步执行可能会超时，但对于 WebSocket 连接影响不大
        # 这里选择同步执行以便立即返回结果
        
        await reload_pipeline(request.model_id)
        
        return {"status": "success", "message": f"Switched to model {request.model_id}"}
        
    except Exception as e:
        logger.error(f"Failed to switch model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to switch model: {e}")
