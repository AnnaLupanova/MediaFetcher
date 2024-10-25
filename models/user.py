from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from database import Base
from sqlalchemy.orm import relationship
import datetime
from passlib.context import CryptContext
from enum import Enum


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(16))
    password_hash = Column(String(128))
    email = Column(String(128))
    role_id = Column(Integer, ForeignKey("user_roles.id"))
    role = relationship('UserRole', back_populates="users", lazy="selectin")

class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True)
    name = Column(String(16))
    is_admin = Column(Boolean, default=False)
    users = relationship('User', back_populates='role')


