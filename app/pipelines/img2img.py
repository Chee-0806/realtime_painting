import sys
import os
import logging
import random
from typing import Any, Dict, Optional

sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "lib",
        "StreamDiffusion",
    )
)

from utils.wrapper import StreamDiffusionWrapper

import torch
from pydantic import BaseModel, Field
from PIL import Image

from app.pipelines.lora_utils import discover_lora_options

base_model = "stabilityai/sd-turbo"
taesd_model = "madebyollin/taesd"

default_prompt = "flowering tree branch, cherry blossoms, detailed bark texture, natural curves, blooming flowers, delicate petals, botanical illustration, high quality, artistic style"
default_negative_prompt = "straight line, geometric, abstract, blurry, low quality, distorted, deformed, bad anatomy, poorly drawn, watermark, signature, text"

page_content = """<h1 class="text-3xl font-bold">StreamDiffusion</h1>
<h3 class="text-xl font-bold">Image-to-Image SD-Turbo</h3>
<p class="text-sm">
    This demo showcases
    <a
    href="https://github.com/cumulo-autumn/StreamDiffusion"
    target="_blank"
    class="text-blue-500 underline hover:no-underline">StreamDiffusion
</a>
Image to Image pipeline using
    <a
    href="https://huggingface.co/stabilityai/sd-turbo"
    target="_blank"
    class="text-blue-500 underline hover:no-underline">SD-Turbo</a
    > with a MJPEG stream server.
</p>
"""


LORA_OPTIONS, LORA_PATHS = discover_lora_options()


class Pipeline:
    class Info(BaseModel):
        name: str = "StreamDiffusion img2img"
        input_mode: str = "image"
        page_content: str = page_content

    class InputParams(BaseModel):
        class Config:
            extra = "allow"  # 允许额外字段，避免 controlnets 等字段导致验证失败
        
        prompt: str = Field(
            default_prompt,
            title="Prompt",
            field="textarea",
            id="prompt",
        )
        negative_prompt: str = Field(
            default_negative_prompt,
            title="Negative Prompt",
            field="textarea",
            id="negative_prompt",
        )
        width: int = Field(
            512, min=2, max=15, title="Width", disabled=True, hide=True, id="width"
        )
        height: int = Field(
            512, min=2, max=15, title="Height", disabled=True, hide=True, id="height"
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
            502923423887318, title="Seed", id="seed"
        )
        lora_selection: str = Field(
            "none",
            title="LoRA Selection",
            id="lora_selection",
            field="select",
            values=LORA_OPTIONS,
        )

    def __init__(self, args, device: torch.device, torch_dtype: torch.dtype):
        self.logger = logging.getLogger(__name__)
        self._args = dict(args)
        self._device = device
        self._torch_dtype = torch_dtype
        self._prepare_cache: Dict[str, Any] = {}
        self._active_lora: Optional[str] = None

        initial_params = self.InputParams()
        self.stream = self._create_stream(initial_params)
        self._active_lora = initial_params.lora_selection
        self._prepare_if_needed(initial_params)

    def _create_stream(self, params: "Pipeline.InputParams") -> StreamDiffusionWrapper:
        return StreamDiffusionWrapper(
            model_id_or_path=self._args.get("model_id", base_model),
            use_tiny_vae=False
            if self._args.get("vae_id")
            else self._args.get("use_tiny_vae", True),
            device=self._device,
            dtype=self._torch_dtype,
            t_index_list=[35, 45],
            frame_buffer_size=1,
            width=params.width,
            height=params.height,
            use_lcm_lora=False,
            output_type="pil",
            warmup=10,
            vae_id=self._args.get("vae_id"),
            acceleration=self._args.get("acceleration", "xformers"),
            mode="img2img",
            use_denoising_batch=True,
            cfg_type="none",
            use_safety_checker=self._args.get("use_safety_checker", False),
            engine_dir=self._args.get("engine_dir", "engines"),
            enable_similar_image_filter=self._args.get("enable_similar_image_filter", False),
            similar_image_filter_threshold=self._args.get("similar_image_filter_threshold", 0.98),
            similar_image_filter_max_skip_frame=self._args.get("similar_image_filter_max_skip_frame", 10),
            lora_dict=self._resolve_lora_dict(params.lora_selection),
        )

    def _resolve_lora_dict(self, selection: Optional[str]) -> Optional[Dict[str, float]]:
        selection_key = selection or "none"
        lora_path = LORA_PATHS.get(selection_key)
        if not lora_path:
            return None
        return {lora_path: 1.0}

    def _normalize_seed(self, seed: int) -> int:
        if seed is None:
            return 2
        if seed < 0:
            return random.randint(0, 2**31 - 1)
        return int(seed)

    def _prepare_if_needed(self, params: "Pipeline.InputParams") -> None:
        prepare_args: Dict[str, Any] = {
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

    def _ensure_stream(self, params: "Pipeline.InputParams") -> None:
        selection = params.lora_selection or "none"
        if selection == self._active_lora:
            return

        self.logger.info("Switching LoRA selection to %s", selection)
        self.stream = self._create_stream(params)
        self._prepare_cache = {}
        self._active_lora = selection

    def predict(self, params: "Pipeline.InputParams") -> Image.Image:
        self._ensure_stream(params)
        self._prepare_if_needed(params)

        image_tensor = self.stream.preprocess_image(params.image)
        output_image = self.stream(image=image_tensor, prompt=params.prompt)

        return output_image
