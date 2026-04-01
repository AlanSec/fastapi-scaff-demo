import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

from app import (
    router,
    middleware,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("应用启动中...")

    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    os.makedirs(settings.GALLERY_PATH, exist_ok=True)

    yield

    logger.info("应用关闭中...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="FastAPI Scaff Demo",
    version="0.1.0",
    lifespan=lifespan,
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

router.register_routers(app)
middleware.register_middlewares(app)

app.mount("/media", StaticFiles(directory=settings.media_root_path), name="media")


@app.get("/")
async def root():
    return {
        "message": "欢迎使用FastAPI Scaff Demo",
        "docs_url": "/docs",
        "version": "0.1.0",
    }
