"""WebSocket 消息处理器

处理 WebSocket 连接和消息，遵循 StreamDiffusion 官方协议：
1. 客户端发送 {"status": "next_frame"}
2. 客户端发送参数 JSON
3. 客户端发送图像数据（仅 image 模式）
"""

import io
import json
import logging
from typing import Literal, Optional, Tuple

from fastapi import WebSocket, WebSocketDisconnect
from PIL import Image

from app.core.session import SessionManager, Session

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """
    WebSocket 处理器
    
    负责处理 WebSocket 连接生命周期和消息解析。
    遵循 StreamDiffusion 官方协议。
    """
    
    def __init__(self, session_manager: SessionManager):
        """
        初始化 WebSocket 处理器
        
        Args:
            session_manager: 会话管理器实例
        """
        self.session_manager = session_manager
    
    async def handle_connection(
        self,
        websocket: WebSocket,
        user_id: str,
        mode: Literal["image", "video"] = "image"
    ):
        """
        处理 WebSocket 连接生命周期
        
        Args:
            websocket: WebSocket 连接对象
            user_id: 用户 ID
            mode: 输入模式（image 或 video）
        """
        try:
            # 接受连接
            await websocket.accept()
            logger.info(f"WebSocket 连接已建立: {user_id} (模式: {mode})")
            
            # 创建或更新会话
            session = await self.session_manager.create_session(
                user_id=user_id,
                mode=mode,
                websocket=websocket
            )
            
            # 发送连接成功消息
            await self.send_status(websocket, "connected")
            
            # 主消息循环
            while True:
                try:
                    # 发送准备接收帧的消息
                    await self.send_status(websocket, "send_frame")
                    
                    # 接收帧数据（参数 + 图像）
                    params, image = await self.receive_frame_data(websocket, mode)
                    
                    if params is None:
                        # 接收失败，继续下一次循环
                        continue
                    
                    # 更新会话参数
                    await self.session_manager.update_parameters(user_id, params)
                    
                    # 如果有图像，更新会话图像
                    if image is not None:
                        await self.session_manager.update_image(user_id, image)
                    
                    logger.debug(f"接收到帧数据: {user_id}, prompt: {params.get('prompt', '')[:50]}")
                    
                except WebSocketDisconnect:
                    logger.info(f"WebSocket 连接断开: {user_id}")
                    break
                except Exception as e:
                    logger.error(f"处理消息时出错: {e}")
                    await self.send_status(websocket, "error", str(e))
                    # 继续处理下一条消息
        
        except Exception as e:
            logger.error(f"WebSocket 连接处理失败: {e}")
        
        finally:
            # 清理会话
            await self.session_manager.cleanup_session(user_id)
            logger.info(f"会话已清理: {user_id}")
    
    async def receive_frame_data(
        self,
        websocket: WebSocket,
        mode: Literal["image", "video"]
    ) -> Tuple[Optional[dict], Optional[Image.Image]]:
        """
        接收 StreamDiffusion 官方协议的完整帧数据
        
        协议步骤：
        1. receive_json() -> {"status": "next_frame"}
        2. receive_json() -> {params}
        3. receive_bytes() -> image data (仅 image 模式)
        
        Args:
            websocket: WebSocket 连接
            mode: 输入模式
            
        Returns:
            (params_dict, image_or_none) 元组
        """
        try:
            # 步骤 1: 接收 next_frame 消息
            next_frame_msg = await websocket.receive_json()
            
            if not isinstance(next_frame_msg, dict):
                logger.warning(f"收到无效的消息格式: {type(next_frame_msg)}")
                await self.send_status(websocket, "error", "Invalid message format")
                return None, None
            
            status = next_frame_msg.get("status")
            if status != "next_frame":
                logger.warning(f"期望 'next_frame'，收到: {status}")
                await self.send_status(websocket, "error", f"Expected 'next_frame', got '{status}'")
                return None, None
            
            # 步骤 2: 接收参数 JSON
            params = await websocket.receive_json()
            
            if not isinstance(params, dict):
                logger.warning(f"收到无效的参数格式: {type(params)}")
                await self.send_status(websocket, "error", "Invalid parameters format")
                return None, None
            
            # 验证必需参数
            if "prompt" not in params:
                logger.warning("参数中缺少 'prompt' 字段")
                params["prompt"] = ""  # 使用默认空 prompt
            
            # 步骤 3: 接收图像数据（仅 image 模式）
            image = None
            if mode == "image":
                image_bytes = await websocket.receive_bytes()
                
                # 检查图像数据是否为空
                if len(image_bytes) == 0:
                    logger.warning("收到空的图像数据")
                    await self.send_status(websocket, "send_frame")
                    return None, None
                
                try:
                    # 解码图像
                    image = Image.open(io.BytesIO(image_bytes))
                    
                    # 确保图像为 RGB 模式
                    if image.mode != "RGB":
                        image = image.convert("RGB")
                    
                except Exception as e:
                    logger.error(f"图像解码失败: {e}")
                    await self.send_status(websocket, "error", f"Image decode failed: {e}")
                    return None, None
            
            return params, image
        
        except WebSocketDisconnect:
            # 连接断开，向上传播
            raise
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            await self.send_status(websocket, "error", f"JSON parse error: {e}")
            return None, None
        
        except Exception as e:
            logger.error(f"接收帧数据失败: {e}")
            await self.send_status(websocket, "error", f"Failed to receive frame: {e}")
            return None, None
    
    async def send_status(
        self,
        websocket: WebSocket,
        status: Literal["connected", "send_frame", "wait", "error", "timeout"],
        message: Optional[str] = None
    ):
        """
        发送状态消息给客户端
        
        Args:
            websocket: WebSocket 连接
            status: 状态类型
            message: 可选的附加消息
        """
        try:
            response = {"status": status}
            if message:
                response["message"] = message
            
            await websocket.send_json(response)
            logger.debug(f"发送状态: {status}")
        
        except Exception as e:
            logger.error(f"发送状态消息失败: {e}")
    
    async def send_image(self, websocket: WebSocket, image: Image.Image, quality: int = 85):
        """
        发送图像给客户端（备用方法，主要使用 HTTP 流）
        
        Args:
            websocket: WebSocket 连接
            image: 要发送的图像
            quality: JPEG 质量
        """
        try:
            # 将图像编码为 JPEG
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=quality)
            image_bytes = buffer.getvalue()
            
            # 发送图像数据
            await websocket.send_bytes(image_bytes)
            logger.debug(f"发送图像: {len(image_bytes)} 字节")
        
        except Exception as e:
            logger.error(f"发送图像失败: {e}")
