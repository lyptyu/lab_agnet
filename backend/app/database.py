from datetime import datetime
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, DateTime
from app.config import settings

engine = create_engine(settings.DATABASE_URL)
#数据库session连接工厂
SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True,
                                    comment="主键ID",
                                    sort_order=-1)
    create_time: Mapped[datetime] = mapped_column(DateTime,
                                                  default=datetime.now,
                                                  comment="创建时间")
    update_time: Mapped[datetime] = mapped_column(DateTime,
                                                  default=datetime.now,
                                                  onupdate=datetime.now,
                                                  comment="创建时间")
