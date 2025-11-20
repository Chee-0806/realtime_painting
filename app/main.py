from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request

import logging
import uuid
import time
from types import SimpleNamespace
import asyncio
import os
import mimetypes
import torch

from app.config.settings import get_settings
from app.util import pil_to_frame, bytes_to_pil
from app.connection_manager import ConnectionManager, ServerFullException
from app.pipelines.img2img import Pipeline
from app.api import models

# fix mime error on windows
mimetypes.add_type("application/javascript", ".js")

# 减少日志输出
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

THROTTLE = 1.0 / 120


class App:
    def __init__(self, config, pipeline):
        self.config = config
        self.pipeline = pipeline
        self.app = FastAPI()
        self.conn_manager = ConnectionManager()
        self.init_app()

    def init_app(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @self.app.websocket("/api/ws/{user_id}")
        async def websocket_endpoint(user_id: uuid.UUID, websocket: WebSocket):
            try:
                await self.conn_manager.connect(
                    user_id, websocket, self.config.get("max_queue_size", 0)
                )
                await handle_websocket_data(user_id)
            except ServerFullException:
                pass
            finally:
                await self.conn_manager.disconnect(user_id)

        async def handle_websocket_data(user_id: uuid.UUID):
            if not self.conn_manager.check_user(user_id):
                return HTTPException(status_code=404, detail="User not found")
            last_time = time.time()
            try:
                while True:
                    if (
                        self.config.get("timeout", 0) > 0
                        and time.time() - last_time > self.config.get("timeout", 0)
                    ):
                        await self.conn_manager.send_json(
                            user_id,
                            {
                                "status": "timeout",
                                "message": "Your session has ended",
                            },
                        )
                        await self.conn_manager.disconnect(user_id)
                        return
                    # 接收消息（支持二进制和JSON两种格式）
                    data, image_data = await self.conn_manager.receive_message(user_id)
                    if not data or not isinstance(data, dict):
                        # 如果收到无效数据，继续等待
                        continue
                    logger.info(f"收到WebSocket消息: user_id={user_id}, status={data.get('status')}, image_size={len(image_data)}")
                    if data.get("status") == "next_frame":
                        if pipeline is None:
                            # Pipeline 正在重载中，暂时忽略请求或发送等待状态
                            await asyncio.sleep(0.1)
                            continue
                        info = pipeline.Info()
                        # 从data中提取参数（已经在前端格式中包含了params）
                        # 移除status字段，只保留参数
                        params_dict = {k: v for k, v in data.items() if k != "status"}
                        if not params_dict:
                            # 如果没有参数，继续等待
                            continue
                        params = pipeline.InputParams(**params_dict)
                        params = SimpleNamespace(**params.dict())
                        if info.input_mode == "image":
                            if len(image_data) == 0:
                                await self.conn_manager.send_json(
                                    user_id, {"status": "send_frame"}
                                )
                                continue
                            params.image = bytes_to_pil(image_data)
                            logger.info(f"处理图像数据: user_id={user_id}, image_size={len(image_data)}, prompt={params_dict.get('prompt', '')[:50]}")
                        await self.conn_manager.update_data(user_id, params)
                        logger.info(f"已更新数据到队列: user_id={user_id}")

            except Exception as e:
                logger.error(f"Websocket Error: {e}")
                await self.conn_manager.disconnect(user_id)

        @self.app.get("/api/queue")
        async def get_queue_size():
            queue_size = self.conn_manager.get_user_count()
            return JSONResponse({"queue_size": queue_size})

        @self.app.get("/api/stream/{user_id}")
        async def stream(user_id: uuid.UUID, request: Request):
            try:

                async def generate():
                    logger.info(f"开始图像流生成: user_id={user_id}")
                    while True:
                        last_time = time.time()
                        await self.conn_manager.send_json(
                            user_id, {"status": "send_frame"}
                        )
                        params = await self.conn_manager.get_latest_data(user_id)
                        if params is None:
                            await asyncio.sleep(0.1)  # 避免CPU占用过高
                            continue
                        if pipeline is None:
                            # Pipeline 正在重载中
                            await asyncio.sleep(0.1)
                            continue
                        logger.debug(f"开始生成图像: user_id={user_id}")
                        image = pipeline.predict(params)
                        if image is None:
                            logger.warning(f"图像生成失败: user_id={user_id}")
                            continue
                        frame = pil_to_frame(image)
                        logger.debug(f"生成图像帧: user_id={user_id}, frame_size={len(frame)}")
                        yield frame

                return StreamingResponse(
                    generate(),
                    media_type="multipart/x-mixed-replace;boundary=frame",
                    headers={"Cache-Control": "no-cache"},
                )
            except Exception as e:
                logger.error(f"Streaming Error: {e}")
                return HTTPException(status_code=404, detail="User not found")

        @self.app.get("/api/settings")
        async def settings():
            info_schema = pipeline.Info.schema()
            info = pipeline.Info()
            # page_content 已经是 HTML 格式，直接使用
            page_content = info.page_content if info.page_content else ""

            input_params = pipeline.InputParams.schema()
            return JSONResponse(
                {
                    "info": info_schema,
                    "input_params": input_params,
                    "max_queue_size": self.config.get("max_queue_size", 0),
                    "page_content": page_content,
                }
            )


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch_dtype = torch.float16

# 从配置文件读取设置
settings = get_settings()
config = {
    "max_queue_size": settings.server.max_queue_size,
    "timeout": settings.server.timeout,
    "use_safety_checker": settings.server.use_safety_checker,
    "use_tiny_vae": settings.pipeline.use_tiny_vae,
    "acceleration": settings.model.acceleration,
    "engine_dir": settings.model.engine_dir,
    "model_id": settings.model.model_id,
}

async def reload_pipeline(model_id: str, vae_id: str = None):
    """重新加载 Pipeline"""
    global pipeline, config
    
    logger.info(f"正在重新加载 Pipeline，新模型: {model_id}, VAE: {vae_id}")
    
    # 1. 标记 pipeline 为不可用，防止新请求进入
    # 保存旧引用以便清理
    old_pipeline = pipeline
    pipeline = None
    
    # 2. 清理旧资源
    if old_pipeline is not None:
        if hasattr(old_pipeline, "stream"):
            del old_pipeline.stream
        del old_pipeline
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    # 3. 更新配置
    config["model_id"] = model_id
    # 如果显式提供了 vae_id，则更新；否则保持原样或重置？
    # 假设：切换模型时，如果未指定 VAE，应该重置为 None (使用模型默认或 TinyVAE)
    # 但为了灵活性，如果 vae_id 是 None，我们可能想保留之前的？
    # 不，切换模型通常意味着之前的 VAE 可能不兼容。
    # 安全起见：如果 vae_id 传入 None，我们应该重置 config["vae_id"] 吗？
    # 目前 api/models.py 中 switch_model 传递 request.vae_id。
    # 如果前端没传，就是 None。
    # 所以这里应该允许重置。
    if vae_id is not None:
        config["vae_id"] = vae_id
    else:
        # 如果没有指定 VAE，且切换了模型，最好重置 VAE 配置，避免不兼容
        # 除非我们确定用户想保留。这里假设切换模型重置 VAE。
        if "vae_id" in config:
            del config["vae_id"]
    
    # 4. 重新初始化
    try:
        new_pipeline = Pipeline(config, device, torch_dtype)
        pipeline = new_pipeline
        logger.info("Pipeline 重新加载完成")
    except Exception as e:
        logger.error(f"Pipeline 初始化失败: {e}")
        # 尝试恢复或保持 None
        raise e

pipeline = Pipeline(config, device, torch_dtype)
app = App(config, pipeline).app
app.include_router(models.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=False,
        log_level="warning",
    )
