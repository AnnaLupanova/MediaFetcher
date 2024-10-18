import re
from enum import Enum
from service.instagram_service import InstagramService
from service.youtube_service import YoutubeService
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User, UserRole
from sqlalchemy.future import select
from schemas.user import UserCreate
from passlib.context import CryptContext
from fastapi import HTTPException, status

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


class Source(Enum):
    youtube = "youtube", YoutubeService
    instagram = "instagram", InstagramService

    def __init__(self, value, source_class):
        self._value_ = value
        self.source_class = source_class



