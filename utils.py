import re
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User, UserRole
from sqlalchemy.future import select
from schemas.user import UserCreate
from passlib.context import CryptContext
from fastapi import HTTPException, status
import abc
from typing import Optional, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_user(user_name: str, db: AsyncSession) -> User:
    result = await db.execute(select(User).filter(User.username == user_name))
    return result.scalars().first()


async def get_role(name: str, db: AsyncSession) -> UserRole:
    print(db)
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


class BaseService(abc.ABC):
    def __init__(self, content_id: str):
        self.content_id = content_id

    @abc.abstractmethod
    def get_stream(self) -> Any:
        ...

    async def fetch_video_info(self) -> Any:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, self.get_stream)

