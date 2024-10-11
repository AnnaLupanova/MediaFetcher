# AnnaLupanova



## Getting started
Clone repo
```
git clone <path_repo>
```

Install packages:
```
pip install -r requirements.txt
```

Create .env file and insert data
```
YOUTUBE_VIDEO_ID_PATTERN="[0-9A-Za-z_-]{11}"
YOUTUBE_API_KEY="<YOUTUBE_API_KEY>"
YOUTUBE_API_URL="<YOUTUBE_API_URL>"
REDIS_HOST=<REDIS_HOST>
REDIS_PORT=<REDIS_PORT>

```

Run the live server:
```
uvicorn main:app --reload
```

API documentation :
- 127.0.0.1:8000/docs
- 127.0.0.1:8000/redoc

