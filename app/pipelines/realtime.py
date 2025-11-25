"""
重构后的 realtime Pipeline

基于 StreamDiffusionBasePipeline，专注于实时摄像头模式的图像生成。
"""

from typing import Any, Dict

from pydantic import BaseModel, Field

from app.pipelines.streamdiffusion_base import StreamDiffusionBasePipeline
from app.config import get_config


class Pipeline(StreamDiffusionBasePipeline):
    """
    Realtime Pipeline - 实时模式专用

    适用于：
    - 实时摄像头图像生成
    - 视频流处理
    - 交互式应用
    """

    class Info(BaseModel):
        name: str = "StreamDiffusion Realtime (Camera Mode)"
        input_mode: str = "image"
        page_content: str = """
        <h1 class="text-3xl font-bold">Realtime Image Generation</h1>
        <h3 class="text-xl font-bold">Real-time Camera-to-Image SD-Turbo</h3>
        <p class="text-sm">
            This demo showcases
            <a
            href="https://github.com/cumulo-autumn/StreamDiffusion"
            target="_blank"
            class="text-blue-500 underline hover:no-underline">StreamDiffusion</a>
            real-time Image to Image pipeline using
            <a
            href="https://huggingface.co/stabilityai/sd-turbo"
            target="_blank"
            class="text-blue-500 underline hover:no-underline">SD-Turbo</a>
            optimized for real-time camera applications.
        </p>
        <h2>Features</h2>
        <ul class="list-disc list-inside text-sm">
            <li>Real-time camera input processing</li>
            <li>Similar image filtering for consistency</li>
            <li>LoRA support for different styles</li>
            <li>Optimized for low latency</li>
        </ul>
        <h2>Use Cases</h2>
        <ul class="list-disc list-inside text-sm">
            <li>Live streaming effects</li>
            <li>Interactive installations</li>
            <li>Real-time style transfer</li>
            <li>Video conferencing backgrounds</li>
        </ul>
        """

    class InputParams(StreamDiffusionBasePipeline.InputParams):
        """realtime 特定的输入参数"""
        # 继承所有基础参数，可以添加 realtime 特定参数
        pass

    def _get_initial_params(self) -> "Pipeline.InputParams":
        """获取 realtime 特定的初始参数"""
        config = get_config()
        realtime_gen = config.realtime_generation
        return self.InputParams(
            prompt=realtime_gen.prompt,
            negative_prompt=realtime_gen.negative_prompt,
            width=realtime_gen.width,
            height=realtime_gen.height,
            steps=realtime_gen.steps,
            cfg_scale=realtime_gen.cfg_scale,
            denoise=realtime_gen.denoise,
            seed=realtime_gen.seed,
            lora_selection="none"
        )

    def _get_pipeline_config(self, params: "Pipeline.InputParams") -> Dict[str, Any]:
        """获取 realtime 管道特定配置"""
        config = get_config()
        realtime_perf = config.realtime_performance
        return {
            "mode": "img2img",
            "enable_similar_image_filter": realtime_perf.enable_similar_image_filter,
            "similar_image_filter_threshold": realtime_perf.similar_image_filter_threshold,
            "similar_image_filter_max_skip_frame": realtime_perf.similar_image_filter_max_skip_frame,
            "frame_buffer_size": realtime_perf.frame_buffer_size,
        }

    def _preprocess_input_image(self, params: "Pipeline.InputParams"):
        """
        预处理摄像头输入图像

        Args:
            params: 包含图像和参数的输入对象

        Returns:
            预处理后的图像张量
        """
        if not hasattr(params, 'image') or params.image is None:
            raise ValueError("realtime pipeline requires an input image")

        # 使用 StreamDiffusionWrapper 的预处理功能
        return self.stream.preprocess_image(params.image)

    def prepare(self, prompt: str = "", **kwargs):
        """
        预处理和 warmup

        Args:
            prompt: 初始提示词
            **kwargs: 其他参数
        """
        # 使用默认参数创建初始准备
        initial_params = self._get_initial_params()
        if prompt:
            initial_params.prompt = prompt

        # 更新其他参数
        for key, value in kwargs.items():
            if hasattr(initial_params, key):
                setattr(initial_params, key, value)

        self._prepare_if_needed(initial_params)

    @classmethod
    def get_info(cls) -> "Pipeline.Info":
        """获取管道元信息"""
        return cls.Info()

    @classmethod
    def get_input_params_schema(cls) -> dict:
        """获取输入参数的 JSON Schema"""
        # 使用 Pydantic 的 schema 生成功能
        schema = cls.InputParams.model_json_schema()

        # 转换为前端需要的格式
        properties = {}
        for field_name, field_info in schema.get("properties", {}).items():
            # 跳过隐藏字段
            if field_info.get("hide", False):
                continue

            properties[field_name] = {
                "default": field_info.get("default", ""),
                "title": field_info.get("title", field_name),
                "id": field_name,
                "type": field_info.get("type", "string"),
                "description": field_info.get("description", ""),
            }

            # 添加范围字段
            if "minimum" in field_info:
                properties[field_name]["min"] = field_info["minimum"]
            if "maximum" in field_info:
                properties[field_name]["max"] = field_info["maximum"]

            # 根据类型设置 field 类型
            if field_info.get("type") == "number":
                properties[field_name]["field"] = "range"
            elif field_info.get("type") == "integer":
                if field_name == "seed":
                    properties[field_name]["field"] = "input"
                else:
                    properties[field_name]["field"] = "range"
            elif field_name in ["prompt", "negative_prompt"]:
                properties[field_name]["field"] = "textarea"
            else:
                properties[field_name]["field"] = "input"

            # 处理选择字段
            if field_name == "lora_selection" and "values" in field_info:
                properties[field_name]["values"] = field_info["values"]

        return {
            "properties": properties
        }