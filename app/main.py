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
                    data = await self.conn_manager.receive_json(user_id)
                    if data.get("status") == "next_frame":
                        info = pipeline.Info()
                        params = await self.conn_manager.receive_json(user_id)
                        params = pipeline.InputParams(**params)
                        params = SimpleNamespace(**params.dict())
                        if info.input_mode == "image":
                            image_data = await self.conn_manager.receive_bytes(user_id)
                            if len(image_data) == 0:
                                await self.conn_manager.send_json(
                                    user_id, {"status": "send_frame"}
                                )
                                continue
                            params.image = bytes_to_pil(image_data)
                        await self.conn_manager.update_data(user_id, params)

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
                    while True:
                        last_time = time.time()
                        await self.conn_manager.send_json(
                            user_id, {"status": "send_frame"}
                        )
                        params = await self.conn_manager.get_latest_data(user_id)
                        if params is None:
                            continue
                        image = pipeline.predict(params)
                        if image is None:
                            continue
                        frame = pil_to_frame(image)
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
}

pipeline = Pipeline(config, device, torch_dtype)
app = App(config, pipeline).app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=False,
        log_level="warning",
    )
