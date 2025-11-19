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

### Request Body
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

### cURL Example
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

**Note:** Only `query` is required. All other parameters have defaults and can be omitted.

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|-------|-------------|
| `query` | string | ✅ **Required** | - | 1-200 chars | YouTube search query |
| `max_videos` | integer | Optional | `20` | 1-50 | Number of videos to analyze |
| `max_comments_per_video` | integer | Optional | `50` | 10-100 | Comments per video to analyze |
| `language` | string | Optional | `"en"` | 2-5 chars | Language code (e.g., 'en', 'es', 'fr') |
| `region` | string | Optional | `"US"` | 2-5 chars | Region code (e.g., 'US', 'UK', 'CA') |
| `start_date` | string | Optional | `null` | YYYY-MM-DD | Filter comments from this date onwards (must provide both dates) |
| `end_date` | string | Optional | `null` | YYYY-MM-DD | Filter comments up to this date (must provide both dates) |
| `ai_analysis_prompt` | string | Optional | See below* | 10-500 chars | **Custom AI analysis instructions** |
| `model` | string | Optional | `"gpt-4.1-2025-04-14"` | - | OpenAI model to use |
| `max_quote_length` | integer | Optional | `200` | 50-500 | Max length for extracted quotes |

**Default `ai_analysis_prompt`:** `"Analyze sentiment, themes, and purchase intent"`

### Minimal Valid Request
If you only want to use defaults, you can send just the query:
```json
{
  "query": "iPhone 16 Pro review"
}
```
This will use all default values shown in the table above.

---

## 📅 Date Filtering

Filter comments by date range to analyze sentiment trends over specific time periods.

### Key Features
- ✅ **Cost Savings**: Comments are filtered **BEFORE** AI analysis → Lower OpenAI costs
- ✅ **Timezone Aware**: Automatically infers timezone from `region` parameter
- ✅ **ISO Format**: Uses standard `YYYY-MM-DD` format (e.g., `"2024-11-19"`)
- ✅ **Both Required**: Must provide both `start_date` and `end_date` together

### How It Works
1. YouTube provides relative dates (e.g., "1 month ago", "3 days ago")
2. System converts these to absolute dates using region timezone
3. Comments outside date range are filtered out
4. Only filtered comments are sent to AI for analysis

### Important Notes
⚠️ **Both dates required**: You cannot provide only one date
⚠️ **Date format**: Must be `YYYY-MM-DD` (ISO 8601)
⚠️ **Timezone**: Inferred from `region` (e.g., `"US"` → `America/New_York`)
⚠️ **Approximate**: YouTube's relative dates are approximate (e.g., "1 month ago" ≈ 30 days)

### Example 1: Analyze Q4 2024 Comments

```bash
curl -X POST "https://youtubeslapi-production.up.railway.app/analyze-youtube-search" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "query": "Tesla Model 3",
    "max_videos": 10,
    "start_date": "2024-10-01",
    "end_date": "2024-12-31",
    "region": "US"
  }'
```

### Example 2: Last 30 Days Only

```json
{
  "query": "iPhone 16 Pro review",
  "max_videos": 15,
  "start_date": "2024-10-20",
  "end_date": "2024-11-19",
  "region": "UK"
}
```
**Timezone**: `Europe/London` (inferred from `"UK"`)

### Example 3: Compare Different Time Periods

**Recent sentiment** (last week):
```json
{
  "query": "Samsung Galaxy S24",
  "start_date": "2024-11-12",
  "end_date": "2024-11-19"
}
```

**Historical sentiment** (3 months ago):
```json
{
  "query": "Samsung Galaxy S24",
  "start_date": "2024-08-01",
  "end_date": "2024-08-31"
}
```

### Response Metadata
When date filtering is applied, the response includes:

```json
{
  "metadata": {
    "youtube_specific": {
      "date_filter_applied": true,
      "date_filter_stats": {
        "total_comments_before": 150,
        "total_comments_after": 45,
        "comments_filtered_out": 105,
        "comments_unparseable": 0,
        "videos_with_comments": 8,
        "videos_without_comments": 2,
        "date_range": {
          "start": "2024-10-01",
          "end": "2024-12-31",
          "timezone": "America/New_York"
        }
      }
    }
  }
}
```

### Error Handling

**Error 1: Only one date provided**
```json
{
  "error": "DATE_VALIDATION",
  "message": "Both start_date and end_date must be provided together, or neither."
}
```

**Error 2: Invalid date range**
```json
{
  "error": "DATE_VALIDATION",
  "message": "Invalid date range: start_date (2024-12-31) cannot be after end_date (2024-01-01)."
}
```

**Error 3: Invalid format**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "String should match pattern '^\\d{4}-\\d{2}-\\d{2}$'"
}
```

### Supported Regions & Timezones

Common region-to-timezone mappings:
- `"US"` → `America/New_York`
- `"UK"`, `"GB"` → `Europe/London`
- `"JP"` → `Asia/Tokyo`
- `"AU"` → `Australia/Sydney`
- `"FR"` → `Europe/Paris`
- `"CA"` → `America/Toronto`
- Unknown regions → `UTC`

*See full list in the codebase: `app/utils/date_parser.py`*

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

