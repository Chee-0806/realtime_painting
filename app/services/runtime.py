"""Runtime wiring for session services."""

from __future__ import annotations

from typing import List, Optional

import logging
import torch

from app.connection_manager import ConnectionManager
from app.config.builders import build_canvas_config, build_realtime_config
from app.config.settings import Settings
from app.pipelines.img2img import Pipeline
from app.pipelines.realtime_pipeline import RealtimePipeline
from app.services.session_service import SessionService

logger = logging.getLogger(__name__)

_canvas_service: Optional[SessionService] = None
_realtime_service: Optional[SessionService] = None


def setup_session_services(settings: Settings, device: torch.device, torch_dtype: torch.dtype) -> None:
    global _canvas_service, _realtime_service

    def _canvas_manager_factory() -> ConnectionManager:
        return ConnectionManager(drain_strategy="latest", max_queue_depth=1)

    realtime_conf = settings.realtime if isinstance(settings.realtime, dict) else {}
    rt_strategy = realtime_conf.get("queue_strategy") or "all"
    if rt_strategy not in ("latest", "all"):
        logger.warning("Invalid realtime queue_strategy=%s, defaulting to 'all'", rt_strategy)
        rt_strategy = "all"

    rt_queue_depth = realtime_conf.get("queue_max_depth")

    def _realtime_manager_factory() -> ConnectionManager:
        return ConnectionManager(drain_strategy=rt_strategy, max_queue_depth=rt_queue_depth)

    if _canvas_service is None:
        _canvas_service = SessionService(
            name="canvas",
            pipeline_cls=Pipeline,
            connection_manager_factory=_canvas_manager_factory,
            settings=settings,
            config_builder=build_canvas_config,
            device=device,
            torch_dtype=torch_dtype,
        )

    if _realtime_service is None:
        _realtime_service = SessionService(
            name="realtime",
            pipeline_cls=RealtimePipeline,
            connection_manager_factory=_realtime_manager_factory,
            settings=settings,
            config_builder=build_realtime_config,
            device=device,
            torch_dtype=torch_dtype,
        )


def get_canvas_service() -> SessionService:
    if _canvas_service is None:
        raise RuntimeError("Canvas service not configured")
    return _canvas_service


def get_realtime_service() -> SessionService:
    if _realtime_service is None:
        raise RuntimeError("Realtime service not configured")
    return _realtime_service


def list_services() -> List[SessionService]:
    return [svc for svc in (_canvas_service, _realtime_service) if svc is not None]
