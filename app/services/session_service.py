"""Session service abstractions used by API routers.

Wraps `SessionAPI` so that routers no longer need to juggle module-level
singletons or instantiate pipelines directly.
"""

from __future__ import annotations

import asyncio
import logging
import os
import psutil
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

import torch

from app.api.session_base import SessionAPI

logger = logging.getLogger(__name__)


@dataclass
class ServiceState:
    """Holds runtime objects for a concrete session service."""

    pipeline: Any | None = None
    config: Dict[str, Any] = field(default_factory=dict)
    initialized: bool = False
    child_pids: set[int] = field(default_factory=set)  # 跟踪子进程


class SessionService:
    """Owns a pipeline instance plus its SessionAPI facade."""

    def __init__(
        self,
        name: str,
        pipeline_cls: Type,
        connection_manager_factory: Callable[[], Any],
        config: Dict[str, Any],
        device: torch.device,
        torch_dtype: torch.dtype,
    ) -> None:
        self._name = name
        self._pipeline_cls = pipeline_cls
        self._connection_manager_factory = connection_manager_factory
        self._config = config
        self._device = device
        self._torch_dtype = torch_dtype

        self._session_api = SessionAPI()
        self._state = ServiceState()
        self._persistent_overrides: Dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def startup(self) -> None:
        async with self._lock:
            if self._state.initialized:
                return
            self._initialize_pipeline()

    async def shutdown(self) -> None:
        async with self._lock:
            if not self._state.initialized:
                return
            await self._session_api.shutdown_api()

            # 清理pipeline资源
            if self._state.pipeline is not None:
                self._cleanup_pipeline_resources(self._state.pipeline)

            self._state = ServiceState()

    async def reload(self, overrides: Optional[Dict[str, Any]] = None, persist: bool = False) -> None:
        async with self._lock:
            await self._session_api.shutdown_api()
            if persist and overrides:
                self._apply_overrides(self._persistent_overrides, overrides)
                self._initialize_pipeline()
            else:
                self._initialize_pipeline(ephemeral_overrides=overrides)

    async def get_api(self) -> SessionAPI:
        if not self._state.initialized:
            logger.info(f"懒加载初始化 {self._name} 服务")
            async with self._lock:
                if not self._state.initialized:
                    self._initialize_pipeline()
        return self._session_api

    def get_config(self) -> Dict[str, Any]:
        return dict(self._state.config)

    def get_pipeline(self) -> Any:
        return self._state.pipeline

    def _initialize_pipeline(self, ephemeral_overrides: Optional[Dict[str, Any]] = None) -> None:
        # 先清理旧的pipeline资源
        if self._state.initialized and self._state.pipeline is not None:
            self._cleanup_pipeline_resources(self._state.pipeline)

        config = dict(self._config)
        if self._persistent_overrides:
            self._apply_overrides(config, self._persistent_overrides)
        if ephemeral_overrides:
            self._apply_overrides(config, ephemeral_overrides)

        logger.info("Initializing %s pipeline (model=%s)", self._name, config.get("model_id"))

        # 记录初始化前的子进程
        initial_children = set(psutil.Process().children(recursive=True))

        pipeline = self._pipeline_cls(config, self._device, self._torch_dtype)
        self._session_api.init_api(pipeline, config, self._connection_manager_factory)

        # 记录初始化后新增的子进程（可能是multiprocessing进程）
        final_children = set(psutil.Process().children(recursive=True))
        new_children = final_children - initial_children
        child_pids = {child.pid for child in new_children}

        if child_pids:
            logger.info(f"发现新的子进程: {child_pids}")

        self._state = ServiceState(pipeline=pipeline, config=config, initialized=True, child_pids=child_pids)

    def _cleanup_pipeline_resources(self, pipeline: Any) -> None:
        """清理pipeline的资源，特别是GPU相关组件"""
        try:
            logger.info(f"开始清理 {self._name} pipeline 资源...")

            # 检查是否有StreamDiffusionWrapper类型的pipeline
            if hasattr(pipeline, 'stream'):
                self._cleanup_streamdiffusion_pipeline(pipeline)

            # 检查是否有ControlNet处理器
            if hasattr(pipeline, 'controlnet_processors'):
                self._cleanup_controlnet_processors(pipeline)

            # 强制垃圾回收和GPU缓存清理
            import gc
            import torch

            collected = gc.collect()
            logger.info(f"垃圾回收释放了 {collected} 个对象")

            if torch.cuda.is_available():
                try:
                    # 获取清理前的内存状态
                    before_memory = torch.cuda.memory_allocated()
                    before_reserved = torch.cuda.memory_reserved()

                    # 多次清理
                    for i in range(3):
                        torch.cuda.empty_cache()
                        torch.cuda.synchronize()
                        gc.collect()

                    # 获取清理后的内存状态
                    after_memory = torch.cuda.memory_allocated()
                    after_reserved = torch.cuda.memory_reserved()

                    freed_allocated = (before_memory - after_memory) / 1024**3
                    freed_reserved = (before_reserved - after_reserved) / 1024**3

                    logger.info(f"GPU 内存清理完成: 已分配释放 {freed_allocated:.2f}GB, 已保留释放 {freed_reserved:.2f}GB")
                    logger.info(f"当前 GPU 内存: 已分配 {after_memory / 1024**3:.2f}GB, 已保留 {after_reserved / 1024**3:.2f}GB")

                except Exception as e:
                    logger.error(f"清理 GPU 内存时出错: {e}")

            logger.info(f"{self._name} pipeline 资源清理完成")

            # 清理关联的子进程
            self._cleanup_child_processes()

        except Exception as e:
            logger.error(f"清理 {self._name} pipeline 资源时发生错误: {e}")

    def _cleanup_child_processes(self):
        """清理关联的子进程"""
        if not self._state.child_pids:
            return

        logger.info(f"开始清理 {self._name} 的子进程: {self._state.child_pids}")

        cleaned_count = 0
        for child_pid in list(self._state.child_pids):
            try:
                proc = psutil.Process(child_pid)
                if proc.is_running():
                    logger.info(f"终止子进程: PID {child_pid}")
                    proc.terminate()
                    proc.wait(timeout=3)
                    cleaned_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                try:
                    # 如果优雅终止失败，强制杀死
                    proc = psutil.Process(child_pid)
                    proc.kill()
                    cleaned_count += 1
                    logger.warning(f"强制终止子进程: PID {child_pid}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    logger.debug(f"子进程 {child_pid} 已不存在或无法访问")

        self._state.child_pids.clear()
        logger.info(f"{self._name} 子进程清理完成，共处理 {cleaned_count} 个进程")

    def _cleanup_streamdiffusion_pipeline(self, pipeline: Any) -> None:
        """清理StreamDiffusionWrapper类型的pipeline"""
        try:
            stream = pipeline.stream

            # 清理主要组件
            components_to_cleanup = [
                ('unet', 'UNet'),
                ('vae', 'VAE'),
                ('text_encoder', '文本编码器'),
                ('pipe', '管道')
            ]

            for attr_name, display_name in components_to_cleanup:
                if hasattr(stream, attr_name):
                    try:
                        delattr(stream, attr_name)
                        logger.debug(f"{display_name} 已清理")
                    except Exception as e:
                        logger.warning(f"清理 {display_name} 失败: {e}")

            # 删除stream对象
            delattr(pipeline, 'stream')
            logger.debug("StreamDiffusion 对象已清理")

        except Exception as e:
            logger.error(f"清理 StreamDiffusion pipeline 失败: {e}")

    def _cleanup_controlnet_processors(self, pipeline: Any) -> None:
        """清理ControlNet处理器"""
        try:
            processors = pipeline.controlnet_processors

            for name, processor in processors.items():
                try:
                    # 清理模型的GPU引用
                    if hasattr(processor, 'model'):
                        delattr(processor, 'model')
                    if hasattr(processor, 'device'):
                        delattr(processor, 'device')
                    logger.debug(f"ControlNet 处理器 {name} 已清理")
                except Exception as e:
                    logger.warning(f"清理 ControlNet 处理器 {name} 失败: {e}")

            # 清空处理器字典
            processors.clear()
            if hasattr(pipeline, 'controlnet_processors'):
                delattr(pipeline, 'controlnet_processors')

            logger.info("ControlNet 处理器已清理")

        except Exception as e:
            logger.error(f"清理 ControlNet 处理器时出错: {e}")

    @staticmethod
    def _apply_overrides(target: Dict[str, Any], overrides: Dict[str, Any]) -> None:
        for key, value in overrides.items():
            if value is None:
                target.pop(key, None)
            else:
                target[key] = value