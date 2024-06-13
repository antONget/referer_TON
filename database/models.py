from sqlalchemy import BigInteger, ForeignKey, String, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

from typing import List



engine = create_async_engine(url="sqlite+aiosqlite:///database/db.sqlite3", echo=False)


async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(200))
    referral_link: Mapped[str] = mapped_column(String(200))
    referral_users: Mapped[str] = mapped_column(String, default="")  # id_1,id_2,...
    ton_balance: Mapped[int] = mapped_column(Float, default=0.0)




async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# import asyncio

# asyncio.run(async_main())
