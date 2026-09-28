from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from fastapi import FastAPI
from app.models.user import User
from app.database import Base, engine
from app.api import api
from app.common.exceptions import (BussinessException,
                                   bussiness_exception_handler,
                                   http_exception_handler,
                                   validation_exception_handler,
                                   global_exception_handler)

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(api)
#注册自定义异常
app.add_exception_handler(BussinessException,bussiness_exception_handler)
app.add_exception_handler(HTTPException,http_exception_handler)
app.add_exception_handler(RequestValidationError,validation_exception_handler)
app.add_exception_handler(Exception,global_exception_handler)

@app.get('/')
def root():
    return {"messages": "fast api running"}
