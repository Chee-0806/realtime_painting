"""
重构后的 txt2img Pipeline

基于 StreamDiffusionBasePipeline，专注于纯文本到图像的生成。
"""

from typing import Any, Dict

from pydantic import BaseModel, Field

from app.pipelines.streamdiffusion_base import StreamDiffusionBasePipeline
from app.config import get_config


class Pipeline(StreamDiffusionBasePipeline):
    """
    txt2img Pipeline - 纯文本模式专用

    适用于：
    - 纯文本生成图像
    - 视频模式（不需要输入图像）
    - 批量生成
    """

    class Info(BaseModel):
        name: str = "StreamDiffusion txt2img (Text-to-Image)"
        input_mode: str = "video"  # txt2img 不需要图像输入
        page_content: str = """
        <h1 class="text-3xl font-bold">Text-to-Image Generation</h1>
        <h3 class="text-xl font-bold">Pure Text-to-Image SD-Turbo</h3>
        <p class="text-sm">
            This demo showcases
            <a
            href="https://github.com/cumulo-autumn/StreamDiffusion"
            target="_blank"
            class="text-blue-500 underline hover:no-underline">StreamDiffusion</a>
            Text-to-Image pipeline using
            <a
            href="https://huggingface.co/stabilityai/sd-turbo"
            target="_blank"
            class="text-blue-500 underline hover:no-underline">SD-Turbo</a>
            optimized for pure text generation.
        </p>
        <h2>Features</h2>
        <ul class="list-disc list-inside text-sm">
            <li>No input image required</li>
            <li>Seed control for reproducible results</li>
            <li>Dynamic prompt updates</li>
            <li>Multiple acceleration methods (xformers/TensorRT)</li>
            <li>High quality text-to-image generation</li>
        </ul>
        <h2>Use Cases</h2>
        <ul class="list-disc list-inside text-sm">
            <li>Creative image generation</li>
            <li>Concept visualization</li>
            <li>Art creation from text</li>
            <li>Batch generation workflows</li>
        </ul>
        """

    class InputParams(StreamDiffusionBasePipeline.InputParams):
        """txt2img 特定的输入参数"""
        # txt2img 特有的参数
        guidance_scale: float = Field(
            7.5,
            title="Guidance Scale",
            description="Guidance strength for text-to-image generation",
            min=0.0,
            max=20.0,
            field="range",
        )

        num_inference_steps: int = Field(
            4,
            title="Inference Steps",
            description="Number of inference steps for generation",
            min=1,
            max=50,
            field="range",
        )

    def _get_initial_params(self) -> "Pipeline.InputParams":
        """获取 txt2img 特定的初始参数"""
        config = get_config()
        txt2img_gen = config.txt2img_generation
        return self.InputParams(
            prompt=txt2img_gen.prompt,
            negative_prompt=txt2img_gen.negative_prompt,
            width=txt2img_gen.width,
            height=txt2img_gen.height,
            steps=txt2img_gen.num_inference_steps,  # txt2img使用专门的推理步数
            cfg_scale=txt2img_gen.guidance_scale,    # txt2img使用专门的引导强度
            denoise=txt2img_gen.denoise,
            seed=txt2img_gen.seed,
            lora_selection="none",
            guidance_scale=txt2img_gen.guidance_scale,
            num_inference_steps=txt2img_gen.num_inference_steps,
        )

    def _get_pipeline_config(self, params: "Pipeline.InputParams") -> Dict[str, Any]:
        """获取 txt2img 管道特定配置"""
        config = get_config()
        txt2img_perf = config.txt2img_performance
        return {
            "mode": "txt2img",
            "enable_similar_image_filter": txt2img_perf.enable_similar_image_filter,
            "similar_image_filter_threshold": txt2img_perf.similar_image_filter_threshold,
            "similar_image_filter_max_skip_frame": txt2img_perf.similar_image_filter_max_skip_frame,
            "frame_buffer_size": txt2img_perf.frame_buffer_size,
            "warmup": txt2img_perf.warmup,
        }

    def _preprocess_input_image(self, params: "Pipeline.InputParams"):
        """
        txt2img 不需要预处理输入图像

        Args:
            params: 输入参数（不包含图像）

        Returns:
            None (txt2img 不需要图像张量）
        """
        # txt2img 模式不需要输入图像
        # 返回 None 或适当的占位符
        return None

    def predict(self, params: "Pipeline.InputParams"):
        """
        执行 txt2img 生成

        Args:
            params: 输入参数（不需要图像）

        Returns:
            生成的图像
        """
        self._ensure_stream(params)
        self._prepare_if_needed(params)

        # 对于 txt2img，直接调用流而不提供图像
        # StreamDiffusionWrapper 应该处理 txt2img 模式
        if hasattr(self.stream, 'txt2img'):
            # 使用专用的 txt2img 方法
            output_image = self.stream.txt2img(
                prompt=params.prompt,
                num_inference_steps=params.num_inference_steps,
                guidance_scale=params.guidance_scale,
                seed=params.seed if params.seed >= 0 else None
            )
        else:
            # 使用通用的 generate 方法
            output_image = self.stream.generate_image(
                prompt=params.prompt,
                input_image=None,  # 明确指定无输入图像
                negative_prompt=params.negative_prompt,
                num_inference_steps=params.num_inference_steps,
                guidance_scale=params.guidance_scale,
                seed=params.seed if params.seed >= 0 else None
            )

        return output_image

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