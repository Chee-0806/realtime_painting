import sys
import os

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

base_model = "stabilityai/sd-turbo"
taesd_model = "madebyollin/taesd"

default_prompt = "Portrait of The Joker halloween costume, face painting, with , glare pose, detailed, intricate, full of colour, cinematic lighting, trending on artstation, 8k, hyperrealistic, focused, extreme details, unreal engine 5 cinematic, masterpiece"
default_negative_prompt = "black and white, blurry, low resolution, pixelated,  pixel art, low quality, low fidelity"

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
            2, min=1, max=10, title="Steps", id="steps"
        )
        cfg_scale: float = Field(
            2.0, min=0.0, max=10.0, title="CFG Scale", id="cfg_scale"
        )
        denoise: float = Field(
            0.3, min=0.0, max=1.0, title="Denoise Strength", id="denoise"
        )
        seed: int = Field(
            502923423887318, title="Seed", id="seed"
        )
        lora_selection: str = Field(
            "none", title="LoRA Selection", id="lora_selection"
        )

    def __init__(self, args, device: torch.device, torch_dtype: torch.dtype):
        import logging
        self.logger = logging.getLogger(__name__)
        
        params = self.InputParams()
        self.stream = StreamDiffusionWrapper(
            model_id_or_path=args.get("model_id", base_model),
            use_tiny_vae=False if args.get("vae_id") else args.get("use_tiny_vae", True),
            device=device,
            dtype=torch_dtype,
            t_index_list=[35, 45],
            frame_buffer_size=1,
            width=params.width,
            height=params.height,
            use_lcm_lora=False,
            output_type="pil",
            warmup=10,
            vae_id=args.get("vae_id"),
            acceleration=args.get("acceleration", "xformers"),
            mode="img2img",
            use_denoising_batch=True,
            cfg_type="none",
            use_safety_checker=args.get("use_safety_checker", False),
            engine_dir=args.get("engine_dir", "engines"),
        )

        self.last_prompt = default_prompt
        self.last_negative_prompt = default_negative_prompt
        self.stream.prepare(
            prompt=default_prompt,
            negative_prompt=default_negative_prompt,
            num_inference_steps=50,
            guidance_scale=1.2,
        )

    def predict(self, params: "Pipeline.InputParams") -> Image.Image:
        import time
        start_time = time.time()
        
        # 更新 prompt（如果变化）
        if params.prompt != self.last_prompt or params.negative_prompt != self.last_negative_prompt:
            self.logger.info(f"更新 prompt: {params.prompt[:50]}...")
            self.stream.prepare(
                prompt=params.prompt,
                negative_prompt=params.negative_prompt,
            )
            self.last_prompt = params.prompt
            self.last_negative_prompt = params.negative_prompt
        
        # 预处理图像
        image_tensor = self.stream.preprocess_image(params.image)
        
        # 生成图像
        output_image = self.stream(image=image_tensor, prompt=params.prompt)
        
        # 性能日志
        elapsed_time = (time.time() - start_time) * 1000
        self.logger.info(f"⏱️  帧生成耗时: {elapsed_time:.1f}ms ({1000/elapsed_time:.1f} FPS)")

        return output_image
