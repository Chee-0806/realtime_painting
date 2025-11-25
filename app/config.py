"""
简化的配置系统

直接基于实际需求设计，删除不必要的抽象层。
支持环境变量覆盖，优先级：环境变量 > .env > config.yaml > 默认值
"""

import os
from pathlib import Path
from typing import Literal, Optional

try:
    import yaml
except ImportError:
    yaml = None

from pydantic import BaseModel, Field
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    BaseSettings = object
    SettingsConfigDict = dict


class ModelConfig(BaseModel):
    """模型配置"""
    model_id: str = "stabilityai/sd-turbo"
    vae_id: Optional[str] = None
    acceleration: Literal["xformers", "tensorrt", "none"] = "xformers"
    use_tiny_vae: bool = True
    use_lcm_lora: bool = True


class GenerationConfig(BaseModel):
    """生成参数配置"""
    width: int = 512
    height: int = 512
    steps: int = 2
    cfg_scale: float = 2.0
    denoise: float = 0.3
    seed: int = 502923423887318
    prompt: str = ""
    negative_prompt: str = ""


class PerformanceConfig(BaseModel):
    """性能配置"""
    enable_similar_image_filter: bool = False
    similar_image_filter_threshold: float = 0.98
    similar_image_filter_max_skip_frame: int = 10
    jpeg_quality: int = 95
    max_fps: int = 30
    warmup: int = 10
    frame_buffer_size: int = 1


class ServerConfig(BaseModel):
    """服务器配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    max_queue_size: int = 0
    timeout: int = 0
    use_safety_checker: bool = False


class Config(BaseSettings):
    """应用主配置"""
    model_config = SettingsConfigDict(
        env_prefix="STREAMDIFFUSION_",
        env_nested_delimiter="__",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # 配置文件路径
    config_file: str = "app/config/config.yaml"

    # 各模块配置
    model: ModelConfig = Field(default_factory=ModelConfig)

    # Canvas 画板配置
    canvas_generation: GenerationConfig = Field(default_factory=GenerationConfig)
    canvas_performance: PerformanceConfig = Field(default_factory=lambda: PerformanceConfig(
        enable_similar_image_filter=False,
        jpeg_quality=95
    ))

    # Realtime 实时配置
    realtime_generation: GenerationConfig = Field(default_factory=GenerationConfig)
    realtime_performance: PerformanceConfig = Field(default_factory=lambda: PerformanceConfig(
        enable_similar_image_filter=True,
        jpeg_quality=85,
        max_fps=30
    ))

    # Txt2Img 文本生成配置
    txt2img_generation: GenerationConfig = Field(default_factory=lambda: GenerationConfig(
        steps=4,
        cfg_scale=7.5,
        guidance_scale=7.5,
        denoise=0.0,
        seed=-1
    ))
    txt2img_performance: PerformanceConfig = Field(default_factory=lambda: PerformanceConfig(
        enable_similar_image_filter=False,
        jpeg_quality=90
    ))

    # 服务器和日志配置
    server: ServerConfig = Field(default_factory=ServerConfig)
    log_level: str = "INFO"

    def __init__(self, **kwargs):
        """初始化配置，优先从YAML文件加载"""
        config_file = kwargs.get("config_file", "app/config/config.yaml")

        # 从YAML加载配置
        yaml_config = self._load_yaml(config_file)

        # 合并配置（YAML < 环境变量）
        merged_config = {**yaml_config, **kwargs}

        super().__init__(**merged_config)

    @staticmethod
    def _load_yaml(config_file: str) -> dict:
        """从YAML文件加载配置"""
        if yaml is None:
            return {}

        config_path = Path(config_file)

        if not config_path.exists():
            return {}

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def get_canvas_config(self) -> dict:
        """获取canvas模式配置"""
        config = {
            "model_id": self.model.model_id,
            "acceleration": self.model.acceleration,
            "use_tiny_vae": self.model.use_tiny_vae,
            "use_lcm_lora": self.model.use_lcm_lora,
            **self.canvas_generation.model_dump(),
            **self.canvas_performance.model_dump()
        }
        # 添加txt2img专用配置以兼容现有代码
        config.update({
            "guidance_scale": self.canvas_generation.cfg_scale,
            "num_inference_steps": self.canvas_generation.steps,
        })
        return config

    def get_realtime_config(self) -> dict:
        """获取realtime模式配置"""
        config = {
            "model_id": self.model.model_id,
            "acceleration": self.model.acceleration,
            "use_tiny_vae": self.model.use_tiny_vae,
            "use_lcm_lora": self.model.use_lcm_lora,
            **self.realtime_generation.model_dump(),
            **self.realtime_performance.model_dump()
        }
        # 添加兼容配置
        config.update({
            "guidance_scale": self.realtime_generation.cfg_scale,
            "num_inference_steps": self.realtime_generation.steps,
        })
        return config

    def get_txt2img_config(self) -> dict:
        """获取txt2img模式配置"""
        return {
            "model_id": self.model.model_id,
            "acceleration": self.model.acceleration,
            "use_tiny_vae": self.model.use_tiny_vae,
            "use_lcm_lora": self.model.use_lcm_lora,
            **self.txt2img_generation.model_dump(),
            **self.txt2img_performance.model_dump()
        }


# 全局配置实例
_config: Optional[Config] = None


def get_config(config_file: Optional[str] = None) -> Config:
    """获取全局配置（单例模式）"""
    global _config

    if _config is None:
        _config = Config(config_file=config_file) if config_file else Config()

    return _config


def reload_config(config_file: Optional[str] = None) -> Config:
    """重新加载配置"""
    global _config
    _config = Config(config_file=config_file) if config_file else Config()
    return _config