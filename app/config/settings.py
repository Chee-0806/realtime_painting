"""配置管理系统

基于 Pydantic Settings 实现配置加载和验证，支持：
- YAML 配置文件
- 环境变量覆盖
- 配置验证
- 类型安全
"""

import os
from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelConfig(BaseModel):
    """模型配置"""
    
    model_id: str = Field(
        default="stabilityai/sd-turbo",
        description="Hugging Face 模型 ID 或本地路径"
    )
    acceleration: Literal["xformers", "tensorrt", "none"] = Field(
        default="xformers",
        description="加速方式：xformers | tensorrt | none"
    )
    engine_dir: str = Field(
        default="engines",
        description="TensorRT 引擎缓存目录"
    )
    use_cuda_graph: bool = Field(
        default=False,
        description="是否启用 CUDA Graph 优化（仅 TensorRT）"
    )
    available_models: list[dict] = Field(
        default_factory=lambda: [
            {"id": "stabilityai/sd-turbo", "name": "SD-Turbo", "description": "Fastest generation, 1 step"},
            {"id": "stabilityai/sdxl-turbo", "name": "SDXL-Turbo", "description": "High quality, 1 step"},
            {"id": "runwayml/stable-diffusion-v1-5", "name": "SD v1.5", "description": "Standard SD v1.5"},
        ],
        description="可用模型列表"
    )
    
    @field_validator("acceleration")
    @classmethod
    def validate_acceleration(cls, v: str) -> str:
        """验证加速方式"""
        valid_methods = ["xformers", "tensorrt", "none"]
        if v not in valid_methods:
            raise ValueError(
                f"无效的加速方式: {v}. 必须是 {', '.join(valid_methods)} 之一"
            )
        return v


class PipelineConfig(BaseModel):
    """Pipeline 配置"""
    
    name: str = Field(
        default="img2img",
        description="Pipeline 类型：img2img | txt2img | controlnet | inpainting"
    )
    mode: Literal["image", "video"] = Field(
        default="image",
        description="输入模式：image (img2img) | video (txt2img)"
    )
    width: int = Field(
        default=512,
        ge=64,
        le=2048,
        description="生成图像宽度"
    )
    height: int = Field(
        default=512,
        ge=64,
        le=2048,
        description="生成图像高度"
    )
    use_tiny_vae: bool = Field(
        default=True,
        description="是否使用 Tiny VAE（更快但质量略低）"
    )
    use_lcm_lora: bool = Field(
        default=True,
        description="是否使用 LCM LoRA"
    )
    warmup: int = Field(
        default=10,
        ge=0,
        le=100,
        description="Warmup 步骤数"
    )
    frame_buffer_size: int = Field(
        default=1,
        ge=1,
        le=10,
        description="帧缓冲区大小"
    )
    use_denoising_batch: bool = Field(
        default=True,
        description="是否使用去噪批处理"
    )
    
    @field_validator("width", "height")
    @classmethod
    def validate_dimensions(cls, v: int) -> int:
        """验证尺寸必须是 8 的倍数（Stable Diffusion 要求）"""
        if v % 8 != 0:
            raise ValueError(f"尺寸必须是 8 的倍数，当前值: {v}")
        return v


class PerformanceConfig(BaseModel):
    """性能配置"""
    
    enable_similar_image_filter: bool = Field(
        default=False,
        description="是否启用相似图像过滤"
    )
    similar_image_filter_threshold: float = Field(
        default=0.98,
        ge=0.0,
        le=1.0,
        description="相似度阈值（0-1）"
    )
    similar_image_filter_max_skip_frame: int = Field(
        default=10,
        ge=0,
        le=100,
        description="最大跳帧数"
    )
    jpeg_quality: int = Field(
        default=85,
        ge=1,
        le=100,
        description="图像流 JPEG 质量（1-100）"
    )


class ServerConfig(BaseModel):
    """服务器配置"""
    
    host: str = Field(
        default="0.0.0.0",
        description="服务器监听地址"
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="服务器端口"
    )
    max_queue_size: int = Field(
        default=0,
        ge=0,
        description="最大队列大小，0 表示无限制"
    )
    timeout: int = Field(
        default=0,
        ge=0,
        description="会话超时（秒），0 表示无限制"
    )
    use_safety_checker: bool = Field(
        default=False,
        description="是否启用 NSFW 内容检测"
    )


class LoggingConfig(BaseModel):
    """日志配置"""
    
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="日志级别"
    )
    format: Literal["json", "text"] = Field(
        default="json",
        description="日志格式"
    )


class CORSConfig(BaseModel):
    """CORS 配置"""
    
    allow_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"],
        description="允许的源"
    )
    allow_credentials: bool = Field(
        default=True,
        description="是否允许凭证"
    )
    allow_methods: list[str] = Field(
        default_factory=lambda: ["*"],
        description="允许的 HTTP 方法"
    )
    allow_headers: list[str] = Field(
        default_factory=lambda: ["*"],
        description="允许的 HTTP 头"
    )


class Settings(BaseSettings):
    """应用配置
    
    支持从以下来源加载配置（优先级从高到低）：
    1. 环境变量（前缀 STREAMDIFFUSION_）
    2. .env 文件
    3. config.yaml 文件
    4. 默认值
    """
    
    model_config = SettingsConfigDict(
        env_prefix="STREAMDIFFUSION_",
        env_nested_delimiter="__",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # 配置文件路径
    config_file: str = Field(
        default="app/config/config.yaml",
        description="YAML 配置文件路径"
    )
    
    # 各模块配置
    model: ModelConfig = Field(default_factory=ModelConfig)
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    cors: CORSConfig = Field(default_factory=CORSConfig)
    
    def __init__(self, **kwargs):
        """初始化配置，首先从 YAML 文件加载"""
        # 如果提供了 config_file 参数，使用它
        config_file = kwargs.get("config_file", "app/config/config.yaml")
        
        # 从 YAML 文件加载配置
        yaml_config = self._load_yaml_config(config_file)
        
        # 合并 YAML 配置和传入的参数（参数优先）
        merged_config = {**yaml_config, **kwargs}
        
        # 调用父类初始化
        super().__init__(**merged_config)
    
    @staticmethod
    def _load_yaml_config(config_file: str) -> dict:
        """从 YAML 文件加载配置
        
        Args:
            config_file: YAML 配置文件路径
            
        Returns:
            配置字典
        """
        config_path = Path(config_file)
        
        if not config_path.exists():
            # 如果配置文件不存在，返回空字典（使用默认值）
            return {}
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)
                return yaml_data or {}
        except yaml.YAMLError as e:
            raise ValueError(f"YAML 配置文件格式错误: {e}")
        except Exception as e:
            raise ValueError(f"无法读取配置文件 {config_file}: {e}")
    
    def validate_config(self) -> list[str]:
        """验证配置的完整性和一致性
        
        Returns:
            警告信息列表（如果有）
        """
        warnings = []
        
        # 验证 TensorRT 相关配置
        if self.model.acceleration == "tensorrt":
            if self.model.use_cuda_graph:
                warnings.append(
                    "CUDA Graph 已启用，这可能会增加首次编译时间但提升运行时性能"
                )
            
            # 检查引擎目录
            engine_dir = Path(self.model.engine_dir)
            if not engine_dir.exists():
                warnings.append(
                    f"TensorRT 引擎目录不存在: {self.model.engine_dir}，将自动创建"
                )
        
        # 验证相似图像过滤配置
        if self.performance.enable_similar_image_filter:
            if self.performance.similar_image_filter_threshold < 0.9:
                warnings.append(
                    f"相似度阈值较低 ({self.performance.similar_image_filter_threshold})，"
                    "可能会过滤掉过多帧"
                )
        
        # 验证 Pipeline 模式和名称的一致性
        if self.pipeline.mode == "image" and self.pipeline.name not in ["img2img", "controlnet", "inpainting"]:
            warnings.append(
                f"Pipeline 模式为 'image' 但名称为 '{self.pipeline.name}'，"
                "可能不兼容"
            )
        elif self.pipeline.mode == "video" and self.pipeline.name != "txt2img":
            warnings.append(
                f"Pipeline 模式为 'video' 但名称为 '{self.pipeline.name}'，"
                "建议使用 'txt2img'"
            )
        
        # 验证队列大小
        if self.server.max_queue_size == 0:
            warnings.append(
                "队列大小设置为无限制，在高负载下可能导致内存问题"
            )
        
        return warnings
    
    def get_api_settings_response(self) -> dict:
        """生成 /api/settings 端点的响应
        
        Returns:
            符合前端要求的配置响应
        """
        return {
            "input_params": {
                "properties": {
                    "prompt": {
                        "default": "",
                        "title": "Prompt",
                        "id": "prompt",
                        "field": "textarea",
                        "type": "string"
                    },
                    "guidance_scale": {
                        "default": 7.5,
                        "title": "Guidance Scale",
                        "id": "guidance_scale",
                        "field": "range",
                        "type": "number",
                        "min": 1.0,
                        "max": 20.0
                    },
                    "num_inference_steps": {
                        "default": 4,
                        "title": "Inference Steps",
                        "id": "num_inference_steps",
                        "field": "range",
                        "type": "integer",
                        "min": 1,
                        "max": 50
                    }
                }
            },
            "info": {
                "properties": {
                    "title": "StreamDiffusion Backend",
                    "input_mode": {
                        "default": self.pipeline.mode
                    }
                }
            },
            "max_queue_size": self.server.max_queue_size,
            "page_content": "<h1>StreamDiffusion Backend</h1><p>实时图像生成服务</p>"
        }
    
    def to_dict(self) -> dict:
        """将配置转换为字典
        
        Returns:
            配置字典
        """
        return {
            "model": self.model.model_dump(),
            "pipeline": self.pipeline.model_dump(),
            "performance": self.performance.model_dump(),
            "server": self.server.model_dump(),
            "logging": self.logging.model_dump(),
            "cors": self.cors.model_dump()
        }


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings(config_file: Optional[str] = None) -> Settings:
    """获取全局配置实例（单例模式）
    
    Args:
        config_file: 可选的配置文件路径
        
    Returns:
        Settings 实例
    """
    global _settings
    
    if _settings is None:
        if config_file:
            _settings = Settings(config_file=config_file)
        else:
            _settings = Settings()
    
    return _settings


def reload_settings(config_file: Optional[str] = None) -> Settings:
    """重新加载配置
    
    Args:
        config_file: 可选的配置文件路径
        
    Returns:
        新的 Settings 实例
    """
    global _settings
    
    if config_file:
        _settings = Settings(config_file=config_file)
    else:
        _settings = Settings()
    
    return _settings
