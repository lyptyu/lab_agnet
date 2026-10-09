from app.services import kb_service
import traceback
from traceback import print_exc
from fastapi.concurrency import asynccontextmanager
from app.services import reservation_service
import asyncio
from app.config import UPLOAD_DIR
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from fastapi import FastAPI
from app.models.user import User
from app.models.lab import Lab
from app.models.equipment import Equipment
from app.models.reservation import Reservation
from app.database import Base, engine
from app.api import api
from app.common.exceptions import (BussinessException,
                                   bussiness_exception_handler,
                                   http_exception_handler,
                                   validation_exception_handler,
                                   global_exception_handler)
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await asyncio.to_thread(kb_service.warmup)
    except Exception:
        traceback.print_exc()
    task = asyncio.create_task(reservation_service.run_exire_scan())
    try:
        yield
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)


app = FastAPI(lifespan=lifespan)
origins = [
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许的前端源，不要直接写 ["*"]
    allow_credentials=True,  # ✅ 关键：允许前端携带 Authorization token
    allow_methods=["*"],  # 允许所有请求方法 GET POST PUT DELETE OPTIONS
    allow_headers=["*"],  # 允许所有请求头（包含Authorization）
)
app.include_router(api)
#注册自定义异常
app.add_exception_handler(BussinessException, bussiness_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

#挂载静态文件目录
app.mount('/uploads', StaticFiles(directory=UPLOAD_DIR), name='uploads')


@app.get('/')
def root():
    return {"messages": "fast api running"}
