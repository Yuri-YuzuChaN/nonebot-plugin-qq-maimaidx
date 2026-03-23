from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import Field, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from ...config import data_dir

db = data_dir / "user.db"

metadata_user = MetaData()


class UserBase(SQLModel):
    
    __abstract__ = True
    metadata = metadata_user


class User(UserBase, table=True):
    
    UserID: str = Field(primary_key=True)
    QQID: int
    Mode: int = Field(0)


engine = create_async_engine(f"sqlite+aiosqlite:///{str(db)}", echo=False)


async def create_database():
    async with engine.begin() as connect:
        await connect.run_sync(metadata_user.create_all)


async def get_user(user_id: str) -> User | None:
    async with AsyncSession(engine) as session:
        statement = select(User).where(User.UserID == user_id)
        result = await session.exec(statement)
        return result.first()
    

async def insert_user(user_id: str, qqid: int) -> User:
    async with AsyncSession(engine) as session:
        user = User(UserID=user_id, QQID=qqid)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def update_user(user_id: str, qqid: int) -> User | None:
    async with AsyncSession(engine) as session:
        statement = select(User).where(User.UserID == user_id)
        result = await session.exec(statement)
        if user := result.first():
            user.QQID = qqid
            await session.commit()
            await session.refresh(user)
        return user


async def delete_user(user_id: str) -> bool:
    async with AsyncSession(engine) as session:
        statement = select(User).where(User.UserID == user_id)
        result = await session.exec(statement)
        if user := result.first():
            await session.delete(user)
            await session.commit()
            return True
        return False