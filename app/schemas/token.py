from pydantic import BaseModel, Field


class Token(BaseModel):
    """令牌模式"""

    access_token: str
    refresh_token: str
    token_type: str


class TokenPayload(BaseModel):
    """令牌载荷模式"""

    sub: str | None = None


class LoginRequest(BaseModel):
    """登录请求模型"""

    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""

    refresh_token: str = Field(..., description="刷新令牌")
