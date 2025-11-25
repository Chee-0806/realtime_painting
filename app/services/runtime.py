"""Runtime wiring for session services."""

from __future__ import annotations

from typing import List, Optional

import logging
import torch

from app.connection_manager import ConnectionManager
from app.config import get_config, Config
from app.pipelines.canvas import Pipeline as CanvasPipeline
from app.pipelines.realtime import Pipeline as RealtimePipeline
from app.pipelines.txt2img import Pipeline as Txt2ImgPipeline
from app.services.session_service import SessionService

logger = logging.getLogger(__name__)

_canvas_service: Optional[SessionService] = None
_realtime_service: Optional[SessionService] = None
_txt2img_service: Optional[SessionService] = None


def setup_session_services(config: Config, device: torch.device, torch_dtype: torch.dtype) -> None:
    global _canvas_service, _realtime_service, _txt2img_service

    def _canvas_manager_factory() -> ConnectionManager:
        return ConnectionManager(drain_strategy="latest", max_queue_depth=1)

    def _realtime_manager_factory() -> ConnectionManager:
        return ConnectionManager(drain_strategy="all", max_queue_depth=1)

    def _txt2img_manager_factory() -> ConnectionManager:
        return ConnectionManager(drain_strategy="latest", max_queue_depth=1)

    if _canvas_service is None:
        _canvas_service = SessionService(
            name="canvas",
            pipeline_cls=CanvasPipeline,
            connection_manager_factory=_canvas_manager_factory,
            config=config.get_canvas_config(),
            device=device,
            torch_dtype=torch_dtype,
        )

    if _realtime_service is None:
        _realtime_service = SessionService(
            name="realtime",
            pipeline_cls=RealtimePipeline,
            connection_manager_factory=_realtime_manager_factory,
            config=config.get_realtime_config(),
            device=device,
            torch_dtype=torch_dtype,
        )

    if _txt2img_service is None:
        _txt2img_service = SessionService(
            name="txt2img",
            pipeline_cls=Txt2ImgPipeline,
            connection_manager_factory=_txt2img_manager_factory,
            config=config.get_txt2img_config(),
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


def get_txt2img_service() -> SessionService:
    if _txt2img_service is None:
        raise RuntimeError("Txt2Img service not configured")
    return _txt2img_service


def list_services() -> List[SessionService]:
    return [svc for svc in (_canvas_service, _realtime_service, _txt2img_service) if svc is not None]
