"""图像流处理器

通过 HTTP multipart/x-mixed-replace 协议持续推送生成的图像。
"""

import asyncio
import io
import logging
from typing import AsyncGenerator

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image

from app.core.session import SessionManager

logger = logging.getLogger(__name__)


class ImageStreamHandler:
    """
    图像流处理器
    
    负责通过 HTTP multipart 协议推送实时生成的图像。
    """
    
    def __init__(self, session_manager: SessionManager):
        """
        初始化图像流处理器
        
        Args:
            session_manager: 会话管理器实例
        """
        self.session_manager = session_manager
    
    async def stream_images(
        self,
        user_id: str,
        quality: int = 85,
        max_fps: int = 30
    ) -> StreamingResponse:
        """
        生成 multipart/x-mixed-replace 图像流
        
        Args:
            user_id: 用户 ID
            quality: JPEG 质量（1-100）
            max_fps: 最大帧率限制
            
        Returns:
            StreamingResponse 对象
            
        Raises:
            HTTPException: 如果会话不存在
        """
        # 检查会话是否存在
        session = await self.session_manager.get_session(user_id)
        if session is None:
            raise HTTPException(status_code=404, detail=f"Session not found: {user_id}")
        
        logger.info(f"开始图像流: {user_id} (质量: {quality}, 最大FPS: {max_fps})")
        
        # 创建流生成器
        async def generate():
            try:
                frame_interval = 1.0 / max_fps if max_fps > 0 else 0
                last_image_id = None
                
                while True:
                    # 获取会话
                    session = await self.session_manager.get_session(user_id)
                    
                    if session is None or not session.is_active:
                        logger.info(f"会话已结束，停止图像流: {user_id}")
                        break
                    
                    # 获取最新图像
                    if session.latest_image is not None:
                        current_image_id = id(session.latest_image)
                        
                        # 只有当图像更新时才推送
                        if current_image_id != last_image_id:
                            try:
                                # 编码图像
                                image_bytes = await self.encode_image(
                                    session.latest_image,
                                    quality=quality
                                )
                                
                                # 生成 multipart 帧
                                yield (
                                    b"--frame\r\n"
                                    b"Content-Type: image/jpeg\r\n"
                                    f"Content-Length: {len(image_bytes)}\r\n"
                                    b"\r\n"
                                    + image_bytes
                                    + b"\r\n"
                                )
                                
                                last_image_id = current_image_id
                                logger.debug(f"推送图像: {user_id}, 大小: {len(image_bytes)} 字节")
                            
                            except Exception as e:
                                logger.error(f"编码图像失败: {e}")
                    
                    # 帧率限制
                    if frame_interval > 0:
                        await asyncio.sleep(frame_interval)
                    else:
                        # 短暂等待以避免 CPU 占用过高
                        await asyncio.sleep(0.01)
            
            except asyncio.CancelledError:
                logger.info(f"图像流已取消: {user_id}")
            
            except Exception as e:
                logger.error(f"图像流错误: {e}")
            
            finally:
                logger.info(f"图像流已结束: {user_id}")
        
        return StreamingResponse(
            generate(),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )
    
    async def encode_image(
        self,
        image: Image.Image,
        quality: int = 85,
        format: str = "JPEG"
    ) -> bytes:
        """
        将图像编码为字节流
        
        Args:
            image: PIL Image 对象
            quality: 图像质量（1-100）
            format: 图像格式（JPEG/PNG）
            
        Returns:
            编码后的图像字节
        """
        try:
            buffer = io.BytesIO()
            
            # 确保图像为 RGB 模式（JPEG 不支持 RGBA）
            if format.upper() == "JPEG" and image.mode != "RGB":
                image = image.convert("RGB")
            
            # 保存图像到缓冲区
            image.save(buffer, format=format, quality=quality, optimize=True)
            
            return buffer.getvalue()
        
        except Exception as e:
            logger.error(f"图像编码失败: {e}")
            raise RuntimeError(f"Failed to encode image: {e}")
    
    async def get_latest_image(self, user_id: str) -> Image.Image:
        """
        获取会话的最新图像
        
        Args:
            user_id: 用户 ID
            
        Returns:
            最新图像
            
        Raises:
            HTTPException: 如果会话不存在或没有图像
        """
        session = await self.session_manager.get_session(user_id)
        
        if session is None:
            raise HTTPException(status_code=404, detail=f"Session not found: {user_id}")
        
        if session.latest_image is None:
            raise HTTPException(status_code=404, detail=f"No image available for session: {user_id}")
        
        return session.latest_image
