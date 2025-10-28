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

### Full Request Body (ALL Parameters)
```json
{
  "query": "iPhone 16 Pro review",
  "max_videos": 20,
  "max_comments_per_video": 50,
  "language": "en",
  "region": "US",
  "ai_analysis_prompt": "Analyze sentiment, themes, and purchase intent",
  "model": "gpt-4.1-2025-04-14",
  "max_quote_length": 200
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

### cURL Example (Full Request - All Parameters)
```bash
curl -X POST "https://youtubeslapi-production.up.railway.app/analyze-youtube-search" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "query": "Tesla Model 3 review",
    "max_videos": 10,
    "max_comments_per_video": 50,
    "language": "en",
    "region": "US",
    "ai_analysis_prompt": "Focus on battery life, build quality, and value for money",
    "model": "gpt-4.1-2025-04-14",
    "max_quote_length": 200
  }'
```

---

## Request Parameters

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|-------|-------------|
| `query` | string | ✅ Yes | - | 1-200 chars | YouTube search query |
| `max_videos` | integer | No | 20 | 1-50 | Number of videos to analyze |
| `max_comments_per_video` | integer | No | 50 | 10-100 | Comments per video to analyze |
| `language` | string | No | `"en"` | 2-5 chars | Language code (e.g., 'en', 'es', 'fr') |
| `region` | string | No | `"US"` | 2-5 chars | Region code (e.g., 'US', 'UK', 'CA') |
| `ai_analysis_prompt` | string | No | See below* | 10-500 chars | **Custom AI analysis instructions** |
| `model` | string | No | `"gpt-4.1-2025-04-14"` | - | OpenAI model to use |
| `max_quote_length` | integer | No | 200 | 50-500 | Max length for extracted quotes |

**Default `ai_analysis_prompt`:** `"Analyze sentiment, themes, and purchase intent"`

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

### 1. Product Research (Custom AI Prompt)
```json
{
  "query": "AirPods Pro 2 worth it",
  "max_videos": 10,
  "max_comments_per_video": 100,
  "language": "en",
  "region": "US",
  "ai_analysis_prompt": "Focus on value for money, sound quality complaints, and battery life feedback. Identify if people think it's worth the price.",
  "model": "gpt-4.1-2025-04-14"
}
```
**Use case:** Understand if customers think product is worth buying with targeted analysis

### 2. Competitor Analysis
```json
{
  "query": "Samsung vs iPhone comparison",
  "max_videos": 5,
  "max_comments_per_video": 50,
  "language": "en",
  "region": "US",
  "ai_analysis_prompt": "Compare sentiment between Samsung and iPhone. Identify which brand gets more positive mentions and why.",
  "model": "gpt-4.1-2025-04-14"
}
```
**Use case:** Compare sentiment between competing products

### 3. Brand Monitoring
```json
{
  "query": "Nike running shoes review 2024",
  "max_videos": 15,
  "max_comments_per_video": 75,
  "language": "en",
  "region": "US",
  "ai_analysis_prompt": "Analyze sentiment, identify complaints about durability, comfort issues, and sizing problems.",
  "model": "gpt-4.1-2025-04-14"
}
```
**Use case:** Track what people say about your brand and identify product issues

### 4. Feature Validation (Specific Feature Focus)
```json
{
  "query": "iPhone 16 Pro Action button useful",
  "max_videos": 5,
  "max_comments_per_video": 30,
  "language": "en",
  "region": "US",
  "ai_analysis_prompt": "Focus exclusively on opinions about the Action button feature. Is it useful or gimmicky?",
  "model": "gpt-4.1-2025-04-14"
}
```
**Use case:** Validate specific product features with targeted AI analysis

### 5. Multi-Language Analysis
```json
{
  "query": "PlayStation 5 review",
  "max_videos": 10,
  "max_comments_per_video": 50,
  "language": "es",
  "region": "ES",
  "ai_analysis_prompt": "Analiza el sentimiento, temas principales y intención de compra",
  "model": "gpt-4.1-2025-04-14"
}
```
**Use case:** Analyze Spanish-language content for European market

### 6. Advanced: Purchase Intent Focus
```json
{
  "query": "MacBook Pro M4 review",
  "max_videos": 20,
  "max_comments_per_video": 100,
  "language": "en",
  "region": "US",
  "ai_analysis_prompt": "Identify high purchase intent signals: 'I'm buying', 'just ordered', 'convinced me'. Categorize by price concerns vs feature satisfaction.",
  "model": "gpt-4.1-2025-04-14",
  "max_quote_length": 300
}
```
**Use case:** Deep dive into purchase intent with longer quotes and specific signal detection

---

## 🎯 Customizing AI Analysis with `ai_analysis_prompt`

The **`ai_analysis_prompt`** parameter is the most powerful feature - it lets you customize what the AI looks for.

### Default Behavior
```json
{
  "ai_analysis_prompt": "Analyze sentiment, themes, and purchase intent"
}
```
This gives you general sentiment, themes, and purchase signals.

### Custom Prompts for Specific Insights

**Example 1: Focus on Specific Attributes**
```json
{
  "ai_analysis_prompt": "Focus on camera quality, battery life, and screen brightness. Ignore price discussions."
}
```

**Example 2: Identify Pain Points**
```json
{
  "ai_analysis_prompt": "Identify customer complaints, frustrations, and deal-breakers. What makes people return this product?"
}
```

**Example 3: Competitive Intelligence**
```json
{
  "ai_analysis_prompt": "When users compare this to competitors, what specific advantages or disadvantages do they mention?"
}
```

**Example 4: Decision Factors**
```json
{
  "ai_analysis_prompt": "What factors are making people decide to buy or not buy? Price, features, alternatives mentioned?"
}
```

**Example 5: Use Case Discovery**
```json
{
  "ai_analysis_prompt": "What specific use cases do people mention? How are they actually using this product?"
}
```

### Tips for Effective Prompts

✅ **Be specific**: "Focus on X, Y, Z" works better than "analyze everything"  
✅ **Ask questions**: "Is it durable?" vs "analyze durability"  
✅ **Set scope**: "Ignore price" or "Only focus on technical aspects"  
✅ **Request categorization**: "Categorize by pro users vs casual users"  
✅ **Multi-language**: Write prompts in target language for better results

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

