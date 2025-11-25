from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import logging
import asyncio
import mimetypes
import torch

from app.config import get_config, Config
from app.api import models
from app.api import realtime
from app.api import canvas
from app.api import controlnet
from app.services.runtime import (
    setup_session_services,
    list_services,
)
from app.services.resource_monitor import (
    start_resource_monitoring,
    stop_resource_monitoring,
    managed_resource_cleanup,
)

# fix mime error on windows
mimetypes.add_type("application/javascript", ".js")

# 从配置加载日志级别
config = get_config()
log_level = getattr(logging, config.log_level.upper(), logging.INFO)
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI()

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch_dtype = torch.float16

setup_session_services(config, device, torch_dtype)

# 注册路由
app.include_router(models.router)
app.include_router(canvas.router)
app.include_router(realtime.router)
app.include_router(controlnet.router)


@app.on_event("startup")
async def startup_event():
    """在应用启动时准备服务，但不立即加载模型（懒加载模式）。"""
    logger.info("应用启动完成 - 服务将以懒加载模式初始化模型")

    # 启动资源监控
    try:
        monitor = start_resource_monitoring(check_interval=30, auto_cleanup=True)
        logger.info("资源监控已启动")
    except Exception as e:
        logger.error(f"启动资源监控失败: {e}")

    # 不在启动时加载模型，而是在首次使用时加载


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时断开连接并释放资源。"""
    logger.info("开始应用关闭，清理所有服务资源...")

    try:
        # 使用资源管理的上下文管理器
        with managed_resource_cleanup():
            # 获取所有服务
            services = list_services()
            logger.info(f"发现 {len(services)} 个服务需要清理")

            # 并行清理所有服务
            shutdown_tasks = [svc.shutdown() for svc in services]
            results = await asyncio.gather(*shutdown_tasks, return_exceptions=True)

            # 检查清理结果
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"服务 {services[i]._name} 清理失败: {result}")
                else:
                    logger.info(f"服务 {services[i]._name} 清理成功")

        # 停止资源监控
        try:
            stop_resource_monitoring()
            logger.info("资源监控已停止")
        except Exception as e:
            logger.error(f"停止资源监控失败: {e}")

        # 最终GPU内存清理
        import gc
        if torch.cuda.is_available():
            logger.info("执行最终GPU内存清理...")
            for i in range(5):
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                gc.collect()

            final_allocated = torch.cuda.memory_allocated() / 1024**3
            final_reserved = torch.cuda.memory_reserved() / 1024**3
            logger.info(f"最终GPU内存状态: 已分配 {final_allocated:.2f}GB, 已保留 {final_reserved:.2f}GB")

        logger.info("应用关闭和资源清理完成")

    except Exception as e:
        logger.error(f"应用关闭过程中发生错误: {e}")
        import traceback
        logger.error(f"关闭错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=False,
        log_level="warning",
    )
