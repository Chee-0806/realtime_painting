"""FastAPI 应用主入口

集成所有组件，提供完整的 StreamDiffusion 后端服务。
"""

import asyncio
import logging
from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config.settings import get_settings
from app.core.dependencies import DependencyChecker
from app.core.session import get_session_manager
from app.core.engine import StreamDiffusionEngine
from app.pipelines.base import PipelineFactory
from app.api import http
from app.api.websocket import WebSocketHandler
from app.api.stream import ImageStreamHandler
from app.utils.logger import setup_logging
from app.utils.performance import PerformanceOptimizer

logger = logging.getLogger(__name__)

# 全局变量
pipeline = None
session_manager = None
websocket_handler = None
image_stream_handler = None
performance_optimizer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    启动时：
    - 加载配置
    - 检查依赖
    - 初始化引擎
    - 执行 warmup
    
    关闭时：
    - 清理资源
    """
    global pipeline, session_manager, websocket_handler, image_stream_handler, performance_optimizer
    
    # 启动事件
    logger.info("=" * 60)
    logger.info("StreamDiffusion Backend 启动中...")
    logger.info("=" * 60)
    
    try:
        # 1. 加载配置
        logger.info("加载配置...")
        settings = get_settings()
        
        # 验证配置
        warnings = settings.validate_config()
        for warning in warnings:
            logger.warning(warning)
        
        logger.info(f"配置加载完成: {settings.model.model_id}")
        logger.info(f"加速方式: {settings.model.acceleration}")
        logger.info(f"Pipeline: {settings.pipeline.name} ({settings.pipeline.mode} 模式)")
        
        # 2. 检查依赖
        logger.info("检查依赖兼容性...")
        dependency_checker = DependencyChecker()
        
        is_valid, errors = dependency_checker.check_all(settings.model.acceleration)
        
        if not is_valid:
            logger.error("依赖检查失败:")
            for error in errors:
                logger.error(f"  - {error}")
            
            # 获取推荐版本
            recommended = dependency_checker.get_recommended_versions(settings.model.acceleration)
            logger.info("推荐版本:")
            for key, value in recommended.items():
                logger.info(f"  - {key}: {value}")
            
            raise RuntimeError("依赖检查失败，请安装正确的依赖版本")
        
        logger.info("依赖检查通过")
        
        # 3. 初始化会话管理器
        logger.info("初始化会话管理器...")
        session_manager = get_session_manager(timeout=settings.server.timeout)
        
        # 4. 初始化 Pipeline
        logger.info(f"初始化 Pipeline: {settings.pipeline.name}...")
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        dtype = torch.float16 if device.type == "cuda" else torch.float32
        
        logger.info(f"使用设备: {device}, 数据类型: {dtype}")
        
        config = settings.to_dict()
        
        pipeline = PipelineFactory.create_pipeline(
            pipeline_name=settings.pipeline.name,
            config=config,
            device=device,
            dtype=dtype
        )
        
        logger.info("Pipeline 初始化成功")
        
        # 5. 执行 warmup
        if settings.pipeline.warmup > 0:
            logger.info(f"执行 warmup ({settings.pipeline.warmup} 步)...")
            pipeline.prepare(prompt="warmup")
            logger.info("Warmup 完成")
        
        # 6. 初始化 API 处理器
        logger.info("初始化 API 处理器...")
        websocket_handler = WebSocketHandler(session_manager)
        image_stream_handler = ImageStreamHandler(session_manager)
        
        # 设置 HTTP API 依赖
        http.set_dependencies(settings, session_manager)
        
        # 7. 初始化性能优化器
        logger.info("初始化性能优化器...")
        performance_optimizer = PerformanceOptimizer(
            enable_similar_filter=settings.performance.enable_similar_image_filter,
            similar_threshold=settings.performance.similar_image_filter_threshold,
            max_skip_frame=settings.performance.similar_image_filter_max_skip_frame
        )
        
        # 8. 记录 GPU 内存信息
        PerformanceOptimizer.log_gpu_memory_info()
        
        logger.info("=" * 60)
        logger.info("StreamDiffusion Backend 启动完成!")
        logger.info(f"服务器地址: http://{settings.server.host}:{settings.server.port}")
        logger.info("=" * 60)
        
        yield
        
    except Exception as e:
        logger.error(f"启动失败: {e}")
        raise
    
    # 关闭事件
    logger.info("=" * 60)
    logger.info("StreamDiffusion Backend 关闭中...")
    logger.info("=" * 60)
    
    try:
        # 清理会话
        if session_manager:
            logger.info("清理所有会话...")
            sessions = await session_manager.get_all_sessions()
            for session in sessions:
                await session_manager.cleanup_session(session.user_id)
        
        # 清理 Pipeline
        if pipeline and hasattr(pipeline, 'cleanup'):
            logger.info("清理 Pipeline...")
            pipeline.cleanup()
        
        # 清理 GPU 内存
        logger.info("清理 GPU 内存...")
        PerformanceOptimizer.cleanup_gpu_memory()
        
        # 记录性能统计
        if performance_optimizer:
            performance_optimizer.log_statistics()
        
        logger.info("=" * 60)
        logger.info("StreamDiffusion Backend 已关闭")
        logger.info("=" * 60)
    
    except Exception as e:
        logger.error(f"关闭时出错: {e}")


# 创建 FastAPI 应用
app = FastAPI(
    title="StreamDiffusion Backend",
    description="实时图像生成后端服务，基于 StreamDiffusion",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allow_origins,
    allow_credentials=settings.cors.allow_credentials,
    allow_methods=settings.cors.allow_methods,
    allow_headers=settings.cors.allow_headers,
)

# 注册 HTTP 路由
app.include_router(http.router)


@app.websocket("/api/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket 端点
    
    处理实时图像生成的 WebSocket 连接，并执行完整的生成循环。
    
    Args:
        websocket: WebSocket 连接
        user_id: 用户 ID
    """
    if websocket_handler is None or pipeline is None:
        await websocket.close(code=1011, reason="Server not ready")
        return
    
    # 获取模式（从查询参数）
    mode = websocket.query_params.get("mode", settings.pipeline.mode)
    
    # 创建生成任务
    generation_task = asyncio.create_task(
        generation_loop(user_id, mode)
    )
    
    try:
        # 处理 WebSocket 连接（接收消息）
        await websocket_handler.handle_connection(websocket, user_id, mode)
    finally:
        # 取消生成任务
        generation_task.cancel()
        try:
            await generation_task
        except asyncio.CancelledError:
            pass


async def generation_loop(user_id: str, mode: str):
    """
    图像生成循环
    
    持续从会话获取参数和图像，生成新图像并更新会话。
    
    Args:
        user_id: 用户 ID
        mode: 输入模式
    """
    logger.info(f"启动生成循环: {user_id}")
    
    try:
        while True:
            # 获取会话
            session = await session_manager.get_session(user_id)
            
            if session is None or not session.is_active:
                logger.info(f"会话不活跃，停止生成: {user_id}")
                break
            
            # 检查是否有参数
            if not session.parameters:
                await asyncio.sleep(0.1)
                continue
            
            try:
                # 准备参数
                params_dict = session.parameters.copy()
                
                # 根据模式生成图像
                if mode == "image":
                    # img2img 模式：需要输入图像
                    if session.latest_image is None:
                        await asyncio.sleep(0.1)
                        continue
                    
                    # 创建 InputParams
                    from app.pipelines.img2img import Pipeline as Img2ImgPipeline
                    params = Img2ImgPipeline.InputParams(**params_dict)
                    
                    # 生成图像
                    output_image = pipeline.predict(params, session.latest_image)
                
                else:
                    # txt2img 模式：不需要输入图像
                    from app.pipelines.txt2img import Pipeline as Txt2ImgPipeline
                    params = Txt2ImgPipeline.InputParams(**params_dict)
                    
                    # 生成图像
                    output_image = pipeline.predict(params)
                
                # 检查是否应该跳过（相似图像过滤）
                if performance_optimizer and performance_optimizer.should_skip_frame(output_image):
                    continue
                
                # 更新会话图像
                await session_manager.update_image(user_id, output_image)
                
                logger.debug(f"生成图像完成: {user_id}")
            
            except Exception as e:
                logger.error(f"生成图像失败: {e}")
                await asyncio.sleep(0.5)
                continue
            
            # 短暂等待以避免 CPU 占用过高
            await asyncio.sleep(0.01)
    
    except asyncio.CancelledError:
        logger.info(f"生成循环已取消: {user_id}")
    
    except Exception as e:
        logger.error(f"生成循环错误: {e}")
    
    finally:
        logger.info(f"生成循环已结束: {user_id}")


@app.get("/api/stream/{user_id}")
async def image_stream_endpoint(user_id: str, quality: int = 85, max_fps: int = 30):
    """
    图像流端点
    
    通过 HTTP multipart/x-mixed-replace 协议推送实时生成的图像。
    
    Args:
        user_id: 用户 ID
        quality: JPEG 质量（1-100）
        max_fps: 最大帧率
        
    Returns:
        StreamingResponse
    """
    if image_stream_handler is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Server not ready"}
        )
    
    return await image_stream_handler.stream_images(user_id, quality, max_fps)


@app.get("/")
async def root():
    """根端点"""
    return {
        "name": "StreamDiffusion Backend",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "websocket": "/api/ws/{user_id}",
            "stream": "/api/stream/{user_id}",
            "settings": "/api/settings",
            "queue": "/api/queue",
            "health": "/api/health"
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    
    # 配置日志
    setup_logging(
        level=settings.logging.level,
        format=settings.logging.format
    )
    
    # 运行服务器
    uvicorn.run(
        "app.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=False,
        log_level=settings.logging.level.lower()
    )
