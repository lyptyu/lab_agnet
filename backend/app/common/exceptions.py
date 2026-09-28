from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import HTTP_422_UNPROCESSABLE_ENTITY
from fastapi import HTTPException
from app.common.response import Response
from fastapi.responses import JSONResponse
from fastapi import Request


class BussinessException(Exception):
    """自定义业务异常"""

    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(message)


async def bussiness_exception_handler(request: Request,
                                      exc: BussinessException):
    return JSONResponse(status_code=200,
                        content=Response.error(
                            code=exc.code, message=exc.message).model_dump())
async def http_exception_handler(request: Request,
                                      exc: HTTPException):
    return JSONResponse(status_code=exc.status_code,
                        content=Response.error(
                            code=exc.status_code, message=exc.detail).model_dump())

async def validation_exception_handler(request: Request,
                                      exc: RequestValidationError):
    return JSONResponse(status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                        content=Response.error(
                            code=HTTP_422_UNPROCESSABLE_ENTITY, message='请求参数校验错误').model_dump())

async def global_exception_handler(request: Request,
                                      exc: Exception):
    return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                        content=Response.error(
                            code=HTTP_500_INTERNAL_SERVER_ERROR, message='服务器内部错误').model_dump())
