import datetime
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedColumn, mapped_column, relationship

load_dotenv(Path(__file__).resolve().parent / ".env")

POSTGRES_USER = os.getenv("POSTGRES_USER", "app")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "secret")
POSTGRES_DB = os.getenv("POSTGRES_DB", "app")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5431")

POSTGRES_DSN = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/"
    f"{POSTGRES_DB}"
)

engine = create_async_engine(POSTGRES_DSN)
Session = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase, AsyncAttrs):
    pass


class User(Base):
    __tablename__ = "users"

    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    email: MappedColumn[str] = mapped_column(String, unique=True, nullable=False)
    password: MappedColumn[str] = mapped_column(String, nullable=False)
    registration_time: MappedColumn[datetime.datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )

    advertisements: Mapped[list["Advertisement"]] = relationship(
        back_populates="owner"
    )

    @property
    def id_dict(self):
        return {"id": self.id}

    @property
    def dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "registration_time": int(self.registration_time.timestamp()),
        }


class Advertisement(Base):
    __tablename__ = "advertisements"

    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    title: MappedColumn[str] = mapped_column(String, nullable=False)
    description: MappedColumn[str] = mapped_column(String, nullable=False)
    created_at: MappedColumn[datetime.datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
    owner_id: MappedColumn[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )

    owner: Mapped[User] = relationship(back_populates="advertisements")

    @property
    def id_dict(self):
        return {"id": self.id}

    @property
    def dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created_at": int(self.created_at.timestamp()),
            "owner": self.owner.email,
        }


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    await engine.dispose()
