"""StreamDiffusion 引擎封装

封装 StreamDiffusionWrapper，提供：
- 模型加载
- 加速方式初始化（xformers、TensorRT、none）
- TensorRT 引擎路径生成和缓存
- 图像生成（img2img 和 txt2img）
- 运行时参数动态更新
- Warmup 优化
"""

import gc
import logging
import sys
from pathlib import Path
from typing import Literal, Optional

import torch
from PIL import Image

# 添加本地 StreamDiffusion 到路径
streamdiffusion_root = Path(__file__).parent.parent / "lib" / "StreamDiffusion"
streamdiffusion_src = streamdiffusion_root / "src"
streamdiffusion_utils = streamdiffusion_root / "utils"

# 添加 src 目录以导入 streamdiffusion 模块
if str(streamdiffusion_src) not in sys.path:
    sys.path.insert(0, str(streamdiffusion_src))

# 添加 utils 目录以导入 wrapper
if str(streamdiffusion_utils) not in sys.path:
    sys.path.insert(0, str(streamdiffusion_utils))

# 从本地 StreamDiffusion 导入
from streamdiffusion.image_utils import postprocess_image
from wrapper import StreamDiffusionWrapper

from app.config.settings import ModelConfig, PipelineConfig

logger = logging.getLogger(__name__)


class StreamDiffusionEngine:
    """StreamDiffusion 引擎管理器
    
    封装 StreamDiffusion 核心功能，提供统一的接口用于：
    - 模型初始化和加载
    - 加速方式配置（xformers/TensorRT/none）
    - 图像生成（img2img/txt2img）
    - 运行时参数更新
    """
    
    def __init__(
        self,
        model_config: ModelConfig,
        pipeline_config: PipelineConfig,
        device: Optional[torch.device] = None,
        dtype: Optional[torch.dtype] = None
    ):
        """初始化 StreamDiffusion 引擎
        
        Args:
            model_config: 模型配置
            pipeline_config: Pipeline 配置
            device: 计算设备，默认为 CUDA
            dtype: 数据类型，默认为 float16
        """
        self.model_config = model_config
        self.pipeline_config = pipeline_config
        
        # 设置设备和数据类型
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.dtype = dtype or torch.float16
        
        if self.device.type == "cpu":
            logger.warning("未检测到 CUDA，使用 CPU 运行（性能会显著降低）")
            self.dtype = torch.float32  # CPU 不支持 float16
        
        # StreamDiffusion wrapper 实例
        self.stream: Optional[StreamDiffusionWrapper] = None
        
        # 当前参数状态
        self.current_prompt: Optional[str] = None
        self.current_negative_prompt: Optional[str] = None
        
        # 初始化引擎
        self._initialize_engine()
    
    def _initialize_engine(self):
        """初始化 StreamDiffusion 引擎"""
        logger.info(f"初始化 StreamDiffusion 引擎: {self.model_config.model_id}")
        logger.info(f"设备: {self.device}, 数据类型: {self.dtype}")
        logger.info(f"加速方式: {self.model_config.acceleration}")
        
        try:
            # 确定模式
            mode = "img2img" if self.pipeline_config.mode == "image" else "txt2img"
            
            # 根据模型类型选择配置（完全按照 StreamDiffusion demo 的配置）
            model_id_lower = self.model_config.model_id.lower()
            is_turbo = "turbo" in model_id_lower
            
            if is_turbo:
                # SD-Turbo 配置（参考 demo/realtime-img2img/img2img.py）
                t_index_list = [35, 45]
                use_lcm_lora = False  # SD-Turbo 不使用 LCM LoRA
                num_inference_steps = 50
                guidance_scale = 1.2
                logger.info("使用 SD-Turbo 配置: t_index_list=[35, 45], use_lcm_lora=False")
            else:
                # 其他模型配置（参考 demo/realtime-txt2img）
                t_index_list = [0, 16, 32, 45]
                use_lcm_lora = self.pipeline_config.use_lcm_lora
                num_inference_steps = 50
                guidance_scale = 1.2
                logger.info(f"使用标准配置: t_index_list={t_index_list}, use_lcm_lora={use_lcm_lora}")
            
            # 创建 StreamDiffusionWrapper 实例（完全按照 demo 的参数）
            self.stream = StreamDiffusionWrapper(
                model_id_or_path=self.model_config.model_id,
                t_index_list=t_index_list,
                mode=mode,
                device=self.device.type,
                dtype=self.dtype,
                width=self.pipeline_config.width,
                height=self.pipeline_config.height,
                do_add_noise=True,
                frame_buffer_size=self.pipeline_config.frame_buffer_size,
                use_denoising_batch=self.pipeline_config.use_denoising_batch,
                use_lcm_lora=use_lcm_lora,  # 根据模型类型决定
                use_tiny_vae=self.pipeline_config.use_tiny_vae,
                acceleration=self.model_config.acceleration,
                cfg_type="none",  # 与 demo 一致
                warmup=0,  # 稍后手动执行 warmup
                engine_dir=self.model_config.engine_dir,
            )
            
            logger.info("StreamDiffusion 实例创建成功")
            
            # 准备模型（完全按照 demo 的参数）
            self.stream.prepare(
                prompt="",  # 初始空 prompt
                negative_prompt="",
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,  # 使用 1.2 与 demo 一致
            )
            
            logger.info("StreamDiffusion 引擎初始化完成")
            
            # 检测实际使用的加速方式
            self._detect_acceleration()
            
        except Exception as e:
            logger.error(f"StreamDiffusion 引擎初始化失败: {e}")
            raise RuntimeError(f"无法初始化 StreamDiffusion 引擎: {e}")
    
    def _detect_acceleration(self):
        """检测实际使用的加速方式"""
        if self.stream is None:
            return
        
        try:
            # 检查 TensorRT 引擎文件是否存在
            engine_dir = Path(self.model_config.engine_dir)
            has_tensorrt_engines = False
            if engine_dir.exists():
                # 查找 .engine 文件
                engine_files = list(engine_dir.rglob("*.engine"))
                has_tensorrt_engines = len(engine_files) > 0
            
            # 检查 unet 和 vae 的类型来判断加速方式
            unet_type = type(self.stream.stream.unet).__name__
            vae_type = type(self.stream.stream.vae).__name__
            
            # TensorRT 引擎类型
            is_tensorrt = (
                "UNet2DConditionModelEngine" in unet_type or
                "AutoencoderKLEngine" in vae_type or
                has_tensorrt_engines
            )
            
            # xformers 检查（通过检查是否有 memory_efficient_attention）
            is_xformers = False
            try:
                if hasattr(self.stream.stream.pipe, 'unet'):
                    # 检查是否使用了 xformers
                    import xformers
                    is_xformers = True
            except:
                pass
            
            # 输出加速方式状态
            logger.info("=" * 60)
            logger.info("加速方式检测结果:")
            logger.info("=" * 60)
            logger.info(f"配置的加速方式: {self.model_config.acceleration}")
            
            if is_tensorrt:
                logger.info("✓ TensorRT 加速已启用")
                if has_tensorrt_engines:
                    logger.info(f"  - 找到 {len(engine_files)} 个 TensorRT 引擎文件")
                    for engine_file in engine_files[:3]:  # 只显示前3个
                        logger.info(f"    - {engine_file.name}")
                logger.info(f"  - UNet 类型: {unet_type}")
                logger.info(f"  - VAE 类型: {vae_type}")
            elif is_xformers and self.model_config.acceleration == "xformers":
                logger.info("✓ xformers 加速已启用")
            elif self.model_config.acceleration == "none":
                logger.info("✓ 使用默认 PyTorch 实现（无加速）")
            else:
                logger.warning(f"⚠ 配置的加速方式 '{self.model_config.acceleration}' 可能未正确启用")
                logger.info(f"  - UNet 类型: {unet_type}")
                logger.info(f"  - VAE 类型: {vae_type}")
            
            logger.info("=" * 60)
            
        except Exception as e:
            logger.warning(f"检测加速方式时出错: {e}")
    
    def get_acceleration_info(self) -> dict:
        """获取加速方式信息
        
        Returns:
            包含加速方式信息的字典
        """
        if self.stream is None:
            return {"status": "not_initialized"}
        
        try:
            engine_dir = Path(self.model_config.engine_dir)
            engine_files = list(engine_dir.rglob("*.engine")) if engine_dir.exists() else []
            
            unet_type = type(self.stream.stream.unet).__name__
            vae_type = type(self.stream.stream.vae).__name__
            
            is_tensorrt = (
                "UNet2DConditionModelEngine" in unet_type or
                "AutoencoderKLEngine" in vae_type or
                len(engine_files) > 0
            )
            
            return {
                "configured": self.model_config.acceleration,
                "actual": "tensorrt" if is_tensorrt else (
                    "xformers" if self.model_config.acceleration == "xformers" else "none"
                ),
                "tensorrt_enabled": is_tensorrt,
                "tensorrt_engines": len(engine_files),
                "unet_type": unet_type,
                "vae_type": vae_type,
                "engine_dir": str(engine_dir),
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    # StreamDiffusionWrapper 已经处理了 LCM LoRA、Tiny VAE 和加速方式的初始化
    # 这些方法不再需要
    
    def _get_tensorrt_engine_path(self) -> Path:
        """生成 TensorRT 引擎路径
        
        路径格式：{engine_dir}/{model_name}--{options}/
        
        Returns:
            引擎目录路径
        """
        # 从 model_id 提取模型名称
        model_name = self.model_config.model_id.replace("/", "--")
        
        # 构建选项字符串
        options = [
            f"w{self.pipeline_config.width}",
            f"h{self.pipeline_config.height}",
            f"b{self.pipeline_config.frame_buffer_size}",
            f"{'fp16' if self.dtype == torch.float16 else 'fp32'}",
        ]
        
        if self.model_config.use_cuda_graph:
            options.append("cudagraph")
        
        options_str = "-".join(options)
        
        # 完整路径
        engine_dir = Path(self.model_config.engine_dir) / f"{model_name}--{options_str}"
        
        return engine_dir
    
    def generate_image(
        self,
        prompt: str,
        input_image: Optional[Image.Image] = None,
        negative_prompt: str = "",
        num_inference_steps: int = 4,
        guidance_scale: float = 1.0,
        **kwargs
    ) -> Image.Image:
        """生成图像
        
        根据是否提供 input_image 自动选择 img2img 或 txt2img 模式
        
        Args:
            prompt: 提示词
            input_image: 输入图像（可选，None 则为 txt2img 模式）
            negative_prompt: 负面提示词
            num_inference_steps: 推理步数
            guidance_scale: 引导强度
            **kwargs: 其他参数
            
        Returns:
            生成的图像
        """
        if self.stream is None:
            raise RuntimeError("StreamDiffusion 引擎未初始化")
        
        try:
            import time
            start_time = time.time()
            
            # 更新 prompt（如果变化）
            if prompt != self.current_prompt or negative_prompt != self.current_negative_prompt:
                self.update_prompt(prompt, negative_prompt)
            
            # 根据是否有输入图像选择模式
            if input_image is not None:
                # img2img 模式
                output_image = self.stream(
                    image=input_image,
                    prompt=prompt,
                )
            else:
                # txt2img 模式
                output_image = self.stream(
                    prompt=prompt,
                )
            
            # 计算耗时
            elapsed_time = (time.time() - start_time) * 1000  # 转换为毫秒
            logger.info(f"⏱️  帧生成耗时: {elapsed_time:.1f}ms ({1000/elapsed_time:.1f} FPS)")
            
            # StreamDiffusionWrapper 已经返回 PIL Image，无需后处理
            return output_image
            
        except Exception as e:
            logger.error(f"图像生成失败: {e}")
            raise RuntimeError(f"图像生成失败: {e}")
    
    def update_prompt(self, prompt: str, negative_prompt: str = ""):
        """动态更新 prompt（无需重新编译）
        
        Args:
            prompt: 新的提示词
            negative_prompt: 新的负面提示词
        """
        if self.stream is None:
            raise RuntimeError("StreamDiffusion 引擎未初始化")
        
        try:
            logger.debug(f"更新 prompt: {prompt[:50]}...")
            
            # 使用 StreamDiffusionWrapper 的 prepare 方法更新 prompt
            self.stream.prepare(
                prompt=prompt,
                negative_prompt=negative_prompt,
            )
            
            self.current_prompt = prompt
            self.current_negative_prompt = negative_prompt
            
        except Exception as e:
            logger.error(f"更新 prompt 失败: {e}")
            raise RuntimeError(f"更新 prompt 失败: {e}")
    
    def update_parameters(self, params: dict):
        """动态更新生成参数
        
        运行时参数（可动态更新）：
        - prompt: 提示词
        - negative_prompt: 负面提示词
        - guidance_scale: 引导强度
        - num_inference_steps: 推理步数
        
        结构参数（需要重新初始化，不支持动态更新）：
        - width, height: 图像尺寸
        - batch_size: 批处理大小
        
        Args:
            params: 参数字典
        """
        # 提取运行时参数
        prompt = params.get("prompt")
        negative_prompt = params.get("negative_prompt", "")
        
        # 更新 prompt
        if prompt is not None:
            self.update_prompt(prompt, negative_prompt)
        
        # 其他参数（guidance_scale, num_inference_steps）在 generate_image 时传递
        logger.debug(f"参数已更新: {list(params.keys())}")
    
    def warmup(self, steps: int = 10):
        """执行 warmup 以优化首次生成性能
        
        Args:
            steps: warmup 步骤数
        """
        if self.stream is None:
            raise RuntimeError("StreamDiffusion 引擎未初始化")
        
        logger.info(f"执行 warmup ({steps} 步)...")
        
        try:
            # 创建一个空白图像用于 warmup
            dummy_image = Image.new(
                "RGB",
                (self.pipeline_config.width, self.pipeline_config.height),
                color=(128, 128, 128)
            )
            
            # 执行多次生成以预热
            for i in range(steps):
                _ = self.generate_image(
                    prompt="warmup",
                    input_image=dummy_image if self.pipeline_config.mode == "image" else None,
                )
                
                if (i + 1) % 5 == 0:
                    logger.info(f"Warmup 进度: {i + 1}/{steps}")
            
            # 清理 GPU 内存
            self.cleanup_gpu_memory()
            
            logger.info("Warmup 完成")
            
        except Exception as e:
            logger.warning(f"Warmup 失败: {e}")
            # Warmup 失败不应该阻止系统启动
    
    def cleanup_gpu_memory(self):
        """清理 GPU 内存"""
        try:
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            logger.debug("GPU 内存已清理")
        except Exception as e:
            logger.warning(f"GPU 内存清理失败: {e}")
    
    def __del__(self):
        """析构函数，清理资源"""
        try:
            if self.stream is not None:
                del self.stream
                self.cleanup_gpu_memory()
        except Exception:
            pass
