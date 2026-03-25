import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
# from app.services.scheduler import task_scheduler

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

from app import (
    router,
    middleware,
)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("应用启动中...")

    # 确保媒体目录存在
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    os.makedirs(settings.GALLERY_PATH, exist_ok=True)

    # 启动任务调度器
    yield

    # 关闭时执行
    logger.info("应用关闭中...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="FastAPI Scaff Demo",
    version="0.1.0",
    lifespan=lifespan,
)

# 设置CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# 注册应用路由和中间件
router.register_routers(app)          # 注册所有API路由
middleware.register_middlewares(app)  # 注册所有中间件


# 挂载静态文件
app.mount("/media", StaticFiles(directory=settings.media_root_path), name="media")


@app.get("/")
async def root():
    """API根路径，返回欢迎信息"""
    return {
        "message": "欢迎使用FastAPI Scaff Demo",
        "docs_url": "/docs",
        "version": "0.1.0",
    }
