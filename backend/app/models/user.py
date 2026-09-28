from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'comment': '用户信息表'}

    username: Mapped[str] = mapped_column(String(20), comment="用户名", nullable= False)
    password: Mapped[str] = mapped_column(String(255), comment="密码", nullable= False)
    name: Mapped[str] = mapped_column(String(20), comment="名称", nullable= False)
    role: Mapped[str] = mapped_column(String(20), comment="角色：studeng-学生，admin-管理员", nullable= False)
    email: Mapped[str | None] = mapped_column(String(20), comment="邮箱")
    phone: Mapped[str | None] = mapped_column(String(20), comment="手机号")
    avatar: Mapped[str | None] = mapped_column(String(20), comment="头像")
    status:  Mapped[int] = mapped_column(default = 1, comment="状态：0-禁用，1-启用")

    