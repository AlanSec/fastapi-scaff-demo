"""RateLimiter 接口和实现"""
from abc import ABC, abstractmethod
from typing import Optional


class RateLimiter(ABC):
    """速率限制器接口"""
    
    @abstractmethod
    async def check_rate_limit(self, key: str, limit: int, window_seconds: int) -> bool:
        """检查是否超过速率限制"""
        pass
    
    @abstractmethod
    async def get_remaining(self, key: str, limit: int, window_seconds: int) -> int:
        """获取剩余请求次数"""
        pass
    
    @abstractmethod
    async def reset(self, key: str) -> None:
        """重置速率限制"""
        pass


class InMemoryRateLimiter(RateLimiter):
    """基于内存的速率限制器实现"""
    
    def __init__(self):
        self._requests: dict[str, list[float]] = {}
    
    async def check_rate_limit(self, key: str, limit: int, window_seconds: int) -> bool:
        """检查是否超过速率限制"""
        import time
        now = time.time()
        window_start = now - window_seconds
        
        if key not in self._requests:
            self._requests[key] = []
        
        self._requests[key] = [t for t in self._requests[key] if t > window_start]
        
        if len(self._requests[key]) >= limit:
            return False
        
        self._requests[key].append(now)
        return True
    
    async def get_remaining(self, key: str, limit: int, window_seconds: int) -> int:
        """获取剩余请求次数"""
        import time
        now = time.time()
        window_start = now - window_seconds
        
        if key not in self._requests:
            return limit
        
        self._requests[key] = [t for t in self._requests[key] if t > window_start]
        return max(0, limit - len(self._requests[key]))
    
    async def reset(self, key: str) -> None:
        """重置速率限制"""
        self._requests.pop(key, None)