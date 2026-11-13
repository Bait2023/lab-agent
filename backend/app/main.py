import asyncio
from contextlib import asynccontextmanager
import traceback

from fastapi import FastAPI, HTTPException
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from app.common.exceptions import global_exception_handler
from app.config import UPLOAD_DIR
from app.models.user import User
from app.models.lab import Lab
from app.models.equipment import Equipment
from app.models.reservation import Reservation
from app.database import engine, Base
from app.api import api
from starlette.middleware.cors import CORSMiddleware
from app.common.exceptions import (
    BusinessException,
    bussiness_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    global_exception_handler,
)
from app.services import kb_service, reservation_service

Base.metadata.create_all(bind=engine)  # 自动创建数据库和数据库表


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await asyncio.to_thread(kb_service.warmup)
    except Exception:
        traceback.print_exc()
    task = asyncio.create_task(
        reservation_service.run_expire_scan()
    )  # 启动项目开启异步的扫描任务
    yield
    try:
        task.cancel()  # 关闭项目 同时取消异步任务
    finally:
        task.cancel()
        await asyncio.gather(
            task, return_exceptions=True
        )  # 取消任务不再把CancelError抛给lifespan


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许的前端源
    allow_credentials=True,  # 允许前端携带Authorization token
    allow_methods=["*"],  # 允许所有请求方法LGET PUT DELETE OPTIONS
    allow_headers=["*"],  # 允许所有请求头
)

app.include_router(api)

# 注册异常处理器
app.add_exception_handler(BusinessException, bussiness_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
# 全局异常兜底，放在最后注册
app.add_exception_handler(Exception, global_exception_handler)

# 挂载静态的文件目录 http:127.0.0.1:8000/uploads/xxx.jpg
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/")
def root():
    return {"message": "Hello, World!"}
