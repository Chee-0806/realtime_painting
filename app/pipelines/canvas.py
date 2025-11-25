"""
重构后的 img2img Pipeline

基于 StreamDiffusionBasePipeline，专注于画布模式的图像生成。
支持 ControlNet 集成。
"""

import logging
import cv2
import numpy as np
import torch
from typing import Any, Dict, List, Optional
from PIL import Image
from pydantic import BaseModel, Field

from app.pipelines.streamdiffusion_base import StreamDiffusionBasePipeline
from app.config import get_config

try:
    from controlnet_aux import (
        CannyDetector,
        OpenposeDetector,
        MidasDetector,
        HEDdetector,
        MLSDdetector,
        LineartDetector,
        NormalBaeDetector,
        PidiNetDetector,  # 修正：不是 ScribbleDetector
        SamDetector,
    )
    CONTROLNET_AUX_AVAILABLE = True
    logging.info("✅ controlnet-aux 导入成功")
except ImportError as e:
    CONTROLNET_AUX_AVAILABLE = False
    logging.warning(f"controlnet-aux import failed: {e}, ControlNet functionality will be limited")


class Pipeline(StreamDiffusionBasePipeline):
    """
    img2img Pipeline - 画布模式专用

    适用于：
    - 画布绘制到图像生成
    - 局部修改和增强
    - 艺术创作辅助
    - ControlNet 精确控制
    """

    class Info(BaseModel):
        name: str = "StreamDiffusion img2img (Canvas Mode with ControlNet)"
        input_mode: str = "image"
        page_content: str = """
        <h1 class="text-3xl font-bold">Canvas Image Generation with ControlNet</h1>
        <h3 class="text-xl font-bold">Image-to-Image SD-Turbo for Canvas Drawing with Precise Control</h3>
        <p class="text-sm">
            This demo showcases
            <a
            href="https://github.com/cumulo-autumn/StreamDiffusion"
            target="_blank"
            class="text-blue-500 underline hover:no-underline">StreamDiffusion</a>
            Image to Image pipeline using
            <a
            href="https://huggingface.co/stabilityai/sd-turbo"
            target="_blank"
            class="text-blue-500 underline hover:no-underline">SD-Turbo</a>
            with ControlNet support for precise artistic control.
        </p>
        <h2>Features</h2>
        <ul class="list-disc list-inside text-sm">
            <li>Canvas-to-image generation</li>
            <li>LoRA support for different styles</li>
            <li>Real-time parameter adjustment</li>
            <li>High quality output for artistic work</li>
            <li><strong>ControlNet integration for precise control</strong></li>
            <li>Multiple ControlNet support</li>
            <li>Edge detection, pose estimation, depth mapping</li>
        </ul>
        <h2>Use Cases</h2>
        <ul class="list-disc list-inside text-sm">
            <li>Digital painting assistance</li>
            <li>Sketch to image conversion</li>
            <li>Art style transfer</li>
            <li>Concept visualization</li>
            <li>Pose-controlled character creation</li>
            <li>Structure-preserving editing</li>
        </ul>
        """

    class InputParams(StreamDiffusionBasePipeline.InputParams):
        """img2img 特定的输入参数（包含 ControlNet 支持）"""
        # ControlNet 基础控制
        controlnet_enabled: bool = Field(
            False,
            title="启用 ControlNet",
            id="controlnet_enabled",
            field="checkbox"
        )

        controlnet_model: str = Field(
            "canny",
            title="ControlNet 类型",
            id="controlnet_model",
            field="select",
            values=["canny", "depth", "pose", "scribble", "lineart", "normal", "semantic", "mlsd", "hed"]
        )

        controlnet_strength: float = Field(
            1.0,
            min=0.0,
            max=2.0,
            step=0.1,
            title="ControlNet 强度",
            id="controlnet_strength",
            field="range"
        )

        # Canny 特定参数
        canny_low_threshold: int = Field(
            50,
            min=0,
            max=255,
            title="Canny 低阈值",
            id="canny_low_threshold",
            hide=True
        )

        canny_high_threshold: int = Field(
            100,
            min=0,
            max=255,
            title="Canny 高阈值",
            id="canny_high_threshold",
            hide=True
        )

        # 多 ControlNet 配置（从 API 传入）
        multi_controlnet_configs: Optional[List[Dict[str, Any]]] = Field(
            None,
            title="多 ControlNet 配置",
            id="multi_controlnet_configs",
            hide=True
        )

    def __init__(self, args: Dict[str, Any], device: torch.device, torch_dtype: torch.dtype):
        super().__init__(args, device, torch_dtype)
        self.controlnet_processors = {}
        self._init_controlnet_processors()

    def _init_controlnet_processors(self):
        """初始化 ControlNet 预处理器"""
        self.logger.info("🔧 开始初始化 ControlNet 预处理器...")

        if not CONTROLNET_AUX_AVAILABLE:
            self.logger.warning("❌ controlnet-aux 未安装，使用基础预处理器")
            return

        try:
            # 初始化所有可用的预处理器
            self.controlnet_processors = {}

            # Canny 边缘检测
            try:
                self.controlnet_processors["canny"] = CannyDetector()
                self.logger.info("✅ Canny 边缘检测预处理器初始化成功")
            except Exception as e:
                self.logger.error(f"❌ Canny 预处理器初始化失败: {e}")

            # Openpose 姿态检测
            try:
                self.controlnet_processors["pose"] = OpenposeDetector()
                self.logger.info("✅ Openpose 姿态检测预处理器初始化成功")
            except Exception as e:
                self.logger.error(f"❌ Openpose 预处理器初始化失败: {e}")

            # Midas 深度检测
            try:
                self.controlnet_processors["depth"] = MidasDetector()
                self.logger.info("✅ Midas 深度检测预处理器初始化成功")
            except Exception as e:
                self.logger.error(f"❌ Midas 预处理器初始化失败: {e}")

            # HED 边缘检测
            try:
                self.controlnet_processors["hed"] = HEDdetector()
                self.logger.info("✅ HED 边缘检测预处理器初始化成功")
            except Exception as e:
                self.logger.error(f"❌ HED 预处理器初始化失败: {e}")

            # MLSD 线条检测
            try:
                self.controlnet_processors["mlsd"] = MLSDdetector()
                self.logger.info("✅ MLSD 线条检测预处理器初始化成功")
            except Exception as e:
                self.logger.error(f"❌ MLSD 预处理器初始化失败: {e}")

            # Lineart 线条艺术
            try:
                self.controlnet_processors["lineart"] = LineartDetector()
                self.logger.info("✅ Lineart 线条艺术预处理器初始化成功")
            except Exception as e:
                self.logger.error(f"❌ Lineart 预处理器初始化失败: {e}")

            # NormalBae 法线图
            try:
                self.controlnet_processors["normal"] = NormalBaeDetector()
                self.logger.info("✅ NormalBae 法线图预处理器初始化成功")
            except Exception as e:
                self.logger.error(f"❌ NormalBae 预处理器初始化失败: {e}")

            # PidiNet 涂鸦检测
            try:
                self.controlnet_processors["scribble"] = PidiNetDetector()
                self.logger.info("✅ PidiNet 涂鸦检测预处理器初始化成功")
            except Exception as e:
                self.logger.error(f"❌ PidiNet 预处理器初始化失败: {e}")

            # SAM 分割
            try:
                self.controlnet_processors["semantic"] = SamDetector()
                self.logger.info("✅ SAM 语义分割预处理器初始化成功")
            except Exception as e:
                self.logger.error(f"❌ SAM 预处理器初始化失败: {e}")

            self.logger.info(f"🎉 ControlNet 预处理器初始化完成！成功初始化 {len(self.controlnet_processors)} 个预处理器")
            self.logger.info(f"📋 可用的 ControlNet 类型: {list(self.controlnet_processors.keys())}")

        except Exception as e:
            self.logger.error(f"💥 初始化 ControlNet 预处理器时发生严重错误: {e}")
            self.controlnet_processors = {}

    def _get_initial_params(self) -> "Pipeline.InputParams":
        """获取 canvas 特定的初始参数"""
        config = get_config()
        canvas_gen = config.canvas_generation
        return self.InputParams(
            prompt=canvas_gen.prompt,
            negative_prompt=canvas_gen.negative_prompt,
            width=canvas_gen.width,
            height=canvas_gen.height,
            steps=canvas_gen.steps,
            cfg_scale=canvas_gen.cfg_scale,
            denoise=canvas_gen.denoise,
            seed=canvas_gen.seed,
            lora_selection="none",
            controlnet_enabled=config.model.controlnet.enabled,
            controlnet_model=config.model.controlnet.preprocessor,
            controlnet_strength=config.model.controlnet.conditioning_scale,
            canny_low_threshold=config.model.controlnet.canny_low_threshold,
            canny_high_threshold=config.model.controlnet.canny_high_threshold
        )

    def _get_pipeline_config(self, params: "Pipeline.InputParams") -> Dict[str, Any]:
        """获取 canvas 管道特定配置"""
        config = get_config()
        canvas_perf = config.canvas_performance
        return {
            "mode": "img2img",
            "enable_similar_image_filter": canvas_perf.enable_similar_image_filter,
            "similar_image_filter_threshold": canvas_perf.similar_image_filter_threshold,
            "similar_image_filter_max_skip_frame": canvas_perf.similar_image_filter_max_skip_frame,
            "frame_buffer_size": canvas_perf.frame_buffer_size,
        }

    def _apply_controlnet_preprocessing(self, image: Image.Image, params: "Pipeline.InputParams") -> Image.Image:
        """应用 ControlNet 预处理"""
        self.logger.info(f"🎛️ ControlNet 预处理开始 - 启用状态: {params.controlnet_enabled}")

        if not params.controlnet_enabled:
            self.logger.info("⏭️ ControlNet 未启用，跳过预处理")
            return image

        processor_type = params.controlnet_model
        self.logger.info(f"🔧 使用的 ControlNet 类型: {processor_type}")
        self.logger.info(f"📏 输入图像尺寸: {image.size}, 模式: {image.mode}")

        if processor_type not in self.controlnet_processors:
            available_types = list(self.controlnet_processors.keys())
            self.logger.error(f"❌ 未知的 ControlNet 模型: {processor_type}")
            self.logger.error(f"❌ 可用的 ControlNet 类型: {available_types}")
            return image

        try:
            processor = self.controlnet_processors[processor_type]
            self.logger.info(f"✅ 成功获取 {processor_type} 处理器")

            # 转换为 RGB 格式
            original_mode = image.mode
            if image.mode != 'RGB':
                image = image.convert('RGB')
                self.logger.info(f"🔄 图像格式转换: {original_mode} -> RGB")

            # 特殊处理 Canny 边缘检测
            if processor_type == "canny":
                self.logger.info(f"⚡ 应用 Canny 边缘检测 - 低阈值: {params.canny_low_threshold}, 高阈值: {params.canny_high_threshold}")
                return self._apply_canny_preprocessing(image, params)
            else:
                self.logger.info(f"🎨 应用 {processor_type} 预处理...")
                # 使用 controlnet-aux 处理器
                processed_image = processor(image)
                self.logger.info(f"✅ {processor_type} 处理完成")

                # 确保输出是 PIL Image
                if isinstance(processed_image, np.ndarray):
                    self.logger.info(f"🔄 转换 numpy array 到 PIL Image")
                    self.logger.info(f"📏 预处理后图像尺寸 (numpy): {processed_image.shape}")
                    processed_image = Image.fromarray(processed_image)
                elif hasattr(processed_image, 'image'):  # 某些处理器返回带有 .image 属性的对象
                    self.logger.info(f"🔄 从对象提取 .image 属性")
                    processed_image = processed_image.image

                # 转换为 RGB
                processed_mode = processed_image.mode
                if processed_image.mode != 'RGB':
                    processed_image = processed_image.convert('RGB')
                    self.logger.info(f"🔄 预处理后图像格式转换: {processed_mode} -> RGB")

                self.logger.info(f"📏 最终输出图像尺寸: {processed_image.size}, 模式: {processed_image.mode}")
                return processed_image

        except Exception as e:
            self.logger.error(f"💥 ControlNet 预处理失败 ({processor_type}): {e}")
            self.logger.error(f"💥 错误详情: {type(e).__name__}: {str(e)}")
            return image

    def _apply_canny_preprocessing(self, image: Image.Image, params: "Pipeline.InputParams") -> Image.Image:
        """应用 Canny 边缘检测预处理"""
        try:
            self.logger.info(f"🔍 开始 Canny 边缘检测预处理")
            self.logger.info(f"📏 原始图像尺寸: {image.size}, 模式: {image.mode}")

            # 转换为 numpy 数组
            img_array = np.array(image)
            self.logger.info(f"🔄 转换为 numpy 数组，形状: {img_array.shape}, 数据类型: {img_array.dtype}")

            # 应用 Canny 边缘检测
            self.logger.info(f"⚡ 执行 Canny 边缘检测 - 低阈值: {params.canny_low_threshold}, 高阈值: {params.canny_high_threshold}")
            edges = cv2.Canny(
                img_array,
                params.canny_low_threshold,
                params.canny_high_threshold
            )
            self.logger.info(f"✅ Canny 检测完成，边缘图像形状: {edges.shape}")

            # 统计边缘像素
            edge_pixels = np.sum(edges > 0)
            total_pixels = edges.size
            edge_ratio = edge_pixels / total_pixels * 100
            self.logger.info(f"📊 边缘统计: {edge_pixels}/{total_pixels} 像素 ({edge_ratio:.2f}%) 是边缘")

            # 转换回 PIL 图像
            self.logger.info(f"🔄 转换边缘检测结果到 PIL 图像")
            control_image = Image.fromarray(edges, mode='L').convert('RGB')
            self.logger.info(f"📏 最终控制图像尺寸: {control_image.size}, 模式: {control_image.mode}")

            return control_image
        except Exception as e:
            self.logger.error(f"💥 Canny 预处理失败: {e}")
            self.logger.error(f"💥 错误详情: {type(e).__name__}: {str(e)}")
            return image

    def _decode_base64_image(self, base64_str: str) -> Optional[Image.Image]:
        """解码 Base64 图像"""
        try:
            import base64
            import io

            # 移除可能的数据URL前缀
            if base64_str.startswith('data:image'):
                base64_str = base64_str.split(',')[1]

            image_data = base64.b64decode(base64_str)
            image = Image.open(io.BytesIO(image_data))

            # 转换为 RGB 格式
            if image.mode != 'RGB':
                image = image.convert('RGB')

            return image
        except Exception as e:
            self.logger.error(f"解码 Base64 图像失败: {e}")
            return None

    def _image_to_tensor(self, image: Image.Image) -> torch.Tensor:
        """将 PIL 图像转换为张量"""
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # 转换为 numpy 数组
        img_array = np.array(image).astype(np.float32) / 255.0

        # 转换维度顺序 (H, W, C) -> (C, H, W)
        img_array = np.transpose(img_array, (2, 0, 1))

        # 转换为 PyTorch 张量并添加 batch 维度
        tensor = torch.from_numpy(img_array).unsqueeze(0)

        return tensor.to(self._device)

    def _preprocess_input_image(self, params: "Pipeline.InputParams"):
        """
        预处理画布输入图像（支持 ControlNet）

        Args:
            params: 包含图像和参数的输入对象

        Returns:
            预处理后的图像张量或包含控制信息的字典
        """
        self.logger.info("📸 开始预处理输入图像...")

        if not hasattr(params, 'image') or params.image is None:
            self.logger.error("❌ img2img pipeline 需要输入图像")
            raise ValueError("img2img pipeline requires an input image")

        canvas_image = params.image
        self.logger.info(f"📊 原始画布图像尺寸: {canvas_image.size}, 模式: {canvas_image.mode}")
        self.logger.info(f"🎯 目标尺寸: {params.width}x{params.height}")

        # 如果启用了多 ControlNet
        if params.multi_controlnet_configs and len(params.multi_controlnet_configs) > 0:
            self.logger.info(f"🎛️ 处理多 ControlNet 配置 - 数量: {len(params.multi_controlnet_configs)}")

            control_images = []
            controlnet_scales = []

            for i, config in enumerate(params.multi_controlnet_configs):
                self.logger.info(f"🎛️ 处理 ControlNet {i+1}/{len(params.multi_controlnet_configs)}")
                self.logger.info(f"   类型: {config.get('type', 'unknown')}")
                self.logger.info(f"   权重: {config.get('weight', 1.0)}")

                # 解码控制图像
                base64_image = config.get("image", "")
                if base64_image:
                    self.logger.info(f"   📦 解码 Base64 控制图像 (长度: {len(base64_image)})")
                    control_image = self._decode_base64_image(base64_image)
                    if control_image:
                        self.logger.info(f"   📏 控制图像原始尺寸: {control_image.size}")

                        # 调整大小匹配画布
                        control_image = control_image.resize(
                            (params.width, params.height),
                            Image.Resampling.LANCZOS
                        )
                        self.logger.info(f"   📏 控制图像调整后尺寸: {control_image.size}")

                        # 应用对应的预处理器
                        cn_type = config.get("type", "canny")
                        temp_params = self.InputParams(
                            controlnet_enabled=True,
                            controlnet_model=cn_type,
                            canny_low_threshold=config.get("canny_low_threshold", 50),
                            canny_high_threshold=config.get("canny_high_threshold", 100)
                        )

                        self.logger.info(f"   🎨 应用 {cn_type} 预处理器...")
                        processed_image = self._apply_controlnet_preprocessing(control_image, temp_params)
                        self.logger.info(f"   📏 预处理后控制图像尺寸: {processed_image.size}")
                        control_images.append(processed_image)
                        controlnet_scales.append(config.get("weight", 1.0))
                    else:
                        self.logger.error(f"   ❌ ControlNet {i+1} 图像解码失败")
                else:
                    self.logger.warning(f"   ⚠️ ControlNet {i+1} 没有图像数据")

            if control_images:
                self.logger.info(f"✅ 成功处理 {len(control_images)} 个 ControlNet")
                canvas_tensor = self._image_to_tensor(canvas_image)
                self.logger.info(f"📊 画布张量形状: {canvas_tensor.shape}")

                control_tensors = []
                for i, img in enumerate(control_images):
                    ctrl_tensor = self._image_to_tensor(img)
                    control_tensors.append(ctrl_tensor)
                    self.logger.info(f"📊 控制张量 {i+1} 形状: {ctrl_tensor.shape}")

                return {
                    "image": canvas_tensor,
                    "control_images": control_tensors,
                    "controlnet_conditioning_scales": controlnet_scales
                }
            else:
                self.logger.warning("⚠️ 没有有效的 ControlNet 图像，回退到单个 ControlNet 或标准模式")

        # 如果启用单个 ControlNet
        if params.controlnet_enabled:
            self.logger.info(f"🎛️ 处理单个 ControlNet - 类型: {params.controlnet_model}, 强度: {params.controlnet_strength}")
            self.logger.info(f"🎨 应用 {params.controlnet_model} 预处理器到画布图像...")
            control_image = self._apply_controlnet_preprocessing(canvas_image, params)

            canvas_tensor = self._image_to_tensor(canvas_image)
            control_tensor = self._image_to_tensor(control_image)

            self.logger.info(f"📊 画布张量形状: {canvas_tensor.shape}")
            self.logger.info(f"📊 控制张量形状: {control_tensor.shape}")
            self.logger.info(f"⚖️ ControlNet 条件缩放: {params.controlnet_strength}")

            return {
                "image": canvas_tensor,
                "control_image": control_tensor,
                "controlnet_conditioning_scale": params.controlnet_strength
            }

        # 标准 img2img 处理
        self.logger.info("🖼️ 使用标准 img2img 处理（无 ControlNet）")
        preprocessed = self.stream.preprocess_image(canvas_image)
        if hasattr(preprocessed, 'shape'):
            self.logger.info(f"📊 标准预处理张量形状: {preprocessed.shape}")
        return preprocessed

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

    # 重写 predict 方法以支持 ControlNet
    def predict(self, params: "Pipeline.InputParams") -> Image.Image:
        """
        执行预测（支持 ControlNet）

        Args:
            params: 输入参数

        Returns:
            生成的图像
        """
        self.logger.info("🚀 开始图像生成预测...")
        self.logger.info(f"⚙️ 参数设置 - ControlNet启用: {params.controlnet_enabled}, 类型: {params.controlnet_model}, 强度: {params.controlnet_strength}")

        self._ensure_stream(params)
        self._prepare_if_needed(params)

        # 预处理输入图像
        self.logger.info("📸 开始预处理输入图像...")
        image_input = self._preprocess_input_image(params)

        try:
            if isinstance(image_input, dict):
                # ControlNet 生成
                if "control_images" in image_input:
                    # 多 ControlNet
                    num_controls = len(image_input['control_images'])
                    control_types = params.multi_controlnet_configs[i].get("type", "unknown") if params.multi_controlnet_configs else "unknown"
                    self.logger.info(f"🎛️ 使用多 ControlNet 生成 - 数量: {num_controls}")
                    self.logger.info(f"🎛️ ControlNet 权重: {image_input['controlnet_conditioning_scales']}")

                    for i, scale in enumerate(image_input['controlnet_conditioning_scales']):
                        cn_type = params.multi_controlnet_configs[i].get("type", "unknown") if params.multi_controlnet_configs and i < len(params.multi_controlnet_configs) else "unknown"
                        self.logger.info(f"   🎛️ ControlNet {i+1}: {cn_type}, 权重: {scale}")

                    self.logger.info(f"📊 主图像张量形状: {image_input['image'].shape}")
                    for i, ctrl_img in enumerate(image_input['control_images']):
                        self.logger.info(f"📊 控制图像 {i+1} 张量形状: {ctrl_img.shape}")

                    self.logger.info("🎨 执行多 ControlNet 图像生成...")
                    output_image = self.stream(
                        image=image_input["image"],
                        control_images=image_input["control_images"],
                        controlnet_conditioning_scales=image_input["controlnet_conditioning_scales"],
                        prompt=params.prompt
                    )
                else:
                    # 单个 ControlNet
                    self.logger.info(f"🎛️ 使用单个 ControlNet 生成 - 类型: {params.controlnet_model}, 权重: {image_input['controlnet_conditioning_scale']}")
                    self.logger.info(f"📊 主图像张量形状: {image_input['image'].shape}")
                    self.logger.info(f"📊 控制图像张量形状: {image_input['control_image'].shape}")

                    self.logger.info("🎨 执行 ControlNet 图像生成...")
                    output_image = self.stream(
                        image=image_input["image"],
                        control_image=image_input["control_image"],
                        controlnet_conditioning_scale=image_input["controlnet_conditioning_scale"],
                        prompt=params.prompt
                    )
            else:
                # 标准 img2img 生成
                self.logger.info("🖼️ 使用标准 img2img 生成（无 ControlNet）")
                if hasattr(image_input, 'shape'):
                    self.logger.info(f"📊 输入图像张量形状: {image_input.shape}")

                self.logger.info("🎨 执行标准图像生成...")
                output_image = self.stream(
                    image=image_input,
                    prompt=params.prompt
                )

            self.logger.info("✅ 图像生成成功完成!")
            if hasattr(output_image, 'size'):
                self.logger.info(f"📏 输出图像尺寸: {output_image.size}")

            return output_image

        except Exception as e:
            self.logger.error(f"💥 图像生成失败: {e}")
            self.logger.error(f"💥 错误详情: {type(e).__name__}: {str(e)}")

            # 降级到标准生成
            try:
                self.logger.info("🔄 尝试降级到标准生成模式...")
                if isinstance(image_input, dict):
                    image_input = image_input["image"]
                    self.logger.info("📊 降级使用主图像张量")

                self.logger.info("🎨 执行降级图像生成...")
                return self.stream(image=image_input, prompt=params.prompt)
            except Exception as fallback_e:
                self.logger.error(f"💥 降级生成也失败: {fallback_e}")
                self.logger.error(f"💥 降级错误详情: {type(fallback_e).__name__}: {str(fallback_e)}")
                raise e

    def generate_with_multi_controlnet(self, **kwargs) -> Image.Image:
        """
        使用多个 ControlNet 生成图像的便捷方法

        Args:
            **kwargs: 生成参数，包括 controlnet_configs

        Returns:
            生成的图像
        """
        # 创建参数对象
        params = self._get_initial_params()

        # 更新参数
        for key, value in kwargs.items():
            if hasattr(params, key):
                setattr(params, key, value)

        # 设置多 ControlNet 配置
        if "controlnet_configs" in kwargs:
            params.multi_controlnet_configs = kwargs["controlnet_configs"]
            params.controlnet_enabled = True  # 确保 ControlNet 启用

        # 设置画布图像
        if "image" in kwargs:
            params.image = kwargs["image"]

        # 执行生成
        return self.predict(params)