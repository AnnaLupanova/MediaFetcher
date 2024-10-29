import re
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User, UserRole
from sqlalchemy.future import select
from schemas.user import UserCreate
from passlib.context import CryptContext
from fastapi import HTTPException, status
import abc
from typing import Optional, Any, Annotated
import asyncio
from concurrent.futures import ThreadPoolExecutor
from database import AsyncSessionLocal
from enum import Enum


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def init_roles():
    INIT_ROLES = [
        {"name": "admin", "is_admin": True},
        {"name": "user", "is_admin": False},
        {"name": "manager", "is_admin": True}
    ]

    async with AsyncSessionLocal() as session:
        for role in INIT_ROLES:
            existing_role = await get_role(role["name"], session)
            if not existing_role:
                new_role = UserRole(**role)
                session.add(new_role)
        await session.commit()

async def get_user(user_name: str, db: AsyncSession) -> User:
    result = await db.execute(select(User).filter(User.username == user_name))
    return result.scalars().first()


async def get_role(name: str, db: AsyncSession) -> UserRole:
    result = await db.execute(select(UserRole).filter(UserRole.name == name))
    return result.scalars().first()

async def create_user(db: AsyncSession, user: UserCreate):
    role_result = await db.execute(select(UserRole).filter(UserRole.name == user.role))
    role = role_result.scalars().first()
    if not role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role not found")

    hashed_password = pwd_context.hash(user.password)
    db_user = User(username=user.username,
                   password_hash=hashed_password,
                   email=user.email,
                   role_id=role.id)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


def is_valid(pattern: str, id: str) -> bool:
    regex = re.compile(pattern)
    results = regex.match(id)
    if not results:
        return False
    return True


class VideoFormat(Enum):
    MP4 = "mp4"
    WEBM = "webm"
    MKV = "mkv"


class BaseService(abc.ABC):
    def __init__(self, content_id: str, fmt: Annotated[str, VideoFormat] = VideoFormat.MP4.value):
        self.content_id = content_id
        self.fmt = fmt

    @abc.abstractmethod
    def get_stream(self) -> Any:
        ...

    async def fetch_video_info(self) -> Any:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, self.get_stream)

