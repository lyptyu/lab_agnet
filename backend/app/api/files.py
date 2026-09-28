from app.schemas.file import FileResponse
from app.common.response import Response
from app.config import UPLOAD_DIR
import uuid
import time
from app.config import MAX_FILE_SIZE
from app.config import ALLOWED_EXTENSIONS
from pathlib import Path
from app.common.exceptions import BussinessException
from fastapi import File, UploadFile
from fastapi.routing import APIRouter
import os
import shutil

router = APIRouter(prefix="/files", tags=['文件管理'])


@router.post('/upload')
def upload(file: UploadFile = File(...)):
    """文件上传接口"""
    if not file.filename:
        raise BussinessException(message="文件名不能为空")
    #原始文件名
    original_name = os.path.basename(file.filename)
    #文件后缀 .jpg
    ext = Path(original_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise BussinessException(message=f"不支持的文件格式: {ext}不支持")

    #校验文件大小
    if file.size and file.size > MAX_FILE_SIZE:
        raise BussinessException(message=f"文件大小不能超过{MAX_FILE_SIZE // 1024}MB")

    #保存文件
    #设置唯一的文件名称
    disk_name = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}{ext}"
    save_path = UPLOAD_DIR / disk_name
    # 流失写文件
    with open(save_path, 'wb') as f:
        shutil.copyfileobj(file.file, f)

    # return Response.success(data={
    #     "original_name": original_name,
    #     "disk_name": disk_name,
    #     "size":file.size,
    #     "url": f'/uploads/{disk_name}'
    # })
    return Response.success(data=FileResponse(original_name=original_name,
                                              disk_name=disk_name,
                                              size=file.size,
                                              url=f'/uploads/{disk_name}'))
