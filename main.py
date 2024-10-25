import json
from fastapi import FastAPI, HTTPException, Depends, Query, status, Response
from settings import AppSettings
from fastapi.responses import JSONResponse
from service.redis_service import get_redis_service
from service.youtube_service import YoutubeService, VideoFormat
from service.instagram_service import InstagramService
from typing import Optional, Annotated
from fastapi.security import OAuth2PasswordRequestForm
from models.user import User, UserRole
from auth import (
    create_access_token,
    verify_password,create_refresh_token,
    get_current_user)
from schemas.token import Token
from schemas.user import UserCreate, UserResponse
from utils import init_roles, get_user, get_role, create_user
from database import AsyncSessionLocal, engine, Base
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.integrations.starlette_client import OAuth
from fastapi.responses import RedirectResponse
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from fastapi import Request
from celery_worker import send_email
from prometheus_fastapi_instrumentator import Instrumentator
from logger import get_logger
from enum import Enum
from service.rabbitmq_service import publish_message


app = FastAPI()
settings = AppSettings()
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

logger = get_logger('api_logger.log')
Instrumentator().instrument(app).expose(app)


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


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await init_roles()



@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"request: {request.method} {request.url}")
    response: Response = await call_next(request)
    if isinstance(response, JSONResponse):
        response_data = await response.json()
        logger.info(f"response: {response.status_code} for {request.method} {response_data}")
    else:
        logger.info(f"response: {response.status_code} for {request.method}")
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error for {request.method} {request.url}: {exc}")

@app.get('/')
def public(request: Request):
    user = request.session.get('user')
    if user:
        name = user.get('name')
        return name
    return {"detail": "Not authenticated"}


class Source(Enum):
    youtube = "youtube", YoutubeService
    instagram = "instagram", InstagramService

    def __init__(self, value, source_class):
        self._value_ = value
        self.source_class = source_class


@app.get("/get-download-link/")
async def get_metadata(request: Request, video_id: str, fmt: str,
                       source: Source = Source.youtube.value,
                       redis=Depends(get_redis_service)):
    """
    Sends stream url by source, video ID and video format to user email.
    This endpoint fetches the streaming url for a specified Source video

    - Args:
        video_id (str): A valid video ID.
        source (str): youtube or instagram
        fmt (str): Desired format for the video (e.g., 'mp4', 'mov').

    - Example:
        GET /get-download-link/?source=youtube&video_id=G2-2l9ZLftQ&fmt=mp4
    """

    user = request.session.get('user')
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    cache = await redis.get_cache(key=f"{source}${video_id}${fmt}")
    if cache:
        await publish_message(cache.decode(), user["email"])
        return {"detail": "Link for download video was sent by email."}

    service = source.source_class(video_id, fmt)
    res = await service.fetch_video_info()
    await redis.set_cache(key=f"{source}${video_id}${fmt}", value=res.url, expire=120)
    await publish_message(res.url,  user["email"])
    return {"detail": "Link for download video was sent by email."}


@app.get("/get-metadata/")
async def get_metadata(user: Annotated[User, Depends(get_current_user)],
                       video_id: str, fmt: str,
                       source: Source = Source.youtube.value,
                       redis=Depends(get_redis_service),
                       ):
    """
    Sends stream metadata by source, video ID and video format to user email.

    - Args:
        video_id (str): A valid video ID.
        source (str): youtube or instagram
        fmt (str): Desired format for the video (e.g., 'mp4', 'mov').
    - Example:
        GET /get-metadata/?source=youtube&video_id=G2-2l9ZLftQ&fmt=mp4
    """
    cache = await redis.get_cache(key=f"{source}${video_id}${fmt}")
    if cache:
        result = json.dumps(cache.decode())
        send_email.delay(user.email, "Video metadata", result)
        return {"detail": "Video metadata was sent by email."}

    service = source.source_class(video_id, fmt)
    res = await service.fetch_video_info()
    await redis.set_cache(key=f"{source}${video_id}${fmt}", value=json.dumps(res), expire=120)
    send_email.delay(user.email, "Video metadata", res)
    return {"detail": "Video metadata was sent by email."}


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


