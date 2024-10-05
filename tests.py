from fastapi.testclient import TestClient
from main import app, get_metadata_with_fmt, get_metadata
import asyncio
import pytest
import pytest_asyncio
from unittest.mock import patch


client = TestClient(app)


@pytest.mark.asyncio
async def test_get_link():
    response = client.get("/get-download-link/7t2alSnE2-I")
    assert response.status_code == 200


pytest.mark.asyncio
def test_invalid_url():
    response = client.get("/get-download-link/7t2alSnE2**")
    assert response.status_code == 400
    assert response.json() == {"detail": "regex_search: could not find match for (?:v=|\/)([0-9A-Za-z_-]{11}).*"}


@pytest.mark.asyncio
async def test_get_video_not_found():
    response = client.get("/get-download-link/7t2alSnE2-I/mp3")
    assert response.status_code == 404
    assert response.json() == {"detail": "Video not found"}


@pytest.mark.asyncio
async def test_get_metadata_success(mocker):
    mock_link = f"https://www.youtube.com/watch?v=7t2alSnE2-I"
    mock_stream = mocker.Mock()
    mock_stream.url = "http://example.com/video.mp4"
    with patch('main.fetch_video_info', return_value=mock_stream):
        response = await get_metadata("7t2alSnE2-I")
        assert response == mock_stream.url

@pytest.mark.asyncio
async def test_get_metadata_fmt_success(mocker):
    mock_stream = mocker.Mock()
    mock_stream._monostate.duration = 100
    mock_stream._filesize_mb = 5.5
    mock_stream._monostate.title = "Test Video"
    mock_stream.url = "http://example.com/video.mp4"
    mock_stream.resolution = "720p"
    mock_youtube = mocker.patch("main.fetch_video_info", return_value=mock_stream) 
    response = await get_metadata_with_fmt("7t2alSnE2-I", "mp4")
    assert response['duration'] == mock_stream._monostate.duration



    