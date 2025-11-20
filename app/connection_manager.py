from typing import Dict, Union, Tuple
from uuid import UUID
import asyncio
import json
from fastapi import WebSocket
from starlette.websockets import WebSocketState
from types import SimpleNamespace


class ServerFullException(Exception):
    """Exception raised when the server is full."""
    pass


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[UUID, Dict[str, Union[WebSocket, asyncio.Queue]]] = {}

    async def connect(
        self, user_id: UUID, websocket: WebSocket, max_queue_size: int = 0
    ):
        await websocket.accept()
        user_count = self.get_user_count()
        if max_queue_size > 0 and user_count >= max_queue_size:
            await websocket.send_json({"status": "error", "message": "Server is full"})
            await websocket.close()
            raise ServerFullException("Server is full")
        self.active_connections[user_id] = {
            "websocket": websocket,
            "queue": asyncio.Queue(),
        }
        await websocket.send_json(
            {"status": "connected", "message": "Connected"},
        )
        await websocket.send_json({"status": "wait"})
        await websocket.send_json({"status": "send_frame"})

    def check_user(self, user_id: UUID) -> bool:
        return user_id in self.active_connections

    async def update_data(self, user_id: UUID, new_data: SimpleNamespace):
        user_session = self.active_connections.get(user_id)
        if user_session:
            queue = user_session["queue"]
            await queue.put(new_data)

    async def get_latest_data(self, user_id: UUID) -> SimpleNamespace:
        """获取队列中的最新数据，丢弃所有旧数据
        
        这是关键的性能优化：当前端发送很快时，队列会堆积很多旧帧。
        如果按顺序处理所有旧帧，会导致延迟累积。因此只处理最新帧，丢弃旧帧。
        """
        user_session = self.active_connections.get(user_id)
        if user_session:
            queue = user_session["queue"]
            latest_data = None
            
            # 清空队列，只保留最新的数据
            while not queue.empty():
                try:
                    latest_data = queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
            
            return latest_data
        return None

    def delete_user(self, user_id: UUID):
        user_session = self.active_connections.pop(user_id, None)
        if user_session:
            queue = user_session["queue"]
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    continue

    def get_user_count(self) -> int:
        return len(self.active_connections)

    def get_websocket(self, user_id: UUID) -> WebSocket:
        user_session = self.active_connections.get(user_id)
        if user_session:
            websocket = user_session["websocket"]
            if websocket.client_state == WebSocketState.CONNECTED:
                return user_session["websocket"]
        return None

    async def disconnect(self, user_id: UUID):
        websocket = self.get_websocket(user_id)
        if websocket:
            await websocket.close()
        self.delete_user(user_id)

    async def send_json(self, user_id: UUID, data: Dict):
        try:
            websocket = self.get_websocket(user_id)
            if websocket:
                await websocket.send_json(data)
        except Exception:
            pass

    async def receive_json(self, user_id: UUID) -> Dict:
        try:
            websocket = self.get_websocket(user_id)
            if websocket:
                return await websocket.receive_json()
            else:
                return {}
        except Exception:
            return {}

    async def receive_bytes(self, user_id: UUID) -> bytes:
        try:
            websocket = self.get_websocket(user_id)
            if websocket:
                return await websocket.receive_bytes()
        except Exception:
            return b""
    
    async def receive_message(self, user_id: UUID) -> Tuple[Dict, bytes]:
        """
        接收消息，支持两种格式：
        1. 二进制格式：[4字节JSON长度] + [JSON数据] + [图像数据]
        2. JSON格式：{status: 'next_frame', params: {...}}
        
        Returns:
            (data_dict, image_bytes) 元组
        """
        try:
            websocket = self.get_websocket(user_id)
            if not websocket:
                return {}, b""
            
            # 尝试接收消息
            message = await websocket.receive()
            
            # 检查消息类型
            if "bytes" in message:
                # 二进制格式：[4字节JSON长度] + [JSON数据] + [图像数据]
                binary_data = message["bytes"]
                
                if len(binary_data) < 4:
                    return {}, b""
                
                # 读取JSON长度（大端序）
                json_length = int.from_bytes(binary_data[:4], byteorder="big")
                
                if len(binary_data) < 4 + json_length:
                    return {}, b""
                
                # 解析JSON
                json_bytes = binary_data[4:4 + json_length]
                json_str = json_bytes.decode("utf-8")
                data = json.loads(json_str)
                
                # 提取图像数据
                image_bytes = binary_data[4 + json_length:] if len(binary_data) > 4 + json_length else b""
                
                # 如果JSON中包含params，提取出来
                if "params" in data:
                    params = data["params"]
                    # 保留status字段
                    result = {"status": data.get("status", "next_frame"), **params}
                else:
                    result = data
                
                return result, image_bytes
            
            elif "text" in message:
                # JSON格式
                json_str = message["text"]
                data = json.loads(json_str)
                
                # 如果包含params，提取出来
                if "params" in data:
                    params = data["params"]
                    result = {"status": data.get("status", "next_frame"), **params}
                else:
                    result = data
                
                return result, b""
            
            else:
                return {}, b""
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"接收消息失败: {e}")
            return {}, b""

