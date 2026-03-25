from typing import Any

from app.api.status import Status


class CustomException(Exception):
    """自定义异常基类"""

    def __init__(
            self,
            msg: str = None,
            code: int = None,
            data: Any = None,
            status: Status = Status.FAILURE,
    ):
        self.msg = msg or status.msg
        self.code = code or status.code
        self.data = data
        self.status = status

    def __str__(self) -> str:
        return f"{self.code} {self.msg}"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: ({self.code!r}, {self.msg!r})>"


class TokenInvalidError(CustomException):
    """令牌无效"""

    def __init__(self, msg: str = None):
        super().__init__(msg=msg, status=Status.TOKEN_INVALID)


class TokenExpiredError(CustomException):
    """令牌已过期"""

    def __init__(self, msg: str = None):
        super().__init__(msg=msg, status=Status.TOKEN_EXPIRED)


class TokenMissingError(CustomException):
    """缺少认证令牌"""

    def __init__(self, msg: str = None):
        super().__init__(msg=msg, status=Status.TOKEN_MISSING)


class LoginFailedError(CustomException):
    """登录失败"""

    def __init__(self, msg: str = None):
        super().__init__(msg=msg, status=Status.LOGIN_FAILED)


class AccountLockedError(CustomException):
    """账户被锁定"""

    def __init__(self, msg: str = None):
        super().__init__(msg=msg, status=Status.ACCOUNT_LOCKED)


class PermissionDeniedError(CustomException):
    """权限不足"""

    def __init__(self, msg: str = None):
        super().__init__(msg=msg, status=Status.PERMISSION_DENIED_ERROR)


class NotFoundError(CustomException):
    """资源不存在"""

    def __init__(self, msg: str = None):
        super().__init__(msg=msg, status=Status.RECORD_NOT_EXIST_ERROR)


class AlreadyExistsError(CustomException):
    """资源已存在"""

    def __init__(self, msg: str = None):
        super().__init__(msg=msg, status=Status.RECORD_EXISTS_ERROR)


class DatabaseError(CustomException):
    """数据库操作失败"""

    def __init__(self, msg: str = None):
        super().__init__(msg=msg, status=Status.DATABASE_ERROR)


class ValidationError(CustomException):
    """参数验证失败"""

    def __init__(self, msg: str = None):
        super().__init__(msg=msg, status=Status.PARAMS_ERROR)
