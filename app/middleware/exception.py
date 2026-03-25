import traceback

from fastapi.exceptions import RequestValidationError
from jose import JWTError
from jose.jwt import ExpiredSignatureError, JWTClaimsError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.exception import CustomException
from app.api.response import Response
from app.api.status import Status
from app.core.logging import logger


class ExceptionHandler:

    @staticmethod
    async def custom_exception_handler(
            request: Request,
            exc: CustomException,
    ) -> JSONResponse:
        lmsg = f'- "{request.method} {request.url.path}" {exc.code} {exc.msg}'
        logger.error(lmsg)
        return Response.failure(msg=exc.msg, code=exc.code, data=exc.data)

    @staticmethod
    async def http_exception_handler(
            request: Request,
            exc: HTTPException,
    ) -> JSONResponse:
        lmsg = f'- "{request.method} {request.url.path}" {exc.status_code} {exc.detail}'
        logger.error(lmsg)
        return Response.failure(msg=exc.detail, code=exc.status_code)

    @staticmethod
    async def validation_exception_handler(
            request: Request,
            exc: RequestValidationError,
    ) -> JSONResponse:
        errors = exc.errors()
        msg = ", ".join([
            f"'{e['loc'][-1]}' {e['msg']}"
            for e in errors
        ])
        lmsg = f'- "{request.method} {request.url.path}" {Status.PARAMS_ERROR.code} {msg}'
        logger.error(lmsg)
        return Response.failure(msg=msg, status=Status.PARAMS_ERROR)

    @staticmethod
    async def jwt_exception_handler(
            request: Request,
            exc: JWTError,
    ) -> JSONResponse:
        if isinstance(exc, ExpiredSignatureError):
            status = Status.TOKEN_EXPIRED
        elif isinstance(exc, JWTClaimsError):
            status = Status.TOKEN_INVALID
        else:
            status = Status.TOKEN_INVALID
        lmsg = f'- "{request.method} {request.url.path}" {status.code} {status.msg}'
        logger.error(lmsg)
        return Response.failure(msg=status.msg, code=status.code)

    @staticmethod
    async def database_exception_handler(
            request: Request,
            exc: SQLAlchemyError,
    ) -> JSONResponse:
        if isinstance(exc, IntegrityError):
            status = Status.DATABASE_INTEGRITY_ERROR
            msg = '数据冲突，请检查是否重复提交'
        elif isinstance(exc, OperationalError):
            status = Status.DATABASE_CONNECTION_ERROR
            msg = '数据库连接异常'
        else:
            status = Status.DATABASE_ERROR
            msg = status.msg
        lmsg = f'- "{request.method} {request.url.path}" {status.code} {msg}'
        logger.error(lmsg)
        return Response.failure(msg=msg, code=status.code)

    @staticmethod
    async def not_found_handler(
            request: Request,
            exc: HTTPException,
    ) -> JSONResponse:
        lmsg = f'- "{request.method} {request.url.path}" 404 资源不存在'
        logger.warning(lmsg)
        return Response.failure(msg='请求的资源不存在', code=Status.NOT_FOUND.code)

    @staticmethod
    async def method_not_allowed_handler(
            request: Request,
            exc: HTTPException,
    ) -> JSONResponse:
        lmsg = f'- "{request.method} {request.url.path}" 405 请求方法不允许'
        logger.warning(lmsg)
        return Response.failure(msg='请求方法不允许', code=Status.METHOD_NOT_ALLOWED.code)

    @staticmethod
    async def unhandled_exception_handler(
            request: Request,
            exc: Exception,
    ) -> JSONResponse:
        lmsg = f'- "{request.method} {request.url.path}" 500 未处理异常\n{traceback.format_exc()}'
        logger.error(lmsg)
        return Response.failure(
            msg='服务器内部错误，请稍后重试',
            code=Status.INTERNAL_SERVER_ERROR.code,
        )