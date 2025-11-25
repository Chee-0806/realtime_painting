"""
StreamDiffusion 通用基类

为所有基于 StreamDiffusionWrapper 的管道提供通用功能，减少代码重复。
"""

import logging
import random
from abc import abstractmethod
from typing import Any, Dict, Optional

import torch
from pydantic import BaseModel, Field
from PIL import Image

from app.pipelines.base import BasePipeline
from app.pipelines.lora_utils import discover_lora_options
from app.config import get_config

# 全局 LoRA 选项（避免重复加载）
LORA_OPTIONS, LORA_PATHS = discover_lora_options()


class StreamDiffusionBasePipeline(BasePipeline):
    """
    StreamDiffusion 通用基类

    提供以下通用功能：
    - LoRA 管理和切换
    - StreamDiffusionWrapper 创建和配置
    - 参数缓存和预处理
    - 种子处理
    """

    class InputParams(BasePipeline.InputParams):
        """StreamDiffusion 通用输入参数"""
        prompt: str = Field(
            "",
            title="Prompt",
            field="textarea",
            id="prompt",
        )
        negative_prompt: str = Field(
            "",
            title="Negative Prompt",
            field="textarea",
            id="negative_prompt",
        )
        width: int = Field(
            512, min=256, max=1024, step=64, title="Width", disabled=True, hide=True, id="width"
        )
        height: int = Field(
            512, min=256, max=1024, step=64, title="Height", disabled=True, hide=True, id="height"
        )
        steps: int = Field(
            2,
            min=1,
            max=10,
            title="Steps",
            id="steps",
            field="range",
        )
        cfg_scale: float = Field(
            2.0,
            min=0.0,
            max=10.0,
            title="CFG Scale",
            id="cfg_scale",
            field="range",
        )
        denoise: float = Field(
            0.3,
            min=0.0,
            max=1.0,
            title="Denoise Strength",
            id="denoise",
            field="range",
        )
        seed: int = Field(
            -1, title="Seed", id="seed"
        )
        lora_selection: str = Field(
            "none",
            title="LoRA Selection",
            id="lora_selection",
            field="select",
            values=LORA_OPTIONS,
        )

    def __init__(self, args: Dict[str, Any], device: torch.device, torch_dtype: torch.dtype):
        """
        初始化基础管道

        Args:
            args: 配置参数字典
            device: PyTorch 设备
            torch_dtype: 数据类型
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self._args = dict(args)
        self._device = device
        self._torch_dtype = torch_dtype
        self._prepare_cache: Dict[str, Any] = {}
        self._active_lora: Optional[str] = None

        # 创建初始流
        initial_params = self._get_initial_params()
        self.stream = self._create_stream(initial_params)
        self._active_lora = initial_params.lora_selection
        self._prepare_if_needed(initial_params)

    @abstractmethod
    def _get_initial_params(self) -> InputParams:
        """
        获取初始参数

        子类可以重写此方法来提供特定的初始参数和默认值

        Returns:
            初始参数对象
        """
        pass

    @abstractmethod
    def _get_pipeline_config(self, params: InputParams) -> Dict[str, Any]:
        """
        获取管道特定配置

        子类重写此方法来提供特定的管道配置

        Args:
            params: 输入参数

        Returns:
            管道配置字典
        """
        pass

    def _resolve_lora_dict(self, selection: Optional[str]) -> Optional[Dict[str, float]]:
        """解析 LoRA 选择"""
        selection_key = selection or "none"
        lora_path = LORA_PATHS.get(selection_key)
        if not lora_path:
            return None
        return {lora_path: 1.0}

    def _create_stream(self, params: InputParams):
        """创建 StreamDiffusionWrapper 实例"""
        # 动态导入以避免循环导入
        import sys
        import os
        sys.path.append(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "lib",
                "StreamDiffusion",
            )
        )
        from utils.wrapper import StreamDiffusionWrapper

        # 获取管道特定配置
        pipeline_config = self._get_pipeline_config(params)

        # 获取模型配置
        config = get_config()
        model_config = config.model

        # 计算 t_index_list
        steps = max(1, int(params.steps))
        if steps <= 4:
            t_index_list = [0, 1] if steps >= 2 else [0]
        elif steps <= 10:
            t_index_list = [steps // 2, steps - 1]
        else:
            t_index_list = [35, 45] if steps >= 50 else [steps // 2, steps - 1]

        # 使用配置文件中的模型配置
        config = {
            "model_id_or_path": self._args.get("model_id", model_config.model_id),
            "use_tiny_vae": model_config.use_tiny_vae if not self._args.get("vae_id") else False,
            "device": self._device,
            "dtype": self._torch_dtype,
            "t_index_list": t_index_list,
            "frame_buffer_size": pipeline_config.get("frame_buffer_size", 1),
            "width": params.width,
            "height": params.height,
            "use_lcm_lora": model_config.use_lcm_lora,
            "output_type": "pil",
            "warmup": pipeline_config.get("warmup", 10),
            "vae_id": self._args.get("vae_id", model_config.vae_id),
            "acceleration": self._args.get("acceleration", model_config.acceleration),
            "mode": "img2img",
            "use_denoising_batch": True,
            "cfg_type": "none",
            "use_safety_checker": self._args.get("use_safety_checker", False),
            "engine_dir": self._args.get("engine_dir", "engines"),
            "lora_dict": self._resolve_lora_dict(params.lora_selection),
        }

        # 应用管道特定配置
        config.update(pipeline_config)

        return StreamDiffusionWrapper(**config)

    def _normalize_seed(self, seed: int) -> int:
        """标准化种子值"""
        if seed is None:
            return 2
        if seed < 0:
            return random.randint(0, 2**31 - 1)
        return int(seed)

    def _prepare_if_needed(self, params: InputParams) -> None:
        """根据需要准备流"""
        prepare_args = {
            "prompt": params.prompt,
            "negative_prompt": params.negative_prompt,
            "num_inference_steps": max(1, int(params.steps)),
            "guidance_scale": float(params.cfg_scale),
            "delta": float(params.denoise),
            "seed": self._normalize_seed(int(params.seed)),
        }

        if self._prepare_cache == prepare_args:
            return

        self.logger.debug("Preparing stream with updated parameters")
        self.stream.prepare(**prepare_args)
        self._prepare_cache = prepare_args

    def _ensure_stream(self, params: InputParams) -> None:
        """确保使用正确的流（处理 LoRA 切换）"""
        selection = params.lora_selection or "none"
        if selection == self._active_lora:
            return

        self.logger.info("Switching LoRA selection to %s", selection)
        self.stream = self._create_stream(params)
        self._prepare_cache = {}
        self._active_lora = selection

    def predict(self, params: InputParams) -> Image.Image:
        """
        执行预测

        Args:
            params: 输入参数

        Returns:
            生成的图像
        """
        self._ensure_stream(params)
        self._prepare_if_needed(params)

        # 预处理输入图像（由子类实现）
        image_tensor = self._preprocess_input_image(params)

        # 执行生成
        output_image = self.stream(image=image_tensor, prompt=params.prompt)

        return output_image

    @abstractmethod
    def _preprocess_input_image(self, params: InputParams):
        """
        预处理输入图像

        子类必须实现此方法来处理特定的输入图像格式

        Args:
            params: 输入参数

        Returns:
            预处理后的图像张量
        """
        pass