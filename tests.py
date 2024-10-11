from fastapi.testclient import TestClient
from main import app, get_metadata_with_fmt, get_metadata, get_redis_service
import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock, AsyncMock

client = TestClient(app)


@pytest.fixture
def mock_redis_service():
    with patch("main.RedisService", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def set_dependencies(mock_redis_service):
    app.dependency_overrides[get_redis_service] = lambda: mock_redis_service
    yield
    app.dependency_overrides.pop(get_redis_service, None)


@pytest.fixture
def mock_fetch_video_info():
    with patch("main.fetch_video_info", new_callable=AsyncMock) as mock:
        yield mock


def test_get_link():
    response = client.get("/get-download-link/7t2alSnE2-I")
    assert response.status_code == 200


def test_invalid_url():
    response = client.get("/get-download-link/7t2alSnE2**")
    assert response.status_code == 400
    assert response.json() == {
        "detail": "regex_search: could not find match for (?:v=|\\/)([0-9A-Za-z_-]{11}).*"
    }


def test_get_video_not_supported():
    response = client.get("/get-download-link/7t2alSnE2-I/mp3")
    assert response.status_code == 400
    assert response.json() == {"detail": "Unsupported format: mp3"}


def test_get_video_not_found():
    response = client.get("/get-download-link/eeeeeeeeeee")
    assert response.status_code == 404
    assert response.json() == {"detail": "Video not found"}


@pytest.mark.asyncio
async def test_get_download_link_with_cache_success(set_dependencies, mock_redis_service):
    mock_redis_service.get_cache = AsyncMock(return_value=b"http://example.com/7t2alSnE2-I")
    response = await get_metadata("7t2alSnE2-I", redis=mock_redis_service)
    assert response == "http://example.com/7t2alSnE2-I"


@pytest.mark.asyncio
async def test_get_download_link_empty_cache_success(
    set_dependencies, mock_redis_service, mock_fetch_video_info
):
    mock_redis_service.get_cache = AsyncMock(return_value=None)
    mock_redis_service.set_cache = AsyncMock()
    mock_video_info = MagicMock()
    mock_video_info.url = "http://example.com/7t2alSnE2-I"
    mock_fetch_video_info.return_value = mock_video_info
    result = await get_metadata("7t2alSnE2-I", redis=mock_redis_service)
    assert result == "http://example.com/7t2alSnE2-I"


@pytest.mark.asyncio
async def test_get_json_for_download_with_cache_success(
    set_dependencies, mock_redis_service, mock_fetch_video_info
):
    mock_redis_service.get_cache = AsyncMock(return_value=None)
    mock_redis_service.set_cache = AsyncMock()

    mock_response = SimpleNamespace(
        _monostate=SimpleNamespace(
            duration=300,
            title="Test Video"
        ),
        _filesize_mb=50,
        url="https://example.com/7t2alSnE2-I",
        resolution="1080p"
    )

    mock_fetch_video_info.return_value = mock_response
    response = await get_metadata_with_fmt("7t2alSnE2-I", "webm", redis=mock_redis_service)
    assert response == {
        "duration": 300,
        "filesize_mb": 50,
        "title": "Test Video",
        "url": "https://example.com/7t2alSnE2-I",
        "resolution": "1080p",
    }