"""会话管理系统

管理用户会话，支持：
- 会话创建、获取、更新、清理
- 线程安全的并发访问控制
- 会话状态跟踪
- 超时管理
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Literal, Optional

from fastapi import WebSocket
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class Session:
    """
    会话数据类
    
    存储单个用户会话的所有状态信息。
    """
    user_id: str
    """用户唯一标识符"""
    
    websocket: Optional[WebSocket] = None
    """WebSocket 连接对象"""
    
    latest_image: Optional[Image.Image] = None
    """最新生成的图像"""
    
    parameters: dict = field(default_factory=dict)
    """当前生成参数"""
    
    is_active: bool = True
    """会话是否活跃"""
    
    last_activity: datetime = field(default_factory=datetime.now)
    """最后活动时间"""
    
    mode: Literal["image", "video"] = "image"
    """输入模式：image (img2img) 或 video (txt2img)"""
    
    created_at: datetime = field(default_factory=datetime.now)
    """会话创建时间"""
    
    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity = datetime.now()
    
    def is_expired(self, timeout_seconds: int) -> bool:
        """
        检查会话是否超时
        
        Args:
            timeout_seconds: 超时时间（秒），0 表示永不超时
            
        Returns:
            是否超时
        """
        if timeout_seconds <= 0:
            return False
        
        elapsed = (datetime.now() - self.last_activity).total_seconds()
        return elapsed > timeout_seconds
    
    def to_dict(self) -> dict:
        """
        转换为字典（用于日志和调试）
        
        Returns:
            会话信息字典
        """
        return {
            "user_id": self.user_id,
            "is_active": self.is_active,
            "mode": self.mode,
            "has_websocket": self.websocket is not None,
            "has_image": self.latest_image is not None,
            "parameters": self.parameters,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
        }


class SessionManager:
    """
    会话管理器
    
    管理所有用户会话，提供线程安全的会话操作。
    使用 asyncio.Lock 保护并发访问。
    """
    
    def __init__(self, timeout: int = 0):
        """
        初始化会话管理器
        
        Args:
            timeout: 会话超时时间（秒），0 表示永不超时
        """
        self._sessions: Dict[str, Session] = {}
        self._lock = asyncio.Lock()
        self._timeout = timeout
        
        logger.info(f"会话管理器初始化完成 (超时: {timeout}s)")
    
    async def create_session(
        self,
        user_id: str,
        mode: Literal["image", "video"] = "image",
        websocket: Optional[WebSocket] = None
    ) -> Session:
        """
        创建新会话
        
        如果会话已存在，则更新现有会话。
        
        Args:
            user_id: 用户 ID
            mode: 输入模式
            websocket: WebSocket 连接（可选）
            
        Returns:
            创建或更新的会话对象
        """
        async with self._lock:
            if user_id in self._sessions:
                # 会话已存在，更新它
                logger.info(f"会话已存在，更新会话: {user_id}")
                session = self._sessions[user_id]
                session.websocket = websocket
                session.mode = mode
                session.is_active = True
                session.update_activity()
            else:
                # 创建新会话
                logger.info(f"创建新会话: {user_id} (模式: {mode})")
                session = Session(
                    user_id=user_id,
                    websocket=websocket,
                    mode=mode,
                    is_active=True
                )
                self._sessions[user_id] = session
            
            return session
    
    async def get_session(self, user_id: str) -> Optional[Session]:
        """
        获取会话
        
        Args:
            user_id: 用户 ID
            
        Returns:
            会话对象，如果不存在则返回 None
        """
        async with self._lock:
            session = self._sessions.get(user_id)
            
            if session is not None:
                # 检查是否超时
                if session.is_expired(self._timeout):
                    logger.warning(f"会话已超时: {user_id}")
                    session.is_active = False
                    return None
                
                session.update_activity()
            
            return session
    
    async def update_image(self, user_id: str, image: Image.Image):
        """
        更新会话的最新图像
        
        Args:
            user_id: 用户 ID
            image: 新图像
        """
        async with self._lock:
            session = self._sessions.get(user_id)
            
            if session is not None:
                session.latest_image = image
                session.update_activity()
                logger.debug(f"更新会话图像: {user_id}")
            else:
                logger.warning(f"尝试更新不存在的会话图像: {user_id}")
    
    async def update_parameters(self, user_id: str, parameters: dict):
        """
        更新会话参数
        
        Args:
            user_id: 用户 ID
            parameters: 新参数
        """
        async with self._lock:
            session = self._sessions.get(user_id)
            
            if session is not None:
                session.parameters.update(parameters)
                session.update_activity()
                logger.debug(f"更新会话参数: {user_id}")
            else:
                logger.warning(f"尝试更新不存在的会话参数: {user_id}")
    
    async def update_websocket(self, user_id: str, websocket: WebSocket):
        """
        更新会话的 WebSocket 连接
        
        Args:
            user_id: 用户 ID
            websocket: 新的 WebSocket 连接
        """
        async with self._lock:
            session = self._sessions.get(user_id)
            
            if session is not None:
                session.websocket = websocket
                session.update_activity()
                logger.debug(f"更新会话 WebSocket: {user_id}")
            else:
                logger.warning(f"尝试更新不存在的会话 WebSocket: {user_id}")
    
    async def cleanup_session(self, user_id: str):
        """
        清理会话资源
        
        Args:
            user_id: 用户 ID
        """
        async with self._lock:
            session = self._sessions.get(user_id)
            
            if session is not None:
                logger.info(f"清理会话: {user_id}")
                
                # 标记为不活跃
                session.is_active = False
                
                # 清理资源
                session.websocket = None
                session.latest_image = None
                session.parameters.clear()
                
                # 从字典中移除
                del self._sessions[user_id]
            else:
                logger.warning(f"尝试清理不存在的会话: {user_id}")
    
    async def cleanup_expired_sessions(self):
        """
        清理所有超时的会话
        
        Returns:
            清理的会话数量
        """
        if self._timeout <= 0:
            return 0
        
        async with self._lock:
            expired_users = []
            
            for user_id, session in self._sessions.items():
                if session.is_expired(self._timeout):
                    expired_users.append(user_id)
            
            # 清理超时会话
            for user_id in expired_users:
                logger.info(f"清理超时会话: {user_id}")
                session = self._sessions[user_id]
                session.is_active = False
                session.websocket = None
                session.latest_image = None
                session.parameters.clear()
                del self._sessions[user_id]
            
            if expired_users:
                logger.info(f"清理了 {len(expired_users)} 个超时会话")
            
            return len(expired_users)
    
    async def get_active_session_count(self) -> int:
        """
        获取活跃会话数量
        
        Returns:
            活跃会话数量
        """
        async with self._lock:
            return sum(1 for session in self._sessions.values() if session.is_active)
    
    async def get_all_sessions(self) -> list[Session]:
        """
        获取所有会话（用于调试和监控）
        
        Returns:
            会话列表
        """
        async with self._lock:
            return list(self._sessions.values())
    
    async def session_exists(self, user_id: str) -> bool:
        """
        检查会话是否存在
        
        Args:
            user_id: 用户 ID
            
        Returns:
            会话是否存在
        """
        async with self._lock:
            return user_id in self._sessions
    
    def get_timeout(self) -> int:
        """
        获取超时设置
        
        Returns:
            超时时间（秒）
        """
        return self._timeout
    
    def set_timeout(self, timeout: int):
        """
        设置超时时间
        
        Args:
            timeout: 超时时间（秒），0 表示永不超时
        """
        self._timeout = timeout
        logger.info(f"会话超时时间已更新: {timeout}s")
    
    async def get_session_info(self, user_id: str) -> Optional[dict]:
        """
        获取会话信息（用于调试）
        
        Args:
            user_id: 用户 ID
            
        Returns:
            会话信息字典，如果不存在则返回 None
        """
        session = await self.get_session(user_id)
        if session is not None:
            return session.to_dict()
        return None
    
    async def get_all_session_info(self) -> list[dict]:
        """
        获取所有会话信息（用于调试和监控）
        
        Returns:
            会话信息列表
        """
        async with self._lock:
            return [session.to_dict() for session in self._sessions.values()]


# 全局会话管理器实例
_session_manager: Optional[SessionManager] = None


def get_session_manager(timeout: int = 0) -> SessionManager:
    """
    获取全局会话管理器实例（单例模式）
    
    Args:
        timeout: 会话超时时间（秒），仅在首次创建时使用
        
    Returns:
        SessionManager 实例
    """
    global _session_manager
    
    if _session_manager is None:
        _session_manager = SessionManager(timeout=timeout)
    
    return _session_manager


def reset_session_manager():
    """
    重置全局会话管理器（用于测试）
    """
    global _session_manager
    _session_manager = None
