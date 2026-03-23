from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import Field, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from ...config import data_dir
from ..clients.lxns.models.oauth import OAuth2Token

db = data_dir / "lxns_token.db"

metadata_lxns = MetaData()


class UserBase(SQLModel):
    
    __abstract__ = True
    metadata = metadata_lxns


class QQUser(UserBase, table=True):
    
    ID: int = Field(default=None, primary_key=True, index=True, exclude=True)
    qqid: int
    access_token: str
    refresh_token: str


engine = create_async_engine(f"sqlite+aiosqlite:///{str(db)}", echo=False)


async def create_database():
    async with engine.begin() as connect:
        await connect.run_sync(metadata_lxns.create_all)


async def get_user(qqid: int) -> QQUser | None:
    async with AsyncSession(engine) as session:
        statement = select(QQUser).where(QQUser.qqid == qqid)
        result = await session.exec(statement)
        return result.first()


async def insert_user_and_token(qqid: int, token: OAuth2Token) -> QQUser:
    async with AsyncSession(engine) as session:
        user = QQUser(
            qqid=qqid, 
            access_token=token.access_token, 
            refresh_token=token.refresh_token
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def update_token(qqid: int, token: OAuth2Token) -> QQUser:
    async with AsyncSession(engine) as session:
        statement = select(QQUser).where(QQUser.qqid == qqid)
        result = await session.exec(statement)
        user = result.first()
        if not user:
            raise
        user.access_token = token.access_token
        user.refresh_token = token.refresh_token
        await session.commit()
        await session.refresh(user)
    return user