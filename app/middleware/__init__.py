from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from jose import JWTError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

from app.api.exception import CustomException
from app.middleware.cors import Cors
from app.middleware.exception import ExceptionHandler
from app.middleware.request_logger import RequestLoggerMiddleware
from app.middleware.response import ResponseWrapperMiddleware


def register_middlewares(app: FastAPI):
    app.add_middleware(RequestLoggerMiddleware)
    app.add_middleware(ResponseWrapperMiddleware)

    app.add_middleware(
        middleware_class=Cors.middleware_class,
        allow_origins=Cors.allow_origins,
        allow_credentials=Cors.allow_credentials,
        allow_methods=Cors.allow_methods,
        allow_headers=Cors.allow_headers,
    )

    app.add_exception_handler(CustomException, ExceptionHandler.custom_exception_handler)  # type: ignore
    app.add_exception_handler(RequestValidationError, ExceptionHandler.validation_exception_handler)  # type: ignore
    app.add_exception_handler(JWTError, ExceptionHandler.jwt_exception_handler)  # type: ignore
    app.add_exception_handler(SQLAlchemyError, ExceptionHandler.database_exception_handler)  # type: ignore
    app.add_exception_handler(HTTPException, ExceptionHandler.http_exception_handler)  # type: ignore
    app.add_exception_handler(Exception, ExceptionHandler.unhandled_exception_handler)  # type: ignore
