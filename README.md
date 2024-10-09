# AnnaLupanova



## Getting started
Clone repo
```
git clone <path_repo>
```

Create .env file and insert data
```
YOUTUBE_VIDEO_ID_PATTERN="[0-9A-Za-z_-]{11}"
YOUTUBE_API_KEY="<YOUTUBE_API_KEY>"
YOUTUBE_API_URL="<YOUTUBE_API_URL>"
REDIS_HOST=<REDIS_HOST>
REDIS_PORT=<REDIS_PORT>
REDIS_PASSWORD=<REDIS_PASSWORD>
REDIS_USER=<REDIS_USER>
```


Run the application:
```
docker-compose up -d
```

API documentation :
- 127.0.0.1:8000/docs
- 127.0.0.1:8000/redoc

