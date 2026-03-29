from typing import List
from typing import Optional
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import LargeBinary
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from uuid import UUID
from uuid import uuid4

from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(20))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[bytes] = mapped_column(LargeBinary(60))
    refresh_tokens: Mapped[Optional[List["RefreshToken"]]] = relationship(back_populates="user", cascade="all, delete-orphan")
    videos: Mapped[Optional[List["Video"]]] = relationship(back_populates="author", cascade="all, delete-orphan")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4) # jti
    issuer: Mapped[str] = mapped_column(String(128))
    last_access_jti: Mapped[UUID] = mapped_column(default=uuid4, unique=True)
    device_agent: Mapped[str] = mapped_column(String(2000))
    expiration_time: Mapped[datetime] = mapped_column(default=datetime.now)
    #valid: Mapped[bool] = mapped_column(Boolean(), default=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

class Video(Base):
    __tablename__ = "videos"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(5000))
    author_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    author: Mapped["User"] = relationship(back_populates="videos")

if True:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from os import getenv
    engine = create_engine(getenv("DATABASE_URI"))
    Session = sessionmaker(engine)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
