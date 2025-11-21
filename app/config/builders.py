"""Configuration builder helpers.

Centralizes how runtime pipeline configs are constructed so we avoid
copy/paste logic scattered across `app/main.py` and the API modules.
"""

from __future__ import annotations

from typing import Any, Dict

from app.config.settings import Settings


def _base_pipeline_config(settings: Settings) -> Dict[str, Any]:
    return {
        "max_queue_size": settings.server.max_queue_size,
        "timeout": settings.server.timeout,
        "use_safety_checker": settings.server.use_safety_checker,
        "use_tiny_vae": settings.pipeline.use_tiny_vae,
        "acceleration": settings.model.acceleration,
        "engine_dir": settings.model.engine_dir,
        "model_id": settings.model.model_id,
    }


def build_canvas_config(settings: Settings) -> Dict[str, Any]:
    """Return canvas-pipeline config derived from current settings."""

    config = _base_pipeline_config(settings)
    perf = settings.performance
    config.update(
        {
            "enable_similar_image_filter": perf.enable_similar_image_filter,
            "similar_image_filter_threshold": perf.similar_image_filter_threshold,
            "similar_image_filter_max_skip_frame": perf.similar_image_filter_max_skip_frame,
            "jpeg_quality": perf.jpeg_quality,
        }
    )
    return config


def build_realtime_config(settings: Settings) -> Dict[str, Any]:
    """Return realtime-pipeline config derived from current settings."""

    config = _base_pipeline_config(settings)

    # Default fallback values if realtime.performance is absent.
    perf_defaults = {
        "enable_similar_image_filter": True,
        "similar_image_filter_threshold": 0.98,
        "similar_image_filter_max_skip_frame": 10,
        "max_fps": 30,
        "jpeg_quality": 85,
    }

    perf_cfg = {}
    if isinstance(settings.realtime, dict):
        perf_cfg = settings.realtime.get("performance", {}) or {}

    config.update({key: perf_cfg.get(key, perf_defaults[key]) for key in perf_defaults})
    return config
