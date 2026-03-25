"""
FastAPI 路由自动注册模块

功能：自动扫描指定目录下的路由模块并注册到FastAPI应用中
特点：
1. 支持递归扫描子目录
2. 支持自定义路由前缀和标签
3. 支持模块激活控制
4. 自动处理路径格式
"""

import importlib
import sys
from pathlib import Path

from fastapi import FastAPI
from loguru import logger

from app import APP_DIR  # 导入应用根目录

# 默认API模块目录和基础导入路径
_API_MOD_DIR = APP_DIR.joinpath("api")  # API模块所在目录
_API_MOD_BASE = "app.api"  # API模块的基础导入路径


def register_routers(
        app: FastAPI,
        mod_dir: Path = _API_MOD_DIR,
        mod_base: str = _API_MOD_BASE,
        prefix: str = "",
        obj_suffix: str = "_router",
        depth: int = 0,
        max_depth: int = 2
):
    """
    自动注册路由到FastAPI应用

    路由模块规范：
    - 模块命名：不以'__'开头
    - 路由对象命名：{模块名称}{路由对象后缀} (默认后缀为'_router')
    - 可选模块变量：
        _prefix: 自定义路由前缀
        _tag: 自定义OpenAPI标签
        _active: 控制是否激活该模块(默认为True)

    :param app: FastAPI应用实例
    :param mod_dir: 要扫描的模块目录(Path对象)
    :param mod_base: 模块的基础导入路径
    :param prefix: URL路径前缀
    :param obj_suffix: 路由对象的后缀名
    :param depth: 当前递归深度(内部使用)
    :param max_depth: 最大递归深度(默认2层)
    """
    if depth > max_depth:
        return
    for item in mod_dir.iterdir():
        if item.name.startswith("__") or item.name == "__pycache__":
            continue
        if item.is_dir():
            new_mod_dir = item
            new_mod_base = f"{mod_base}.{item.name}"
            new_prefix = prefix
            try:
                mod = importlib.import_module(new_mod_base)
                _prefix = getattr(mod, "_prefix", None)
                if _prefix:
                    new_prefix = f"{new_prefix}/{_prefix}"
            except ImportError as e:
                logger.error(f"Register router failed to import module: {new_mod_base}, error: {str(e)}")
                continue
            register_routers(
                app=app,
                mod_dir=new_mod_dir,
                mod_base=new_mod_base,
                prefix=new_prefix,
                obj_suffix=obj_suffix,
                depth=depth + 1,
                max_depth=max_depth
            )
        elif item.is_file() and item.suffix == ".py" and depth > 0:
            mod_name = item.stem
            final_mod = f"{mod_base}.{mod_name}"
            try:
                mod = importlib.import_module(final_mod)
                if not getattr(mod, "_active", True):
                    logger.info(f"Register router skipping inactive module: {final_mod}")
                    sys.modules.pop(final_mod)
                    continue
                router_name = f"{mod_name}{obj_suffix}"
                if not hasattr(mod, router_name):
                    logger.warning(f"Router {router_name} not found in module {final_mod}")
                    continue
                router = getattr(mod, router_name)
                tag = getattr(mod, "_tag", None)
                if not tag:
                    tag = item.parent.stem if depth > 1 else mod_name
                app.include_router(
                    router=router,
                    prefix=prefix.replace("//", "/").rstrip("/"),
                    tags=[tag]
                )
            except ImportError as e:
                logger.error(f"Register router failed to import module: {final_mod}, error: {str(e)}")
                continue