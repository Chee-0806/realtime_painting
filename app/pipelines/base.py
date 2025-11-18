"""
Pipeline 抽象层

提供 Pipeline 的基类和工厂类，支持多种 Pipeline 实现的扩展。
参考：StreamDiffusion/demo/realtime-img2img/img2img.py
"""

from abc import ABC, abstractmethod
from typing import Literal
from importlib import import_module

import torch
from pydantic import BaseModel, Field
from PIL import Image


class BasePipeline(ABC):
    """
    Pipeline 基类，定义标准接口
    
    所有 Pipeline 实现必须继承此类并实现所有抽象方法。
    支持的 Pipeline 类型：
    - img2img: 图像到图像生成
    - txt2img: 文本到图像生成
    - controlnet: ControlNet 控制生成
    - inpainting: 局部重绘
    - 自定义 Pipeline（通过插件）
    """
    
    class Info(BaseModel):
        """
        Pipeline 元信息
        
        定义 Pipeline 的基本信息，用于前端显示和配置。
        """
        name: str = Field(..., description="Pipeline 名称")
        input_mode: Literal["image", "video"] = Field(
            ..., 
            description="输入模式：image (需要图像输入) 或 video (仅文本输入)"
        )
        page_content: str = Field(
            default="", 
            description="页面内容，用于前端显示的 HTML 或 Markdown"
        )
    
    class InputParams(BaseModel):
        """
        Pipeline 输入参数定义（使用 Pydantic）
        
        定义 Pipeline 接受的参数及其元数据。
        子类可以扩展此模型以添加更多参数。
        """
        prompt: str = Field(
            default="", 
            title="Prompt",
            description="生成图像的文本提示词"
        )
        
        class Config:
            """Pydantic 配置"""
            # 允许子类添加额外字段
            extra = "allow"
    
    @abstractmethod
    def __init__(
        self, 
        config: dict, 
        device: torch.device, 
        dtype: torch.dtype
    ):
        """
        初始化 Pipeline
        
        Args:
            config: 配置字典，包含模型路径、参数等
            device: PyTorch 设备（cuda/cpu）
            dtype: PyTorch 数据类型（float16/float32）
        """
        pass
    
    @abstractmethod
    def predict(self, params: InputParams) -> Image.Image:
        """
        执行生成
        
        Args:
            params: 输入参数，包含 prompt 和其他生成参数
            
        Returns:
            生成的 PIL Image 对象
        """
        pass
    
    @abstractmethod
    def prepare(self, prompt: str, **kwargs):
        """
        预处理和 warmup
        
        在开始生成之前进行必要的准备工作，如：
        - 加载模型
        - 编译 TensorRT 引擎
        - 执行 warmup 步骤
        
        Args:
            prompt: 初始提示词
            **kwargs: 其他准备参数
        """
        pass
    
    @classmethod
    @abstractmethod
    def get_info(cls) -> Info:
        """
        获取 Pipeline 元信息
        
        Returns:
            Pipeline 的 Info 对象
        """
        pass
    
    @classmethod
    @abstractmethod
    def get_input_params_schema(cls) -> dict:
        """
        获取输入参数的 JSON Schema
        
        用于前端动态生成参数控制界面。
        
        Returns:
            符合 JSON Schema 规范的参数定义字典
        """
        pass


class PipelineFactory:
    """
    Pipeline 工厂类，支持动态加载
    
    参考：StreamDiffusion/demo/realtime-img2img/util.py
    
    支持的 Pipeline 类型：
    - img2img: 标准图像到图像
    - txt2img: 文本到图像
    - controlnet: ControlNet 控制
    - inpainting: 局部重绘
    - 自定义 Pipeline（通过插件）
    """
    
    @staticmethod
    def create_pipeline(
        pipeline_name: str,
        config: dict,
        device: torch.device,
        dtype: torch.dtype
    ) -> BasePipeline:
        """
        动态加载并创建 Pipeline 实例
        
        Args:
            pipeline_name: Pipeline 名称（如 "img2img", "txt2img"）
            config: 配置字典
            device: PyTorch 设备
            dtype: PyTorch 数据类型
            
        Returns:
            Pipeline 实例
            
        Raises:
            ImportError: 如果 Pipeline 模块不存在
            AttributeError: 如果 Pipeline 类不存在
            TypeError: 如果 Pipeline 类不是 BasePipeline 的子类
        """
        try:
            # 动态导入 Pipeline 模块
            module = import_module(f"app.pipelines.{pipeline_name}")
            
            # 获取 Pipeline 类（约定类名为 "Pipeline"）
            pipeline_class = getattr(module, "Pipeline")
            
            # 验证是否为 BasePipeline 的子类
            if not issubclass(pipeline_class, BasePipeline):
                raise TypeError(
                    f"Pipeline class in {pipeline_name} must inherit from BasePipeline"
                )
            
            # 创建并返回 Pipeline 实例
            return pipeline_class(config, device, dtype)
            
        except ImportError as e:
            raise ImportError(
                f"Failed to import pipeline '{pipeline_name}'. "
                f"Make sure the module 'app.pipelines.{pipeline_name}' exists. "
                f"Error: {e}"
            )
        except AttributeError as e:
            raise AttributeError(
                f"Pipeline module '{pipeline_name}' does not have a 'Pipeline' class. "
                f"Error: {e}"
            )
    
    @staticmethod
    def list_available_pipelines() -> list[str]:
        """
        列出所有可用的 Pipeline
        
        Returns:
            Pipeline 名称列表
        """
        import os
        import pkgutil
        
        # 获取 pipelines 包的路径
        pipelines_path = os.path.dirname(__file__)
        
        # 查找所有 Python 模块（排除 __init__.py 和 base.py）
        available = []
        for _, name, is_pkg in pkgutil.iter_modules([pipelines_path]):
            if not is_pkg and name not in ["__init__", "base"]:
                available.append(name)
        
        return available
