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
from pathlib import Path
from typing import Literal, Optional

import torch
from PIL import Image
from streamdiffusion import StreamDiffusion
from streamdiffusion.image_utils import postprocess_image

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
        self.stream: Optional[StreamDiffusion] = None
        
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
            # 创建 StreamDiffusion 实例
            self.stream = StreamDiffusion(
                model_id_or_path=self.model_config.model_id,
                t_index_list=[0, 16, 32, 45],  # StreamDiffusion 推荐的时间步
                torch_dtype=self.dtype,
                width=self.pipeline_config.width,
                height=self.pipeline_config.height,
                do_add_noise=True,
                frame_buffer_size=self.pipeline_config.frame_buffer_size,
                use_denoising_batch=self.pipeline_config.use_denoising_batch,
                cfg_type="none",  # 使用 LCM 时通常不需要 CFG
            )
            
            logger.info("StreamDiffusion 实例创建成功")
            
            # 加载 LoRA（如果配置）
            if self.pipeline_config.use_lcm_lora:
                self._load_lcm_lora()
            
            # 使用 Tiny VAE（如果配置）
            if self.pipeline_config.use_tiny_vae:
                self._load_tiny_vae()
            
            # 初始化加速方式
            self._init_acceleration()
            
            # 准备模型
            self.stream.prepare(
                prompt="",  # 初始空 prompt
                negative_prompt="",
                num_inference_steps=4,
                guidance_scale=1.0,
            )
            
            logger.info("StreamDiffusion 引擎初始化完成")
            
        except Exception as e:
            logger.error(f"StreamDiffusion 引擎初始化失败: {e}")
            raise RuntimeError(f"无法初始化 StreamDiffusion 引擎: {e}")
    
    def _load_lcm_lora(self):
        """加载 LCM LoRA"""
        try:
            logger.info("加载 LCM LoRA...")
            self.stream.load_lcm_lora()
            self.stream.fuse_lora()
            logger.info("LCM LoRA 加载成功")
        except Exception as e:
            logger.warning(f"LCM LoRA 加载失败: {e}")
            raise RuntimeError(f"无法加载 LCM LoRA: {e}")
    
    def _load_tiny_vae(self):
        """加载 Tiny VAE"""
        try:
            logger.info("加载 Tiny VAE...")
            # Tiny VAE 模型 ID
            tiny_vae_id = "madebyollin/taesd"
            from diffusers import AutoencoderTiny
            
            tiny_vae = AutoencoderTiny.from_pretrained(
                tiny_vae_id,
                torch_dtype=self.dtype
            ).to(self.device)
            
            self.stream.vae = tiny_vae
            logger.info("Tiny VAE 加载成功")
        except Exception as e:
            logger.warning(f"Tiny VAE 加载失败，使用默认 VAE: {e}")
    
    def _init_acceleration(self):
        """初始化加速方式
        
        支持的加速方式：
        - xformers: 内存高效的注意力机制
        - tensorrt: NVIDIA TensorRT 优化
        - none: 不使用加速
        
        如果加速方式初始化失败，抛出异常（不降级）
        """
        acceleration = self.model_config.acceleration
        
        logger.info(f"初始化加速方式: {acceleration}")
        
        try:
            if acceleration == "xformers":
                self._init_xformers()
            elif acceleration == "tensorrt":
                self._init_tensorrt()
            elif acceleration == "none":
                logger.info("不使用加速，使用默认 PyTorch 实现")
            else:
                raise ValueError(f"不支持的加速方式: {acceleration}")
                
        except Exception as e:
            logger.error(f"加速方式 {acceleration} 初始化失败: {e}")
            raise RuntimeError(
                f"无法初始化加速方式 '{acceleration}': {e}\n"
                f"请检查依赖是否正确安装，或在配置中更改加速方式"
            )
    
    def _init_xformers(self):
        """初始化 xformers 加速"""
        try:
            # 尝试启用 xformers
            self.stream.pipe.enable_xformers_memory_efficient_attention()
            logger.info("xformers 加速已启用")
        except Exception as e:
            raise RuntimeError(
                f"xformers 初始化失败: {e}\n"
                f"请确保已安装 xformers: pip install -r requirements-xformers.txt"
            )
    
    def _init_tensorrt(self):
        """初始化 TensorRT 加速"""
        try:
            # 检查 TensorRT 依赖
            try:
                import tensorrt as trt
                logger.info(f"检测到 TensorRT 版本: {trt.__version__}")
            except ImportError:
                raise RuntimeError(
                    "TensorRT 未安装。请安装 TensorRT 依赖:\n"
                    "pip install -r requirements-tensorrt.txt"
                )
            
            # 创建引擎目录
            engine_dir = Path(self.model_config.engine_dir)
            engine_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成 TensorRT 引擎路径
            engine_path = self._get_tensorrt_engine_path()
            
            logger.info(f"TensorRT 引擎路径: {engine_path}")
            
            # 编译或加载 TensorRT 引擎
            if engine_path.exists():
                logger.info("检测到已存在的 TensorRT 引擎，加载中...")
            else:
                logger.info("首次运行，编译 TensorRT 引擎（这可能需要 5-10 分钟）...")
            
            # 使用 StreamDiffusion 的 TensorRT 加速
            use_cuda_graph = self.model_config.use_cuda_graph
            
            self.stream.compile(
                backend="tensorrt",
                mode="max-autotune",
                use_cuda_graph=use_cuda_graph,
            )
            
            logger.info(f"TensorRT 加速已启用 (CUDA Graph: {use_cuda_graph})")
            
        except Exception as e:
            raise RuntimeError(
                f"TensorRT 初始化失败: {e}\n"
                f"请检查 TensorRT 依赖是否正确安装"
            )
    
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
            
            # 后处理图像
            if isinstance(output_image, torch.Tensor):
                output_image = postprocess_image(output_image, output_type="pil")[0]
            
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
            
            # 使用 StreamDiffusion 的 prepare 方法更新 prompt
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
