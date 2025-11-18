"""
Pipeline 模块

提供 Pipeline 抽象层和工厂类，支持多种图像生成 Pipeline 的扩展。
"""

from app.pipelines.base import BasePipeline, PipelineFactory

__all__ = ["BasePipeline", "PipelineFactory"]
