from auth import get_current_user
from fastapi.testclient import TestClient
from main import app
from service.redis_service import get_redis_service
import pytest
from starlette.requests import Request
from unittest.mock import patch,  AsyncMock

VIDEO_ID = "7t2alSnE2-I"
FMT = "mp4"


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
    with patch('main.Source.source_class') as service:
        yield service


@pytest.fixture
def mock_fetch_video():
    with patch("utils.BaseService.fetch_video_info", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_celery():
    with patch('main.send_email.delay', return_value=AsyncMock()) as conn:
        yield conn


@pytest.fixture
def mock_user():
    with patch("auth.get_current_user", new_callable=AsyncMock) as mock:
        yield mock


@pytest.mark.asyncio
async def test_get_metadata_user_not_authenticated(client, mock_redis_service):
    response = client.get(f"/get-download-link/?source=youtube&video_id={VIDEO_ID}&fmt={FMT}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid authentication credentials"}


@pytest.mark.asyncio
async def test_get_link_user_authenticated(client, set_dependencies, mock_publish_message, mock_redis_service):
    with patch.object(Request, "session", {"user": {"email": "test@example.com"}}):
        mock_redis_service.get_cache = AsyncMock(return_value=b"http://example.com/7t2alSnE2-I")
        response = client.get(f"/get-download-link/?source=youtube&video_id={VIDEO_ID}&fmt={FMT}")
        assert response.status_code == 200
        assert response.json() == {"detail": "Link for download video was sent by email."}


@pytest.mark.asyncio
async def test_get_link_empty_cache(client, set_dependencies, mock_publish_message, mock_redis_service,
                                    mock_fetch_video):
    with patch.object(Request, "session", {"user": {"email": "test@example.com"}}):
        mock_redis_service.get_cache = AsyncMock(return_value=None)
        mock_redis_service.set_cache = AsyncMock()
        mock_fetch_video.return_value = {"url": "http://fakeurl.com/video.mp4"}
        response = client.get(f"/get-download-link/?source=youtube&video_id={VIDEO_ID}&fmt={FMT}")
        assert response.status_code == 200
        assert response.json() == {"detail": "Link for download video was sent by email."}
        mock_fetch_video.assert_called_once()
        mock_publish_message.assert_called_once_with("http://fakeurl.com/video.mp4", "test@example.com")


@pytest.mark.asyncio
async def test_get_link_with_cache(client, set_dependencies, mock_publish_message, mock_redis_service,
                                   mock_fetch_video):
    with patch.object(Request, "session", {"user": {"email": "test@example.com"}}):
        mock_redis_service.get_cache = AsyncMock(return_value=b"http://fakeurl.com/video.mp4")
        response = client.get(f"/get-download-link/?source=youtube&video_id={VIDEO_ID}&fmt={FMT}")
        assert response.status_code == 200
        assert response.json() == {"detail": "Link for download video was sent by email."}
        assert mock_fetch_video.call_count == 0
        mock_publish_message.assert_called_once_with("http://fakeurl.com/video.mp4", "test@example.com")


@pytest.mark.asyncio
async def test_get_link_instagram(client, set_dependencies, mock_publish_message, mock_redis_service):
    with patch.object(Request, "session", {"user": {"email": "test@example.com"}}):
        mock_redis_service.get_cache = AsyncMock(return_value=None)
        mock_redis_service.set_cache = AsyncMock()
        response = client.get(f"/get-download-link/?source=instagram&video_id=7t2alSnE2-H&fmt={FMT}")
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_metadata_not_authenticated(client, set_dependencies, mock_celery, mock_redis_service):
    response = client.get(f"/get-metadata/?source=instagram&video_id=7t2alSnE2-H&fmt={FMT}")
    assert response.status_code == 401


def test_user_login(client: TestClient):
    username, email, password, role = "test_user3", "test@test.com", "secret", "user"
    data = {"username": username, "email": email, "password": password, "role": role}
    response = client.post("/register", json=data)
    data = response.json()
    assert response.status_code == 200
    assert data["username"] == "test_user3"
    assert data["email"] == "test@test.com"
    response = client.post(
        "/token", data={"username": "test_user3", "password": "secret"}
    )
    assert response.status_code == 200, response.text


@pytest.mark.asyncio
async def test_get_metadata_authenticated(client, set_dependencies, mock_user, mock_celery, mock_redis_service):
    mock_user.return_value = {"admin": {"email": "test@example.com"}}
    app.dependency_overrides[get_current_user] = lambda: mock_user
    return_val = b'{"duration": 6379, "url": "http://fakeurl.com/video.mp4"}'
    mock_redis_service.get_cache = AsyncMock(return_value=return_val)
    response = client.get(f"/get-metadata/?source=youtube&video_id={VIDEO_ID}&fmt={FMT}")
    assert response.status_code == 200
    assert response.json() == {"detail": "Video metadata was sent by email."}
    mock_celery.assert_called_once()


