from fastapi import WebSocket, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from types import SimpleNamespace
from app.util import bytes_to_pil
import logging
import asyncio
import torch

logger = logging.getLogger(__name__)


class SessionCreateResponse(BaseModel):
    session_id: str
    message: str = "Session created"


class SessionInfo(BaseModel):
    session_id: str
    is_connected: bool
    queue_size: int = 0


class SessionAPI:
    """抽象的会话 API 实现，可用于 canvas / realtime 两个路由模块。

    用法：
        session = SessionAPI()
        session.init_api(pipeline, config, ConnectionManagerClass)

    然后在路由中委托到 session.* 方法。
    """

    def __init__(self):
        self._pipeline = None
        self._config = None
        self._conn_manager = None

    def init_api(self, pipeline, config: dict, conn_manager_factory):
        self._pipeline = pipeline
        self._config = config
        self._conn_manager = conn_manager_factory()
        logger.debug("SessionAPI initialized")

    async def shutdown_api(self):
        try:
            if self._conn_manager is not None:
                user_ids = list(self._conn_manager.active_connections.keys())
                for uid in user_ids:
                    try:
                        await self._conn_manager.disconnect(uid)
                    except Exception:
                        pass
        except Exception:
            pass

        try:
            if self._pipeline is not None:
                if hasattr(self._pipeline, "stream"):
                    try:
                        del self._pipeline.stream
                    except Exception:
                        pass
                try:
                    del self._pipeline
                except Exception:
                    pass
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
        except Exception:
            pass

        self._pipeline = None
        self._conn_manager = None
        self._config = None

    # --- helpers and endpoint logic ---
    async def create_session(self):
        import uuid
        return SessionCreateResponse(session_id=str(uuid.uuid4()))

    async def get_session(self, session_id):
        if self._conn_manager is None:
            raise HTTPException(status_code=503, detail="API not initialized")
        is_connected = self._conn_manager.check_user(session_id)
        queue_size = 1 if is_connected else 0
        return SessionInfo(session_id=str(session_id), is_connected=is_connected, queue_size=queue_size)

    async def delete_session(self, session_id):
        if self._conn_manager is None:
            raise HTTPException(status_code=503, detail="API not initialized")
        await self._conn_manager.disconnect(session_id)
        return {"message": "Session deleted", "session_id": str(session_id)}

    async def websocket_handler(self, session_id, websocket: WebSocket):
        if self._conn_manager is None:
            await websocket.close(code=503, reason="API not initialized")
            return

        try:
            await self._conn_manager.connect(
                session_id, websocket, self._config.get("max_queue_size", 0) if self._config else 0
            )
            await self._handle_websocket_loop(session_id)
        except Exception as e:
            logger.error(f"Server error on connect: {e}")
        finally:
            try:
                await self._conn_manager.disconnect(session_id)
            except Exception:
                pass

    async def _handle_websocket_loop(self, session_id):
        if self._conn_manager is None or not self._conn_manager.check_user(session_id):
            return HTTPException(status_code=404, detail="Session not found")

        last_time = asyncio.get_event_loop().time()
        try:
            while True:
                # timeout handling
                if (
                    self._config and self._config.get("timeout", 0) > 0
                    and asyncio.get_event_loop().time() - last_time > self._config.get("timeout", 0)
                ):
                    await self._conn_manager.send_json(
                        session_id,
                        {
                            "status": "timeout",
                            "message": "Your session has ended",
                        },
                    )
                    await self._conn_manager.disconnect(session_id)
                    return

                # Support both connection managers that provide `receive_message`
                # (binary packed: (data, image_bytes)) and those that use
                # receive_json/receive_bytes separately.
                if hasattr(self._conn_manager, "receive_message"):
                    data, image_data = await self._conn_manager.receive_message(session_id)
                else:
                    data = await self._conn_manager.receive_json(session_id)
                    image_data = None

                if not data:
                    await asyncio.sleep(0.01)
                    continue

                if data.get("status") == "clear_canvas":
                    # 处理清空画布请求：清空会话数据队列并生成空白图像
                    logger.info(f"收到清空画布请求: session_id={session_id}")
                    try:
                        if self._conn_manager and self._conn_manager.check_user(session_id):
                            # 清空队列中的所有数据
                            user_connection = self._conn_manager.active_connections.get(session_id)
                            if user_connection:
                                while not user_connection["queue"].empty():
                                    try:
                                        user_connection["queue"].get_nowait()
                                    except asyncio.QueueEmpty:
                                        break

                            # 标记会话为已清空状态
                            self._conn_manager.clear_session(session_id)

                            # 标记会话为已清空状态，流会自动处理返回空白帧
                            logger.info(f"已标记会话 {session_id} 为清空状态")

                        # 发送确认响应
                        await self._conn_manager.send_json(session_id, {"status": "canvas_cleared"})
                    except Exception as e:
                        logger.error(f"清空画布时发生错误: {e}")
                    continue

                if data.get("status") == "next_frame":
                    if self._pipeline is None:
                        await asyncio.sleep(0.1)
                        continue

                    info = self._pipeline.Info()

                    # If receive_message returned params expanded, use them;
                    # otherwise, read params via receive_json if not provided.
                    if isinstance(data, dict) and any(k != "status" for k in data.keys()):
                        params_dict = {k: v for k, v in data.items() if k != "status"}
                    else:
                        params_dict = {}

                    if not params_dict:
                        # try to get params separately
                        maybe_params = await self._conn_manager.receive_json(session_id)
                        if isinstance(maybe_params, dict):
                            params_dict = maybe_params

                    if not params_dict:
                        logger.warning(f"收到 next_frame 但没有参数: session_id={session_id}")
                        continue

                    params = self._pipeline.InputParams(**params_dict)
                    params = SimpleNamespace(**params.dict())

                    if info.input_mode == "image":
                        if not image_data:
                            image_data = await self._conn_manager.receive_bytes(session_id)
                        if not image_data:
                            await self._conn_manager.send_json(session_id, {"status": "send_frame"})
                            continue
                        # convert bytes to PIL image if pipeline expects PIL
                        try:
                            params.image = bytes_to_pil(image_data)
                        except Exception:
                            params.image = image_data

                    await self._conn_manager.update_data(session_id, params)

        except Exception as e:
            logger.error(f"Websocket Error: {e}, {session_id}")
            try:
                await self._conn_manager.disconnect(session_id)
            except Exception:
                pass

    async def stream_endpoint(self, session_id, request: Request):
        if self._conn_manager is None or self._pipeline is None:
            raise HTTPException(status_code=503, detail="API not initialized")

        wait_for_data = False
        if hasattr(self._conn_manager, "should_block_for_data"):
            try:
                wait_for_data = bool(self._conn_manager.should_block_for_data())
            except Exception:
                wait_for_data = False

        async def generate():
            frame_count = 0
            while True:
                if await request.is_disconnected():
                    logger.info("Client disconnected from stream: %s", session_id)
                    return
                await self._conn_manager.send_json(session_id, {"status": "send_frame"})
                params = await self._conn_manager.get_latest_data(session_id, wait=wait_for_data)

                # 检查会话是否已被清空，如果是则直接返回空白帧
                if self._conn_manager.is_session_cleared(session_id):
                    # 再次检查队列中是否有新的数据（用户可能已经开始新的绘制）
                    fresh_params = await self._conn_manager.get_latest_data(session_id, wait=False)

                    if fresh_params is None:
                        # 没有新数据，返回空白帧
                        from app.util import pil_to_frame
                        from PIL import Image

                        # 直接创建空白帧并返回
                        blank_image = Image.new('RGB', (512, 512), (255, 255, 255))
                        blank_frame = pil_to_frame(blank_image)

                        frame_count += 1
                        yield blank_frame

                        logger.debug(f"为已清空的会话 {session_id} 返回空白帧")
                        continue
                    else:
                        # 有新数据，使用新数据
                        params = fresh_params

                if params is None:
                    if not wait_for_data:
                        await asyncio.sleep(0.01)
                        continue
                    if not self._conn_manager.check_user(session_id):
                        logger.info("Session %s no longer active; stopping stream", session_id)
                        return
                    continue
                if self._pipeline is None:
                    await asyncio.sleep(0.01)
                    continue

                # pipeline.predict may be blocking, run in thread
                image = await asyncio.to_thread(self._pipeline.predict, params)
                if image is None:
                    logger.warning(f"Image generation failed: session_id={session_id}")
                    continue

                from app.util import pil_to_frame
                frame = pil_to_frame(image)
                frame_count += 1

                # 轻量级内存管理 - 每50帧清理一次，避免激进清理
                if frame_count % 50 == 0:
                    import gc
                    gc.collect()
                    if frame_count % 100 == 0:
                        import torch
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()

                if frame_count % 100 == 0 and logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Stream processed: {frame_count} frames")
                yield frame

        return StreamingResponse(
            generate(), media_type="multipart/x-mixed-replace;boundary=frame", headers={"Cache-Control": "no-cache"}
        )

    async def get_session_queue(self, session_id):
        if self._conn_manager is None:
            return JSONResponse({"queue_size": 0})
        queue_size = 1 if self._conn_manager.check_user(session_id) else 0
        return JSONResponse({"queue_size": queue_size})

    async def settings(self):
        if self._pipeline is None:
            raise HTTPException(status_code=503, detail="Pipeline not initialized")
        info_schema = self._pipeline.Info.schema()
        info = self._pipeline.Info()
        page_content = info.page_content if info.page_content else ""
        input_params = self._pipeline.InputParams.schema()
        return JSONResponse(
            {
                "info": info_schema,
                "input_params": input_params,
                "max_queue_size": self._config.get("max_queue_size", 0) if self._config else 0,
                "page_content": page_content,
            }
        )

    async def queue(self):
        if self._conn_manager is None:
            return JSONResponse({"queue_size": 0})
        queue_size = self._conn_manager.get_user_count()
        return JSONResponse({"queue_size": queue_size})
