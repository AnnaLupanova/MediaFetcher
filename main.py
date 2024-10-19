import json
from fastapi import FastAPI, HTTPException, Depends, Query, status
import re
from settings import AppSettings
from service.redis_service import get_redis_service
from logger import logger
from service.youtube_service import YoutubeService, VideoFormat
from typing import Optional, Annotated
from fastapi.security import OAuth2PasswordRequestForm
from models.user import User, UserRole
from auth import (
    verification, oauth_scheme, create_access_token,
    verify_password,create_refresh_token,
    RoleChecker, get_current_user)
from schemas.token import Token
from schemas.user import UserCreate, UserResponse
from utils import is_valid, Source, get_user, get_role, create_user
from database import AsyncSessionLocal, engine, Base
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.integrations.starlette_client import OAuth
from fastapi.responses import RedirectResponse
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from fastapi import Request


app = FastAPI()
settings = AppSettings()
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)



config_data = {'GOOGLE_CLIENT_ID': settings.google_client_id, 'GOOGLE_CLIENT_SECRET': settings.google_client_secret}
starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


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


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await init_roles()

@app.get('/')
def public(request: Request):
    user = request.session.get('user')
    token = request.session.get('token')
    if user:
        name = user.get('name')
        return  token
    return {"detail": "Not authenticated"}


@app.get("/get-video-data/{video_id}")
async def get_data_from_youtube(video_id: str):
    """
        Retrieve stream URL by videoId.
        This endpoint fetches the streaming url for a specified YouTube video.
        Used YouTube API v3

        - Args:
            video_id (str): A valid YouTube video ID.
        - Returns:
            dict: A dictionary containing the information about video
        - Example:
            GET /get-download-link/dQw4w9WgXcQ
    """

    pattern = settings.youtube_video_id_pattern
    if not is_valid(pattern, video_id):
        raise HTTPException(status_code=400, detail=f"Video id don't match pattern={pattern}")
    res = await YoutubeService(video_id).get_video_data()
    if 'items' not in res or not res['items']:
        raise HTTPException(status_code=404, detail=f"Video with id {video_id} not found")

    return res['items'][0]

from service.rabbitmq_service import publish_message
@app.get("/get-download-link/{video_id}")
async def get_metadata(request: Request, video_id: str, redis=Depends(get_redis_service)):
    """
    Retrieve stream URL by videoId.
    This endpoint fetches the streaming url for a specified YouTube video

    - Args:
        video_id (str): A valid YouTube video ID.
    - Returns:
        url (str): The direct stream URL for downloading the video.
    - Example:
        GET /get-download-link/dQw4w9WgXcQ
    """
    user = request.session.get('user')
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    cache = await redis.get_cache(key=f"{video_id}")
    if cache:
        await publish_message(cache.decode(), "annalupanova1999@gmail.com")
        return cache.decode()

    res = await YoutubeService(video_id).fetch_video_info()
    await redis.set_cache(key=f"{video_id}", value=res.url, expire=120)
    await publish_message(res.url, "annalupanova1999@gmail.com")
    return res.url


@app.get("/get-download-link/{video_id}/{fmt_video}")
async def get_metadata_with_fmt(video_id: str, fmt_video: Annotated[str, VideoFormat],
                                redis=Depends(get_redis_service)):
    """
    Retrieve stream URL by videoId and format video.
    This endpoint fetches the streaming information for a specified YouTube video,
    including the duration, file size, title, download URL, and resolution based on
    the provided video ID and format.

    - Args:
        video_id (str): A valid YouTube video ID.
        fmt_video (str): Desired format for the video (e.g., 'mp4', 'mov').
    - Returns:
        dict: A dictionary containing the following information:
            - duration (float): The duration of the video in seconds.
            - filesize_mb (float): The size of the video file in megabytes.
            - title (str): The title of the video.
            - url (str): The direct stream URL for downloading the video.
            - resolution (str): The resolution of the video.
    - Example:
        GET /get-download-link/dQw4w9WgXcQ/mp4
    """

    cache = await redis.get_cache(key=f"{video_id}&{fmt_video}")
    if cache:
        return json.loads(cache.decode())

    res = await YoutubeService(video_id, fmt_video).fetch_video_info()
    result = {
        "duration": res._monostate.duration,
        "filesize_mb": res._filesize_mb,
        "title": res._monostate.title,
        "url": res.url,
        "resolution": res.resolution
    }
    await redis.set_cache(key=f"{video_id}&{fmt_video}", value=json.dumps(result), expire=120)
    return result


@app.get("/get-link/")
async def get_link_by_source(source: Source, video_id: str):
    service = source.source_class(video_id)
    res = await service.fetch_video_info()
    return res


@app.get("/auth/basic")
def work_with_HTTPBasic(verification=Depends(verification)):
    if verification:
        return "Hello"


@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: AsyncSession = Depends(get_db)) -> Token:
    user = await get_user(form_data.username, db)

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(data={"name": user.username, "role": user.role.name}),
                 refresh_token=create_refresh_token(data={"name": user.username, "role": user.role.name})
                 )


@app.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_user = await get_user(user.username, db)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Username already registered")

    new_user = await create_user(db, user)
    return new_user


@app.get("/auth1")
async def work_with_oauth2(token: str = Depends(oauth_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user = await get_user(token, db)
    except Exception:
        raise credentials_exception
    return user


@app.get("/auth2")
async def work_with_jwt(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]


@app.get("/auth3")
def get_data_according_role(_: Annotated[bool, Depends(RoleChecker(allowed_roles=["admin", "manager"]))]):
  return {"data": "This is important data"}


@app.get('/login/google')
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get('/auth')
async def auth(request: Request):
    try:
        access_token = await oauth.google.authorize_access_token(request)
    except Exception:
        return RedirectResponse(url='/')
    userinfo = access_token['userinfo']
    request.session['user'] = dict(userinfo)
    return RedirectResponse(url='/')


@app.get('/logout')
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')


