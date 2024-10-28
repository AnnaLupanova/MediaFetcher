import json
from fastapi.testclient import TestClient
from main import app, get_metadata, get_redis_service
import pytest
from starlette.requests import Request
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def mock_redis_service():
    with patch("service.redis_service.RedisService", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def set_dependencies(mock_redis_service):
    app.dependency_overrides[get_redis_service] = lambda: mock_redis_service
    yield
    app.dependency_overrides.pop(get_redis_service, None)


@pytest.fixture
def mock_publish_message():
    with patch('main.publish_message', new_callable=AsyncMock) as publish:
        yield publish


@pytest.fixture
def mock_source():
    with patch('main.Source') as service:
        yield service

@pytest.fixture
def mock_rabbit_connection():
    with patch('main.aio_pika.connect_robust', return_value=AsyncMock()) as conn:
        yield conn



@pytest.mark.asyncio
async def test_get_metadata_user_not_authenticated(client, mock_redis_service):
    response = client.get("/get-download-link/?source=youtube&video_id=G2-2l9ZLftQ&fmt=mp4")
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid authentication credentials"}


@pytest.mark.asyncio
async def test_get_link_user_authenticated(client, set_dependencies,mock_publish_message, mock_redis_service):

    with patch.object(Request, "session", {"user": {"email": "test@example.com"}}):
        mock_redis_service.get_cache = AsyncMock(return_value=b"http://example.com/7t2alSnE2-I")
        response = client.get("/get-download-link/?source=youtube&video_id=7t2alSnE2-I&fmt=mp4")
        assert response.status_code == 200
        assert response.json() == {"detail": "Link for download video was sent by email."}


@pytest.mark.asyncio
async def test_get_link_empty_cache(client, set_dependencies, mock_publish_message, mock_source, mock_redis_service):
    with patch.object(Request, "session", {"user": {"email": "test@example.com"}}):
        mock_redis_service.get_cache = AsyncMock(return_value=None)
        mock_redis_service.set_cache = AsyncMock()
        mock_video_info = MagicMock()
        mock_video_info.url = "http://example.com/7t2alSnE2-I"
        mock_source.return_value = mock_video_info
        response = client.get("/get-download-link/?source=youtube&video_id=7t2alSnE2-I&fmt=mp4")
        assert response.status_code == 200
        assert mock_source.assert_called_once()