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
                logger.info(f"断开 {len(user_ids)} 个连接...")
                for uid in user_ids:
                    try:
                        await self._conn_manager.disconnect(uid)
                        logger.debug(f"用户 {uid} 连接已断开")
                    except Exception as e:
                        logger.warning(f"断开用户 {uid} 连接失败: {e}")
        except Exception as e:
            logger.warning(f"断开连接时出错: {e}")

        try:
            if self._pipeline is not None:
                logger.info("开始清理 Pipeline 资源...")

                # 清理 ControlNet 处理器
                if hasattr(self._pipeline, "controlnet_processors"):
                    try:
                        logger.info("清理 ControlNet 处理器...")
                        controlnet_processors = getattr(self._pipeline, "controlnet_processors", {})
                        for name, processor in controlnet_processors.items():
                            try:
                                if hasattr(processor, "model"):
                                    del processor.model
                                if hasattr(processor, "device"):
                                    del processor.device
                                logger.debug(f"ControlNet 处理器 {name} 已清理")
                            except Exception as e:
                                logger.warning(f"清理 ControlNet 处理器 {name} 失败: {e}")

                        # 清理处理器字典
                        controlnet_processors.clear()
                        delattr(self._pipeline, "controlnet_processors")
                        logger.info("ControlNet 处理器已清理")
                    except Exception as e:
                        logger.warning(f"清理 ControlNet 处理器时出错: {e}")

                # 清理 StreamDiffusion 流
                if hasattr(self._pipeline, "stream"):
                    try:
                        logger.info("清理 StreamDiffusion 流...")
                        stream = self._pipeline.stream

                        # 清理 UNet
                        if hasattr(stream, "unet"):
                            try:
                                del stream.unet
                                logger.debug("UNet 已清理")
                            except Exception as e:
                                logger.warning(f"清理 UNet 失败: {e}")

                        # 清理 VAE
                        if hasattr(stream, "vae"):
                            try:
                                del stream.vae
                                logger.debug("VAE 已清理")
                            except Exception as e:
                                logger.warning(f"清理 VAE 失败: {e}")

                        # 清理文本编码器
                        if hasattr(stream, "text_encoder"):
                            try:
                                del stream.text_encoder
                                logger.debug("文本编码器已清理")
                            except Exception as e:
                                logger.warning(f"清理文本编码器失败: {e}")

                        # 清理管道
                        if hasattr(stream, "pipe"):
                            try:
                                del stream.pipe
                                logger.debug("管道已清理")
                            except Exception as e:
                                logger.warning(f"清理管道失败: {e}")

                        del self._pipeline.stream
                        logger.debug("StreamDiffusion 流已清理")
                    except Exception as e:
                        logger.warning(f"清理 StreamDiffusion 流时出错: {e}")

                # 清理其他属性
                try:
                    # 清理设备对象
                    if hasattr(self._pipeline, "_device"):
                        delattr(self._pipeline, "_device")

                    # 清理数据类型
                    if hasattr(self._pipeline, "_torch_dtype"):
                        delattr(self._pipeline, "_torch_dtype")

                    logger.debug("Pipeline 其他属性已清理")
                except Exception as e:
                    logger.warning(f"清理 Pipeline 其他属性时出错: {e}")

                # 最后删除 Pipeline
                try:
                    del self._pipeline
                    logger.debug("Pipeline 已删除")
                except Exception as e:
                    logger.warning(f"删除 Pipeline 失败: {e}")

                # 强制垃圾回收
                import gc
                collected = gc.collect()
                logger.info(f"垃圾回收释放了 {collected} 个对象")

                # 清理 GPU 内存
                if torch.cuda.is_available():
                    try:
                        # 获取清理前的内存状态
                        before_memory = torch.cuda.memory_allocated()
                        before_reserved = torch.cuda.memory_reserved()

                        # 清理缓存
                        torch.cuda.empty_cache()
                        torch.cuda.synchronize()

                        # 再次垃圾回收
                        gc.collect()
                        torch.cuda.empty_cache()

                        # 获取清理后的内存状态
                        after_memory = torch.cuda.memory_allocated()
                        after_reserved = torch.cuda.memory_reserved()

                        freed_allocated = (before_memory - after_memory) / 1024**3
                        freed_reserved = (before_reserved - after_reserved) / 1024**3

                        logger.info(f"GPU 内存清理完成: 已分配释放 {freed_allocated:.2f}GB, 已保留释放 {freed_reserved:.2f}GB")
                        logger.info(f"当前 GPU 内存: 已分配 {after_memory / 1024**3:.2f}GB, 已保留 {after_reserved / 1024**3:.2f}GB")

                    except Exception as e:
                        logger.error(f"清理 GPU 内存时出错: {e}")

        except Exception as e:
            logger.error(f"清理 Pipeline 时发生严重错误: {e}")

        # 重置所有引用
        self._pipeline = None
        self._conn_manager = None
        self._config = None
        logger.info("SessionAPI 资源清理完成")

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
