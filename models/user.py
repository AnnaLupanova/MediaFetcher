from pydantic import BaseModel
import datetime
from passlib.context import CryptContext
from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    manager = "manager"
    user = "user"


class User(BaseModel):
    username: str
    password_hash: str
    role: UserRole

    @classmethod
    def get_user(cls, db, username):
        if username in db:
            user_dict = db[username]
            print(f'{user_dict}')
            return User(**user_dict)





