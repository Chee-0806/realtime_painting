"""Session service abstractions used by API routers.

Wraps `SessionAPI` so that routers no longer need to juggle module-level
singletons or instantiate pipelines directly.
"""

from __future__ import annotations

import asyncio
import logging
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
        config = dict(self._config)
        if self._persistent_overrides:
            self._apply_overrides(config, self._persistent_overrides)
        if ephemeral_overrides:
            self._apply_overrides(config, ephemeral_overrides)

        logger.info("Initializing %s pipeline (model=%s)", self._name, config.get("model_id"))

        pipeline = self._pipeline_cls(config, self._device, self._torch_dtype)
        self._session_api.init_api(pipeline, config, self._connection_manager_factory)

        self._state = ServiceState(pipeline=pipeline, config=config, initialized=True)

    @staticmethod
    def _apply_overrides(target: Dict[str, Any], overrides: Dict[str, Any]) -> None:
        for key, value in overrides.items():
            if value is None:
                target.pop(key, None)
            else:
                target[key] = value