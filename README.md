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
Set Environment Variable 
```
YOUTUBE_API_KEY=<YOUTUBE_API_KEY>
```

Run the live server:
```
uvicorn main:app --reload
```

Endpoints:

- 127.0.0.1:8000/get-download-link/{video_id}
- 127.0.0.1:8000/get-video-data/{video_id}

