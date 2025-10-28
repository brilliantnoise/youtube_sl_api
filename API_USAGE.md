# 🎥 YouTube Social Listening API - Usage Guide

## What It Does

Searches YouTube videos and analyzes them for:
- **Sentiment** (positive, negative, neutral)
- **Themes** (main topics discussed)
- **Purchase Intent** (how likely people are to buy)

All insights come with **full source tracking** (which video, comment, or author).

---

## Making a Request

### Endpoint
```
POST https://youtubeslapi-production.up.railway.app/analyze-youtube-search
```

### Headers
```bash
Content-Type: application/json
X-API-Key: your-api-key-here
```

### Minimal Request Body
```json
{
  "query": "iPhone 16 Pro review"
}
```

### Full Request Body (All Parameters)
```json
{
  "query": "iPhone 16 Pro review",
  "max_videos": 5,
  "max_comments_per_video": 50,
  "include_video_content": true,
  "include_comments": true
}
```

### cURL Example (Minimal)
```bash
curl -X POST "https://youtubeslapi-production.up.railway.app/analyze-youtube-search" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "query": "Tesla Model 3 review"
  }'
```

### cURL Example (Full Request)
```bash
curl -X POST "https://youtubeslapi-production.up.railway.app/analyze-youtube-search" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "query": "Tesla Model 3 review",
    "max_videos": 5,
    "max_comments_per_video": 50,
    "include_video_content": true,
    "include_comments": true
  }'
```

---

## Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✅ Yes | - | YouTube search query |
| `max_videos` | integer | No | 5 | Videos to analyze (1-20) |
| `max_comments_per_video` | integer | No | 50 | Comments per video (0-200) |
| `include_video_content` | boolean | No | true | Analyze video metadata |
| `include_comments` | boolean | No | true | Analyze comments |

---

## Response Format

```json
{
  "insights": [
    {
      "content": "The camera quality is absolutely stunning",
      "sentiment": "positive",
      "themes": ["camera quality", "photography"],
      "purchase_intent": "high",
      "sources": [
        {
          "source_type": "comment",
          "video_id": "abc123",
          "video_title": "iPhone 16 Pro Review",
          "comment_id": "xyz789",
          "author_name": "TechLover",
          "youtube_url": "https://youtube.com/watch?v=abc123"
        }
      ]
    }
  ],
  "metadata": {
    "query": "iPhone 16 Pro review",
    "videos_analyzed": 5,
    "comments_analyzed": 127,
    "relevant_insights_extracted": 45,
    "processing_time_seconds": 12.3,
    "sentiment_distribution": {
      "positive": 62.5,
      "neutral": 25.0,
      "negative": 12.5
    },
    "purchase_intent_distribution": {
      "high": 45.0,
      "medium": 35.0,
      "low": 20.0
    },
    "top_themes": [
      {"theme": "camera quality", "count": 23},
      {"theme": "battery life", "count": 18}
    ]
  }
}
```

---

## Key Response Fields

### Each Insight Contains:
- **`content`** - The actual text analyzed
- **`sentiment`** - `positive`, `negative`, or `neutral`
- **`themes`** - Array of topics (e.g., `["price", "quality"]`)
- **`purchase_intent`** - `high`, `medium`, `low`, or `none`
- **`sources`** - Full tracking info (video, comment, author)

### Metadata Includes:
- Processing stats (videos, comments, time)
- Sentiment breakdown (% positive/negative/neutral)
- Purchase intent breakdown (% high/medium/low)
- Top themes with counts
- YouTube-specific stats (total views, likes, engagement)

---

## Quick Examples

### 1. Product Research
```json
{
  "query": "AirPods Pro 2 worth it",
  "max_videos": 10,
  "max_comments_per_video": 100,
  "include_video_content": true,
  "include_comments": true
}
```
**Use case:** Understand if customers think product is worth buying

### 2. Competitor Analysis
```json
{
  "query": "Samsung vs iPhone comparison",
  "max_videos": 5,
  "max_comments_per_video": 50,
  "include_video_content": true,
  "include_comments": true
}
```
**Use case:** Compare sentiment between competing products

### 3. Brand Monitoring
```json
{
  "query": "Nike running shoes review 2024",
  "max_videos": 15,
  "max_comments_per_video": 75,
  "include_video_content": true,
  "include_comments": true
}
```
**Use case:** Track what people say about your brand

### 4. Feature Validation
```json
{
  "query": "iPhone 16 Pro Action button useful",
  "max_videos": 5,
  "max_comments_per_video": 30,
  "include_video_content": true,
  "include_comments": true
}
```
**Use case:** Validate specific product features

### 5. Video-Only Analysis (Skip Comments)
```json
{
  "query": "Best laptops 2024",
  "max_videos": 10,
  "max_comments_per_video": 0,
  "include_video_content": true,
  "include_comments": false
}
```
**Use case:** Analyze only video titles, descriptions, and metadata

---

## Rate Limits

- **10 requests per minute** per API key
- Exceeding limit returns `429 Too Many Requests`

---

## Error Responses

### 401 - Missing API Key
```json
{
  "detail": "Missing API key. Please provide X-API-Key header."
}
```

### 400 - Invalid Request
```json
{
  "error": "VALIDATION_ERROR",
  "message": "max_videos must be between 1 and 20"
}
```

### 429 - Rate Limit
```json
{
  "error": "Rate limit exceeded. Please try again later."
}
```

### 500 - Server Error
```json
{
  "error": "INTERNAL_SERVER_ERROR",
  "message": "An unexpected error occurred"
}
```

---

## Tips for Best Results

1. **Be Specific** - Use targeted queries like "iPhone 16 Pro camera quality" vs "iPhone"
2. **Adjust Limits** - More videos/comments = better insights but slower response
3. **Check Themes** - Use `top_themes` to discover unexpected topics
4. **Track Sources** - Every insight includes full source tracking for verification
5. **Monitor Intent** - Track `purchase_intent_distribution` over time

---

## Need Help?

- **Documentation:** See `RAILWAY_DEPLOYMENT.md` for setup
- **API Docs:** Visit `https://youtubeslapi-production.up.railway.app/docs` for interactive docs
- **GitHub:** https://github.com/liamwatfeh/youtube_sl_api

---

**That's it! Simple as that.** 🚀

