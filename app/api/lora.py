"""
LoRA 管理和下载API
提供预制LoRA模型的下载、进度查询和管理功能
"""

import asyncio
import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.pipelines.lora_downloader import get_downloader, LoRAPreset, DownloadTask

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/lora", tags=["lora"])


class LoRAPresetResponse(BaseModel):
    """LoRA预设响应模型"""
    id: str
    name: str
    description: str
    mirrors: List[Dict[str, str]]
    filename: str
    size: str
    model_type: str
    compatible_models: List[str]
    tags: List[str]
    is_downloaded: bool = False
    preview_image: str = ""


class DownloadTaskResponse(BaseModel):
    """下载任务响应模型"""
    preset_id: str
    filename: str
    total_size: int
    downloaded_size: int
    status: str
    progress: float
    speed: float
    error_message: str = ""
    created_at: str
    updated_at: str


class DownloadRequest(BaseModel):
    """下载请求模型"""
    preset_id: str = Field(..., description="预设ID")
    mirror_index: int = Field(0, description="镜像索引，默认使用第一个镜像")


@router.get("/presets", response_model=List[LoRAPresetResponse])
async def get_lora_presets():
    """获取所有可用的LoRA预设"""
    try:
        downloader = get_downloader()
        presets = downloader.get_available_presets()

        response = []
        for preset in presets:
            is_downloaded = downloader.is_preset_downloaded(preset.id)
            preset_response = LoRAPresetResponse(
                **preset.__dict__,
                is_downloaded=is_downloaded
            )
            response.append(preset_response)

        return response

    except Exception as e:
        logger.error(f"获取LoRA预设失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取预设失败: {str(e)}")


@router.get("/presets/{preset_id}", response_model=LoRAPresetResponse)
async def get_lora_preset(preset_id: str):
    """获取特定LoRA预设信息"""
    try:
        downloader = get_downloader()
        preset = downloader.get_preset_by_id(preset_id)

        if not preset:
            raise HTTPException(status_code=404, detail=f"预设 {preset_id} 不存在")

        is_downloaded = downloader.is_preset_downloaded(preset_id)
        return LoRAPresetResponse(
            **preset.__dict__,
            is_downloaded=is_downloaded
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取LoRA预设失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取预设失败: {str(e)}")


@router.post("/download/{preset_id}")
async def start_download(preset_id: str, request: DownloadRequest = None):
    """开始下载LoRA预设"""
    if request is None:
        request = DownloadRequest(preset_id=preset_id)

    try:
        downloader = get_downloader()

        # 检查预设是否存在
        preset = downloader.get_preset_by_id(preset_id)
        if not preset:
            raise HTTPException(status_code=404, detail=f"预设 {preset_id} 不存在")

        # 检查是否已下载
        if downloader.is_preset_downloaded(preset_id):
            return {
                "message": f"预设 {preset.name} 已存在",
                "status": "already_downloaded"
            }

        # 开始下载
        success = await downloader.start_download(preset_id, request.mirror_index)

        if success:
            return {
                "message": f"开始下载 {preset.name}",
                "status": "download_started"
            }
        else:
            # 检查是否正在下载
            task = downloader.get_download_task(preset_id)
            if task and task.status in ["pending", "downloading"]:
                return {
                    "message": f"预设 {preset.name} 正在下载中",
                    "status": "already_downloading"
                }
            else:
                raise HTTPException(status_code=400, detail=f"无法开始下载 {preset_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"开始下载失败: {e}")
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")


@router.post("/download/{preset_id}/cancel")
async def cancel_download(preset_id: str):
    """取消下载LoRA预设"""
    try:
        downloader = get_downloader()

        success = await downloader.cancel_download(preset_id)

        if success:
            return {"message": f"已取消下载 {preset_id}", "status": "cancelled"}
        else:
            raise HTTPException(status_code=404, detail=f"下载任务 {preset_id} 不存在或无法取消")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消下载失败: {e}")
        raise HTTPException(status_code=500, detail=f"取消下载失败: {str(e)}")


@router.get("/download/{preset_id}/status", response_model=DownloadTaskResponse)
async def get_download_status(preset_id: str):
    """获取下载任务状态"""
    try:
        downloader = get_downloader()
        task = downloader.get_download_task(preset_id)

        if not task:
            raise HTTPException(status_code=404, detail=f"下载任务 {preset_id} 不存在")

        return DownloadTaskResponse(
            preset_id=task.preset_id,
            filename=task.filename,
            total_size=task.total_size,
            downloaded_size=task.downloaded_size,
            status=task.status,
            progress=task.progress,
            speed=task.speed,
            error_message=task.error_message,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取下载状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.get("/download/status", response_model=List[DownloadTaskResponse])
async def get_all_download_status():
    """获取所有下载任务状态"""
    try:
        downloader = get_downloader()
        tasks = downloader.get_all_download_tasks()

        response = []
        for task in tasks:
            task_response = DownloadTaskResponse(
                preset_id=task.preset_id,
                filename=task.filename,
                total_size=task.total_size,
                downloaded_size=task.downloaded_size,
                status=task.status,
                progress=task.progress,
                speed=task.speed,
                error_message=task.error_message,
                created_at=task.created_at.isoformat(),
                updated_at=task.updated_at.isoformat()
            )
            response.append(task_response)

        return response

    except Exception as e:
        logger.error(f"获取所有下载状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.delete("/presets/{preset_id}")
async def delete_preset_file(preset_id: str):
    """删除已下载的LoRA预设文件"""
    try:
        downloader = get_downloader()

        # 检查预设是否存在
        preset = downloader.get_preset_by_id(preset_id)
        if not preset:
            raise HTTPException(status_code=404, detail=f"预设 {preset_id} 不存在")

        # 取消正在进行的下载
        await downloader.cancel_download(preset_id)

        # 删除文件
        success = downloader.delete_preset_file(preset_id)

        if success:
            return {"message": f"已删除预设文件 {preset.name}", "status": "deleted"}
        else:
            raise HTTPException(status_code=404, detail=f"预设文件 {preset_id} 不存在或删除失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除预设文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/refresh")
async def refresh_lora_options():
    """刷新LoRA选项（重新扫描本地文件）"""
    try:
        from app.pipelines.lora_utils import get_lora_options_with_presets

        # 清除缓存
        get_lora_options_with_presets.cache_clear()

        # 重新加载预设
        downloader = get_downloader()
        downloader.load_presets()

        return {"message": "LoRA选项已刷新", "status": "refreshed"}

    except Exception as e:
        logger.error(f"刷新LoRA选项失败: {e}")
        raise HTTPException(status_code=500, detail=f"刷新失败: {str(e)}")


@router.get("/stats")
async def get_download_stats():
    """获取下载统计信息"""
    try:
        downloader = get_downloader()
        return {
            "stats": downloader.stats,
            "presets_count": len(downloader.presets),
            "downloaded_count": sum(1 for preset in downloader.presets.values()
                                  if downloader.is_preset_downloaded(preset.id))
        }

    except Exception as e:
        logger.error(f"获取下载统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


# WebSocket端点用于实时下载进度
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    """WebSocket连接管理器"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()


@router.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    """实时下载进度WebSocket"""
    await manager.connect(websocket)
    try:
        downloader = get_downloader()

        while True:
            # 获取当前下载状态
            tasks = downloader.get_all_download_tasks()

            # 只发送有变化的任务状态
            active_tasks = [task for task in tasks if task.status in ["downloading", "completed", "failed"]]

            if active_tasks:
                progress_data = []
                for task in active_tasks:
                    progress_data.append({
                        "preset_id": task.preset_id,
                        "status": task.status,
                        "progress": round(task.progress, 2),
                        "speed": round(task.speed, 2),
                        "downloaded_size": task.downloaded_size,
                        "total_size": task.total_size,
                        "error_message": task.error_message
                    })

                await websocket.send_json({
                    "type": "progress_update",
                    "tasks": progress_data,
                    "timestamp": asyncio.get_event_loop().time()
                })

            await asyncio.sleep(1)  # 每秒更新一次

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket进度推送错误: {e}")
        manager.disconnect(websocket)