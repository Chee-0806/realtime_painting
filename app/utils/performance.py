"""性能优化组件

提供性能优化功能：
- 相似图像过滤
- GPU 内存清理
- 性能监控
"""

import gc
import logging
import time
from typing import Optional

import numpy as np
import torch
from PIL import Image

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """
    性能优化器
    
    提供各种性能优化功能，包括相似图像过滤和内存管理。
    """
    
    def __init__(
        self,
        enable_similar_filter: bool = False,
        similar_threshold: float = 0.98,
        max_skip_frame: int = 10
    ):
        """
        初始化性能优化器
        
        Args:
            enable_similar_filter: 是否启用相似图像过滤
            similar_threshold: 相似度阈值（0-1）
            max_skip_frame: 最大跳帧数
        """
        self.enable_similar_filter = enable_similar_filter
        self.similar_threshold = similar_threshold
        self.max_skip_frame = max_skip_frame
        
        # 上一帧的图像哈希
        self.last_image_hash: Optional[np.ndarray] = None
        self.skip_count = 0
        
        # 性能统计
        self.total_frames = 0
        self.skipped_frames = 0
        self.start_time = time.time()
        
        logger.info(
            f"性能优化器初始化 (相似过滤: {enable_similar_filter}, "
            f"阈值: {similar_threshold}, 最大跳帧: {max_skip_frame})"
        )
    
    def should_skip_frame(self, current_image: Image.Image) -> bool:
        """
        判断是否应该跳过当前帧（相似度过高）
        
        使用简单的图像哈希算法计算相似度。
        
        Args:
            current_image: 当前图像
            
        Returns:
            是否应该跳过
        """
        if not self.enable_similar_filter:
            return False
        
        self.total_frames += 1
        
        try:
            # 计算当前图像的哈希
            current_hash = self._compute_image_hash(current_image)
            
            # 如果是第一帧，不跳过
            if self.last_image_hash is None:
                self.last_image_hash = current_hash
                self.skip_count = 0
                return False
            
            # 计算相似度
            similarity = self._compute_similarity(self.last_image_hash, current_hash)
            
            # 判断是否跳过
            should_skip = (
                similarity > self.similar_threshold
                and self.skip_count < self.max_skip_frame
            )
            
            if should_skip:
                self.skip_count += 1
                self.skipped_frames += 1
                logger.debug(
                    f"跳过相似帧 (相似度: {similarity:.4f}, "
                    f"跳帧计数: {self.skip_count}/{self.max_skip_frame})"
                )
            else:
                # 更新哈希并重置计数
                self.last_image_hash = current_hash
                self.skip_count = 0
            
            return should_skip
        
        except Exception as e:
            logger.error(f"相似度检查失败: {e}")
            return False
    
    def _compute_image_hash(self, image: Image.Image, hash_size: int = 8) -> np.ndarray:
        """
        计算图像的感知哈希（pHash）
        
        Args:
            image: PIL Image 对象
            hash_size: 哈希大小
            
        Returns:
            图像哈希数组
        """
        # 调整图像大小
        resized = image.resize((hash_size, hash_size), Image.Resampling.LANCZOS)
        
        # 转换为灰度
        gray = resized.convert("L")
        
        # 转换为 numpy 数组
        pixels = np.array(gray, dtype=np.float32)
        
        # 计算 DCT（离散余弦变换）的简化版本
        # 这里使用平均值作为简化
        mean = pixels.mean()
        hash_array = (pixels > mean).astype(np.uint8)
        
        return hash_array.flatten()
    
    def _compute_similarity(self, hash1: np.ndarray, hash2: np.ndarray) -> float:
        """
        计算两个哈希的相似度
        
        Args:
            hash1: 第一个哈希
            hash2: 第二个哈希
            
        Returns:
            相似度（0-1）
        """
        # 计算汉明距离
        hamming_distance = np.sum(hash1 != hash2)
        
        # 转换为相似度
        similarity = 1.0 - (hamming_distance / len(hash1))
        
        return similarity
    
    def reset_filter_state(self):
        """重置过滤器状态"""
        self.last_image_hash = None
        self.skip_count = 0
        logger.debug("相似图像过滤器状态已重置")
    
    def get_statistics(self) -> dict:
        """
        获取性能统计信息
        
        Returns:
            统计信息字典
        """
        elapsed_time = time.time() - self.start_time
        avg_fps = self.total_frames / elapsed_time if elapsed_time > 0 else 0
        skip_rate = self.skipped_frames / self.total_frames if self.total_frames > 0 else 0
        
        return {
            "total_frames": self.total_frames,
            "skipped_frames": self.skipped_frames,
            "skip_rate": skip_rate,
            "elapsed_time": elapsed_time,
            "average_fps": avg_fps,
            "similar_filter_enabled": self.enable_similar_filter,
            "similar_threshold": self.similar_threshold,
            "max_skip_frame": self.max_skip_frame
        }
    
    def log_statistics(self):
        """记录性能统计信息"""
        stats = self.get_statistics()
        logger.info(
            f"性能统计: 总帧数={stats['total_frames']}, "
            f"跳过={stats['skipped_frames']}, "
            f"跳帧率={stats['skip_rate']:.2%}, "
            f"平均FPS={stats['average_fps']:.2f}"
        )
    
    @staticmethod
    def cleanup_gpu_memory():
        """
        清理 GPU 内存
        
        调用垃圾回收和 CUDA 缓存清理。
        """
        try:
            # Python 垃圾回收
            gc.collect()
            
            # CUDA 内存清理
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                
                # 获取内存使用情况
                allocated = torch.cuda.memory_allocated() / 1024**3  # GB
                reserved = torch.cuda.memory_reserved() / 1024**3  # GB
                
                logger.debug(
                    f"GPU 内存已清理 (已分配: {allocated:.2f}GB, "
                    f"已保留: {reserved:.2f}GB)"
                )
        
        except Exception as e:
            logger.warning(f"GPU 内存清理失败: {e}")
    
    @staticmethod
    def get_gpu_memory_info() -> dict:
        """
        获取 GPU 内存使用信息
        
        Returns:
            内存信息字典
        """
        if not torch.cuda.is_available():
            return {
                "available": False,
                "message": "CUDA not available"
            }
        
        try:
            allocated = torch.cuda.memory_allocated() / 1024**3  # GB
            reserved = torch.cuda.memory_reserved() / 1024**3  # GB
            total = torch.cuda.get_device_properties(0).total_memory / 1024**3  # GB
            
            return {
                "available": True,
                "allocated_gb": allocated,
                "reserved_gb": reserved,
                "total_gb": total,
                "free_gb": total - allocated,
                "utilization": allocated / total if total > 0 else 0
            }
        
        except Exception as e:
            logger.error(f"获取 GPU 内存信息失败: {e}")
            return {
                "available": True,
                "error": str(e)
            }
    
    @staticmethod
    def log_gpu_memory_info():
        """记录 GPU 内存使用信息"""
        info = PerformanceOptimizer.get_gpu_memory_info()
        
        if not info.get("available"):
            logger.info(f"GPU 内存: {info.get('message', 'Unknown')}")
        elif "error" in info:
            logger.warning(f"GPU 内存信息获取失败: {info['error']}")
        else:
            logger.info(
                f"GPU 内存: 已分配={info['allocated_gb']:.2f}GB, "
                f"已保留={info['reserved_gb']:.2f}GB, "
                f"总计={info['total_gb']:.2f}GB, "
                f"使用率={info['utilization']:.1%}"
            )
