from fastapi.testclient import TestClient
from main import app, get_metadata_with_fmt, get_metadata
import asyncio
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock
from fakeredis import aioredis
from asyncmock import AsyncMock


client = TestClient(app)

@pytest.fixture
def mock_redis_service():
    with patch("main.RedisService") as mock:
        yield mock

@pytest.fixture
def mock_fetch_video_info():
    with patch("main.fetch_video_info", new_callable=AsyncMock) as mock:
        yield mock


@pytest.mark.asyncio
async def test_get_link():
    response = client.get("/get-download-link/7t2alSnE2-I")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_invalid_url():
    response = client.get("/get-download-link/7t2alSnE2**")
    assert response.status_code == 400
    assert response.json() == {"detail": "regex_search: could not find match for (?:v=|\/)([0-9A-Za-z_-]{11}).*"}


@pytest.mark.asyncio
async def test_get_video_not_supported():
    response = client.get("/get-download-link/7t2alSnE2-I/mp3")
    assert response.status_code == 400
    assert response.json() == {"detail": "Unsupported format: mp3"}


@pytest.mark.asyncio
async def test_get_video_not_found():
    response = client.get("/get-download-link/eeeeeeeeeee")
    assert response.status_code == 404
    assert response.json() == {"detail": "Video not found"}


@pytest.mark.asyncio
async def test_get_download_link_with_cache_success(mock_redis_service):
    mock_redis = mock_redis_service.return_value
    mock_redis.get_cache = AsyncMock(return_value=b"http://example.com/7t2alSnE2-I")
    response = client.get("/get-download-link/7t2alSnE2-I")
    assert response.json() == "http://example.com/7t2alSnE2-I"
    # mock_redis.get_cache.assert_called_once()


@pytest.mark.asyncio
async def test_get_download_link_empty_cache_success(mock_redis_service, mock_fetch_video_info):
    mock_redis = mock_redis_service.return_value
    mock_redis.get_cache = AsyncMock(return_value=None)
    mock_redis.set_cache = AsyncMock()
    mock_fetch_video_info.return_value.url = "http://example.com/7t2alSnE2-I"
    result = await get_metadata("7t2alSnE2-I")
    assert result == "http://example.com/7t2alSnE2-I"
    #mock_fetch_video_info.assert_called_once()

@pytest.mark.asyncio
async def test_get_json_for_download_with_cache_success(mock_redis_service, mock_fetch_video_info):
    mock_redis = mock_redis_service.return_value
    mock_redis.get_cache = AsyncMock(return_value=None)
    mock_redis.set_cache = AsyncMock()
    mock_response = AsyncMock()
    mock_response._monostate.duration = 300
    mock_response._filesize_mb = 50
    mock_response._monostate.title = "Test Video"
    mock_response.url = "https://example.com/7t2alSnE2-I"
    mock_response.resolution = "1080p"
    mock_fetch_video_info.return_value = mock_response
    response = await get_metadata_with_fmt("7t2alSnE2-I", "webm")
    assert response == {
            "duration": 300,
            "filesize_mb": 50,
            "title": "Test Video",
            "url": "https://example.com/7t2alSnE2-I",
            "resolution": "1080p"
        }
