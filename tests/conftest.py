"""全局 pytest 配置。

注意：这里只放真正跨测试模块共享的配置/fixture。
mock 类 fixture 由各测试类自行定义（类作用域优先），全局重复定义是死代码。
"""

pytest_plugins = ("pytest_asyncio",)
