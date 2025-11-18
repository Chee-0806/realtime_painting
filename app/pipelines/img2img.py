"""img2img Pipeline 实现

基于 StreamDiffusion 的图像到图像生成 Pipeline。
支持实时图像转换，适用于摄像头输入等场景。
"""

import logging
from typing import Optional

import torch
from PIL import Image
from pydantic import Field

from app.pipelines.base import BasePipeline
from app.core.engine import StreamDiffusionEngine
from app.config.settings import ModelConfig, PipelineConfig

logger = logging.getLogger(__name__)


class Pipeline(BasePipeline):
    """
    img2img Pipeline 实现
    
    使用 StreamDiffusion 引擎进行图像到图像的实时生成。
    适用于：
    - 摄像头实时风格转换
    - 图像编辑和增强
    - 实时滤镜效果
    """
    
    class InputParams(BasePipeline.InputParams):
        """
        img2img Pipeline 输入参数
        
        扩展基类参数，添加 img2img 特定的参数。
        """
        prompt: str = Field(
            default="",
            title="Prompt",
            description="生成图像的文本提示词"
        )
        negative_prompt: str = Field(
            default="",
            title="Negative Prompt",
            description="负面提示词，描述不想要的内容"
        )
        guidance_scale: float = Field(
            default=1.0,
            title="Guidance Scale",
            description="引导强度，控制生成结果与提示词的相关性",
            ge=0.0,
            le=20.0
        )
        num_inference_steps: int = Field(
            default=4,
            title="Inference Steps",
            description="推理步数，更多步数通常质量更好但速度更慢",
            ge=1,
            le=50
        )
        strength: float = Field(
            default=0.8,
            title="Strength",
            description="转换强度，值越高变化越大",
            ge=0.0,
            le=1.0
        )
    
    def __init__(
        self,
        config: dict,
        device: torch.device,
        dtype: torch.dtype
    ):
        """
        初始化 img2img Pipeline
        
        Args:
            config: 配置字典，包含模型和 Pipeline 配置
            device: PyTorch 设备
            dtype: PyTorch 数据类型
        """
        self.config = config
        self.device = device
        self.dtype = dtype
        
        # 从配置创建 ModelConfig 和 PipelineConfig
        self.model_config = ModelConfig(**config.get("model", {}))
        self.pipeline_config = PipelineConfig(**config.get("pipeline", {}))
        
        # 验证模式
        if self.pipeline_config.mode != "image":
            logger.warning(
                f"img2img Pipeline 应该使用 'image' 模式，"
                f"当前配置为 '{self.pipeline_config.mode}'"
            )
        
        # 初始化 StreamDiffusion 引擎
        logger.info("初始化 img2img Pipeline...")
        self.engine: Optional[StreamDiffusionEngine] = None
        
        try:
            self.engine = StreamDiffusionEngine(
                model_config=self.model_config,
                pipeline_config=self.pipeline_config,
                device=self.device,
                dtype=self.dtype
            )
            logger.info("img2img Pipeline 初始化成功")
        except Exception as e:
            logger.error(f"img2img Pipeline 初始化失败: {e}")
            raise RuntimeError(f"无法初始化 img2img Pipeline: {e}")
    
    def predict(self, params: InputParams, input_image: Image.Image) -> Image.Image:
        """
        执行 img2img 生成
        
        Args:
            params: 输入参数
            input_image: 输入图像
            
        Returns:
            生成的图像
            
        Raises:
            RuntimeError: 如果生成失败
        """
        if self.engine is None:
            raise RuntimeError("StreamDiffusion 引擎未初始化")
        
        if input_image is None:
            raise ValueError("img2img Pipeline 需要输入图像")
        
        try:
            # 调整输入图像尺寸（如果需要）
            target_size = (self.pipeline_config.width, self.pipeline_config.height)
            if input_image.size != target_size:
                input_image = input_image.resize(target_size, Image.Resampling.LANCZOS)
            
            # 确保图像为 RGB 模式
            if input_image.mode != "RGB":
                input_image = input_image.convert("RGB")
            
            # 使用引擎生成图像
            output_image = self.engine.generate_image(
                prompt=params.prompt,
                input_image=input_image,
                negative_prompt=params.negative_prompt,
                num_inference_steps=params.num_inference_steps,
                guidance_scale=params.guidance_scale,
            )
            
            return output_image
            
        except Exception as e:
            logger.error(f"img2img 生成失败: {e}")
            raise RuntimeError(f"img2img 生成失败: {e}")
    
    def prepare(self, prompt: str = "", **kwargs):
        """
        预处理和 warmup
        
        Args:
            prompt: 初始提示词
            **kwargs: 其他参数
        """
        if self.engine is None:
            raise RuntimeError("StreamDiffusion 引擎未初始化")
        
        try:
            logger.info("开始 img2img Pipeline 预处理...")
            
            # 更新初始 prompt
            if prompt:
                self.engine.update_prompt(prompt)
            
            # 执行 warmup
            warmup_steps = self.pipeline_config.warmup
            if warmup_steps > 0:
                self.engine.warmup(steps=warmup_steps)
            
            logger.info("img2img Pipeline 预处理完成")
            
        except Exception as e:
            logger.error(f"img2img Pipeline 预处理失败: {e}")
            raise RuntimeError(f"预处理失败: {e}")
    
    @classmethod
    def get_info(cls) -> BasePipeline.Info:
        """
        获取 Pipeline 元信息
        
        Returns:
            Pipeline 的 Info 对象
        """
        return cls.Info(
            name="img2img",
            input_mode="image",
            page_content="""
            <h1>Image-to-Image Pipeline</h1>
            <p>实时图像到图像生成，基于 StreamDiffusion 优化。</p>
            <h2>特性</h2>
            <ul>
                <li>低延迟实时生成（< 100ms）</li>
                <li>支持摄像头输入</li>
                <li>动态 prompt 更新</li>
                <li>多种加速方式（xformers/TensorRT）</li>
            </ul>
            <h2>使用场景</h2>
            <ul>
                <li>实时风格转换</li>
                <li>视频滤镜效果</li>
                <li>交互式图像编辑</li>
            </ul>
            """
        )
    
    @classmethod
    def get_input_params_schema(cls) -> dict:
        """
        获取输入参数的 JSON Schema
        
        Returns:
            符合 JSON Schema 规范的参数定义字典
        """
        # 使用 Pydantic 的 schema 生成功能
        schema = cls.InputParams.model_json_schema()
        
        # 转换为前端需要的格式
        properties = {}
        for field_name, field_info in schema.get("properties", {}).items():
            properties[field_name] = {
                "default": field_info.get("default", ""),
                "title": field_info.get("title", field_name),
                "id": field_name,
                "type": field_info.get("type", "string"),
                "description": field_info.get("description", ""),
            }
            
            # 添加范围字段（如果有）
            if "minimum" in field_info:
                properties[field_name]["min"] = field_info["minimum"]
            if "maximum" in field_info:
                properties[field_name]["max"] = field_info["maximum"]
            
            # 根据类型设置 field 类型
            if field_info.get("type") == "number":
                properties[field_name]["field"] = "range"
            elif field_info.get("type") == "integer":
                properties[field_name]["field"] = "range"
            elif field_name in ["prompt", "negative_prompt"]:
                properties[field_name]["field"] = "textarea"
            else:
                properties[field_name]["field"] = "input"
        
        return {
            "properties": properties
        }
    
    def update_parameters(self, params: dict):
        """
        更新运行时参数
        
        Args:
            params: 参数字典
        """
        if self.engine is None:
            raise RuntimeError("StreamDiffusion 引擎未初始化")
        
        self.engine.update_parameters(params)
    
    def cleanup(self):
        """清理资源"""
        if self.engine is not None:
            self.engine.cleanup_gpu_memory()
            del self.engine
            self.engine = None
    
    def __del__(self):
        """析构函数"""
        try:
            self.cleanup()
        except Exception:
            pass
