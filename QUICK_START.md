# 🚀 Quick Start Guide

## Start the API Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Ensure .env is configured with your API keys
cat .env | grep -E "YOUTUBE_RAPIDAPI_KEY|OPENAI_API_KEY|SERVICE_API_KEY"

# 3. Start the server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Test the API

### Using curl
```bash
curl -X POST "http://localhost:8000/analyze-youtube-search" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_SERVICE_API_KEY" \
  -d '{
    "query": "iPhone 15 Pro review",
    "max_videos": 2,
    "max_comments_per_video": 10,
    "language": "en",
    "region": "US",
    "ai_analysis_prompt": "Analyze sentiment, themes, and purchase intent",
    "model": "gpt-4o-mini",
    "max_quote_length": 150
  }'
```

### Using Python
```python
import requests

response = requests.post(
    "http://localhost:8000/analyze-youtube-search",
    headers={
        "Content-Type": "application/json",
        "X-API-Key": "YOUR_SERVICE_API_KEY"
    },
    json={
        "query": "iPhone 15 Pro review",
        "max_videos": 2,
        "max_comments_per_video": 10,
        "language": "en",
        "region": "US",
        "ai_analysis_prompt": "Analyze sentiment, themes, and purchase intent",
        "model": "gpt-4o-mini",
        "max_quote_length": 150
    }
)

print(response.json())
```

## Access Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Deploy to Production

See `DEPLOYMENT_READY.md` for full deployment instructions.
