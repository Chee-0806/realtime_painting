"""图像处理工具

提供图像编码、解码、转换和验证功能。
"""

import io
import logging
from typing import Literal, Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def encode_image(
    image: Image.Image,
    format: Literal["JPEG", "PNG", "WEBP"] = "JPEG",
    quality: int = 85,
    optimize: bool = True
) -> bytes:
    """
    将 PIL Image 编码为字节流
    
    Args:
        image: PIL Image 对象
        format: 图像格式
        quality: 质量（1-100，仅用于 JPEG 和 WEBP）
        optimize: 是否优化
        
    Returns:
        编码后的图像字节
    """
    try:
        buffer = io.BytesIO()
        
        # 确保图像模式正确
        if format == "JPEG":
            # JPEG 不支持透明度
            if image.mode in ("RGBA", "LA", "P"):
                # 创建白色背景
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(image, mask=image.split()[-1] if image.mode in ("RGBA", "LA") else None)
                image = background
            elif image.mode != "RGB":
                image = image.convert("RGB")
            
            image.save(buffer, format=format, quality=quality, optimize=optimize)
        
        elif format == "PNG":
            # PNG 支持透明度
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGBA")
            
            image.save(buffer, format=format, optimize=optimize)
        
        elif format == "WEBP":
            # WEBP 支持透明度
            image.save(buffer, format=format, quality=quality, method=6)
        
        else:
            raise ValueError(f"不支持的图像格式: {format}")
        
        return buffer.getvalue()
    
    except Exception as e:
        logger.error(f"图像编码失败: {e}")
        raise RuntimeError(f"Failed to encode image: {e}")


def decode_image(image_bytes: bytes) -> Image.Image:
    """
    将字节流解码为 PIL Image
    
    Args:
        image_bytes: 图像字节流
        
    Returns:
        PIL Image 对象
    """
    try:
        buffer = io.BytesIO(image_bytes)
        image = Image.open(buffer)
        
        # 加载图像数据
        image.load()
        
        return image
    
    except Exception as e:
        logger.error(f"图像解码失败: {e}")
        raise RuntimeError(f"Failed to decode image: {e}")


def validate_image(
    image: Image.Image,
    max_width: Optional[int] = None,
    max_height: Optional[int] = None,
    allowed_modes: Optional[list[str]] = None
) -> Tuple[bool, Optional[str]]:
    """
    验证图像是否符合要求
    
    Args:
        image: PIL Image 对象
        max_width: 最大宽度（可选）
        max_height: 最大高度（可选）
        allowed_modes: 允许的颜色模式列表（可选）
        
    Returns:
        (是否有效, 错误消息) 元组
    """
    try:
        # 检查尺寸
        if max_width is not None and image.width > max_width:
            return False, f"图像宽度 {image.width} 超过最大值 {max_width}"
        
        if max_height is not None and image.height > max_height:
            return False, f"图像高度 {image.height} 超过最大值 {max_height}"
        
        # 检查颜色模式
        if allowed_modes is not None and image.mode not in allowed_modes:
            return False, f"图像模式 {image.mode} 不在允许列表中: {allowed_modes}"
        
        return True, None
    
    except Exception as e:
        logger.error(f"图像验证失败: {e}")
        return False, f"验证失败: {e}"


def resize_image(
    image: Image.Image,
    width: int,
    height: int,
    resample: Image.Resampling = Image.Resampling.LANCZOS,
    maintain_aspect_ratio: bool = False
) -> Image.Image:
    """
    调整图像大小
    
    Args:
        image: PIL Image 对象
        width: 目标宽度
        height: 目标高度
        resample: 重采样方法
        maintain_aspect_ratio: 是否保持宽高比
        
    Returns:
        调整大小后的图像
    """
    try:
        if maintain_aspect_ratio:
            # 计算保持宽高比的尺寸
            aspect_ratio = image.width / image.height
            target_ratio = width / height
            
            if aspect_ratio > target_ratio:
                # 图像更宽，以宽度为准
                new_width = width
                new_height = int(width / aspect_ratio)
            else:
                # 图像更高，以高度为准
                new_height = height
                new_width = int(height * aspect_ratio)
            
            resized = image.resize((new_width, new_height), resample)
            
            # 创建目标尺寸的画布并居中粘贴
            canvas = Image.new(image.mode, (width, height), (0, 0, 0))
            offset_x = (width - new_width) // 2
            offset_y = (height - new_height) // 2
            canvas.paste(resized, (offset_x, offset_y))
            
            return canvas
        else:
            # 直接调整到目标尺寸
            return image.resize((width, height), resample)
    
    except Exception as e:
        logger.error(f"图像调整大小失败: {e}")
        raise RuntimeError(f"Failed to resize image: {e}")


def convert_image_mode(
    image: Image.Image,
    mode: Literal["RGB", "RGBA", "L", "P"]
) -> Image.Image:
    """
    转换图像颜色模式
    
    Args:
        image: PIL Image 对象
        mode: 目标颜色模式
        
    Returns:
        转换后的图像
    """
    try:
        if image.mode == mode:
            return image
        
        return image.convert(mode)
    
    except Exception as e:
        logger.error(f"图像模式转换失败: {e}")
        raise RuntimeError(f"Failed to convert image mode: {e}")


def image_to_numpy(image: Image.Image) -> np.ndarray:
    """
    将 PIL Image 转换为 numpy 数组
    
    Args:
        image: PIL Image 对象
        
    Returns:
        numpy 数组 (H, W, C)
    """
    try:
        return np.array(image)
    
    except Exception as e:
        logger.error(f"图像转 numpy 失败: {e}")
        raise RuntimeError(f"Failed to convert image to numpy: {e}")


def numpy_to_image(array: np.ndarray) -> Image.Image:
    """
    将 numpy 数组转换为 PIL Image
    
    Args:
        array: numpy 数组 (H, W, C) 或 (H, W)
        
    Returns:
        PIL Image 对象
    """
    try:
        # 确保数据类型正确
        if array.dtype != np.uint8:
            # 假设值在 0-1 范围内
            if array.max() <= 1.0:
                array = (array * 255).astype(np.uint8)
            else:
                array = array.astype(np.uint8)
        
        return Image.fromarray(array)
    
    except Exception as e:
        logger.error(f"numpy 转图像失败: {e}")
        raise RuntimeError(f"Failed to convert numpy to image: {e}")


def create_placeholder_image(
    width: int,
    height: int,
    color: Tuple[int, int, int] = (128, 128, 128),
    text: Optional[str] = None
) -> Image.Image:
    """
    创建占位图像
    
    Args:
        width: 宽度
        height: 高度
        color: 背景颜色 (R, G, B)
        text: 可选的文本（需要 PIL 支持字体）
        
    Returns:
        占位图像
    """
    try:
        image = Image.new("RGB", (width, height), color)
        
        if text:
            try:
                from PIL import ImageDraw, ImageFont
                
                draw = ImageDraw.Draw(image)
                
                # 尝试使用默认字体
                try:
                    font = ImageFont.truetype("arial.ttf", 20)
                except:
                    font = ImageFont.load_default()
                
                # 计算文本位置（居中）
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                position = (
                    (width - text_width) // 2,
                    (height - text_height) // 2
                )
                
                draw.text(position, text, fill=(255, 255, 255), font=font)
            
            except Exception as e:
                logger.warning(f"添加文本到占位图像失败: {e}")
        
        return image
    
    except Exception as e:
        logger.error(f"创建占位图像失败: {e}")
        raise RuntimeError(f"Failed to create placeholder image: {e}")


def get_image_info(image: Image.Image) -> dict:
    """
    获取图像信息
    
    Args:
        image: PIL Image 对象
        
    Returns:
        图像信息字典
    """
    return {
        "width": image.width,
        "height": image.height,
        "mode": image.mode,
        "format": image.format,
        "size_bytes": len(image.tobytes()) if hasattr(image, 'tobytes') else None
    }
