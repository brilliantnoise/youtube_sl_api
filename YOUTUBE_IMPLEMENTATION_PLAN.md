# 🎥 YouTube Social Listening API - Comprehensive Implementation Plan

> **For Cursor Agent Mode**: Step-by-step implementation guide with narrow, focused tasks that can be executed incrementally by AI agents.

> ✅ **VERIFIED ACCURACY**: All API endpoints, parameters, response structures, and field names have been tested with the actual YouTube138 RapidAPI (December 2024). The schemas and data cleaning logic use REAL response formats from live testing.

## 🎯 **Project Overview**

**Goal**: Create a YouTube social listening API with 1 endpoint that searches for videos and analyzes video titles, descriptions, and comments for sentiment, themes, and purchase intent using the YouTube138 RapidAPI and OpenAI.

**Architecture**: Duplicate the proven TikTok/Instagram API structure for YouTube with 80% code reuse.

**Timeline**: 6 weeks across 4 phases

**Cost per Analysis**: ~$1.01 (21 YouTube API calls + 20 OpenAI calls)

**1 Endpoint**:
1. **`/analyze-youtube-search`** - Search videos by keyword and analyze content + comments

---

## 📋 **Phase 1: Foundation Setup** (Week 1-2)

### **Task 1.1: Project Structure Setup**
Create the basic project structure mirroring the TikTok/Instagram APIs:

**Steps for Cursor Agent**:
1. Create new directory `youtube_sl_api` 
2. Copy the following structure from the TikTok project:
   ```
   youtube_sl_api/
   ├── app/
   │   ├── __init__.py
   │   ├── main.py
   │   ├── core/
   │   │   ├── __init__.py
   │   │   ├── config.py
   │   │   └── exceptions.py
   │   ├── models/
   │   │   ├── __init__.py
   │   │   └── youtube_schemas.py
   │   └── services/
   │       ├── __init__.py
   │       ├── youtube_search/
   │       │   ├── __init__.py
   │       │   └── search_service.py
   │       └── youtube_shared/
   │           ├── __init__.py
   │           ├── youtube_api_client.py
   │           ├── youtube_comment_collector.py
   │           ├── youtube_data_cleaners.py
   │           ├── youtube_ai_analyzer.py
   │           └── youtube_response_builder.py
   ├── requirements.txt
   ├── .env.example
   ├── .gitignore
   └── README.md
   ```

**Deliverable**: Clean project structure with empty files ready for implementation.

### **Task 1.2: Environment Configuration**
Set up configuration management for YouTube API keys.

**Edit `app/core/config.py`**:
```python
from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Configuration
    API_TITLE: str = Field(
        default="YouTube Social Media Analysis API",
        description="API title for documentation"
    )
    API_VERSION: str = Field(
        default="1.0.0", 
        description="API version"
    )
    
    # YouTube API Configuration (RapidAPI)
    YOUTUBE_RAPIDAPI_KEY: str = Field(
        ...,
        env="YOUTUBE_RAPIDAPI_KEY",
        description="YouTube RapidAPI key (required)",
        min_length=10
    )
    YOUTUBE_RAPIDAPI_HOST: str = Field(
        default="youtube138.p.rapidapi.com",
        env="YOUTUBE_RAPIDAPI_HOST",
        description="YouTube RapidAPI host"
    )
    YOUTUBE_BASE_URL: str = Field(
        default="https://youtube138.p.rapidapi.com",
        env="YOUTUBE_BASE_URL",
        description="YouTube API base URL"
    )
    
    # AI Configuration
    OPENAI_API_KEY: str = Field(
        ...,
        env="OPENAI_API_KEY", 
        description="OpenAI API key (required)",
        min_length=20
    )
    DEFAULT_MODEL: str = Field(
        default="gpt-4.1-2025-04-14",
        env="DEFAULT_MODEL",
        description="Default OpenAI model to use"
    )
    
    # Authentication
    SERVICE_API_KEY: str = Field(
        ...,
        env="SERVICE_API_KEY",
        description="API key for service authentication (required)",
        min_length=16
    )
    
    # Processing Limits
    MAX_VIDEOS_PER_REQUEST: int = Field(
        default=50,
        env="MAX_VIDEOS_PER_REQUEST",
        description="Maximum videos per request",
        ge=1, le=100
    )
    DEFAULT_VIDEOS_PER_REQUEST: int = Field(
        default=20,
        env="DEFAULT_VIDEOS_PER_REQUEST", 
        description="Default number of videos per request",
        ge=1, le=50
    )
    MAX_COMMENTS_PER_VIDEO: int = Field(
        default=50,
        env="MAX_COMMENTS_PER_VIDEO",
        description="Maximum comments to collect per video",
        ge=10, le=100
    )
    
    # Request Configuration  
    REQUEST_TIMEOUT: float = Field(
        default=30.0,
        env="REQUEST_TIMEOUT",
        description="HTTP request timeout in seconds",
        ge=10.0, le=120.0
    )
    YOUTUBE_REQUEST_DELAY: float = Field(
        default=0.5,
        env="YOUTUBE_REQUEST_DELAY",
        description="Delay between YouTube API requests in seconds",
        ge=0.0, le=5.0
    )
    
    # Environment
    ENVIRONMENT: str = Field(
        default="development",
        env="ENVIRONMENT",
        description="Application environment"
    )
    
    # Server Configuration
    PORT: int = Field(
        default=8000,
        env="PORT",
        description="Port for the server to listen on",
        ge=1, le=65535
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()
```

**Create `.env.example`**:
```env
# YouTube API (RapidAPI)
YOUTUBE_RAPIDAPI_KEY=your_rapidapi_key_here
YOUTUBE_RAPIDAPI_HOST=youtube138.p.rapidapi.com
YOUTUBE_BASE_URL=https://youtube138.p.rapidapi.com

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
DEFAULT_MODEL=gpt-4.1-2025-04-14

# Service Authentication
SERVICE_API_KEY=your_service_api_key_here

# Processing Configuration
MAX_VIDEOS_PER_REQUEST=50
DEFAULT_VIDEOS_PER_REQUEST=20
MAX_COMMENTS_PER_VIDEO=50
REQUEST_TIMEOUT=30.0
YOUTUBE_REQUEST_DELAY=0.5

# Environment
ENVIRONMENT=development
PORT=8000
```

**Deliverable**: Complete configuration management ready for YouTube API keys.

### **Task 1.3: Dependencies and Requirements**
Set up the required Python packages with latest versions.

**Create/Update `requirements.txt`**:
```txt
# Core FastAPI and Web Framework (Latest versions)
fastapi[standard]==0.115.6
uvicorn[standard]==0.32.2

# Pydantic for data validation and settings (Latest)
pydantic==2.10.4
pydantic-settings==2.6.2

# AI/ML Dependencies (Latest)
openai==1.58.1

# HTTP Client and Networking (Latest)
httpx==0.28.1
requests==2.32.3

# Environment and Configuration
python-dotenv==1.0.1

# Rate Limiting and Throttling
slowapi==0.1.9
asyncio-throttle==1.0.2

# Development and Testing (Latest)
pytest==8.3.4
pytest-asyncio==0.25.0
pytest-httpx==0.31.2

# Logging and Monitoring
structlog==24.5.0

# Data Processing (Latest)
pandas==2.2.3
numpy==2.2.1

# Additional FastAPI Extensions
python-multipart==0.0.12

# Security and Authentication
cryptography==43.0.3
python-jose[cryptography]==3.3.0

# Database (if needed for caching)
redis==5.2.0
sqlalchemy==2.0.36
```

**Deliverable**: Complete, modern dependency management with latest stable versions.

### **Task 1.4: Exception Handling Setup**
Copy and adapt the exception handling from TikTok/Instagram APIs.

**Edit `app/core/exceptions.py`**:
```python
import logging
from typing import Optional, Dict, Any
from datetime import datetime

class YouTubeAPIException(Exception):
    """Base exception for YouTube API errors."""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 500, 
        error_code: Optional[str] = None, 
        details: Optional[Dict[str, Any]] = None,
        log_level: str = "ERROR"
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self._generate_error_code()
        self.details = self._sanitize_details(details or {})
        self.log_level = log_level
        self.timestamp = datetime.utcnow().isoformat()
        
        # Log the exception
        logger = logging.getLogger(self.__class__.__module__)
        getattr(logger, log_level.lower(), logger.error)(
            f"{self.error_code}: {self.message}",
            extra={
                "error_code": self.error_code,
                "status_code": self.status_code,
                "details": self.details,
                "timestamp": self.timestamp
            }
        )
        
        super().__init__(self.message)
    
    def _generate_error_code(self) -> str:
        """Generate error code from class name."""
        class_name = self.__class__.__name__
        if class_name.endswith('Error'):
            class_name = class_name[:-5]
        return class_name.upper()
    
    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize details to prevent sensitive information leakage."""
        sanitized = {}
        sensitive_keys = {'password', 'token', 'key', 'secret', 'auth', 'api_key'}
        
        for key, value in details.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str) and len(value) > 1000:
                sanitized[key] = value[:1000] + "...[TRUNCATED]"
            else:
                sanitized[key] = value
                
        return sanitized
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
            "status_code": self.status_code
        }

class YouTubeValidationError(YouTubeAPIException):
    """Request validation error."""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["provided_value"] = value
        super().__init__(message, status_code=400, details=details)

class YouTubeDataCollectionError(YouTubeAPIException):
    """YouTube data collection error."""
    
    def __init__(self, message: str, api_endpoint: Optional[str] = None, http_status: Optional[int] = None):
        details = {}
        if api_endpoint:
            details["api_endpoint"] = api_endpoint
        if http_status:
            details["http_status"] = http_status
        super().__init__(message, status_code=502, details=details)

class YouTubeAnalysisError(YouTubeAPIException):
    """AI analysis error."""
    
    def __init__(self, message: str, model: Optional[str] = None, video_id: Optional[str] = None):
        details = {}
        if model:
            details["model"] = model
        if video_id:
            details["video_id"] = video_id
        super().__init__(message, status_code=503, details=details)

class RateLimitExceededError(YouTubeAPIException):
    """Rate limit exceeded error."""
    
    def __init__(self, message: str, service: Optional[str] = None, retry_after: Optional[int] = None):
        details = {}
        if service:
            details["service"] = service
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, status_code=429, details=details, log_level="WARNING")

class AuthenticationError(YouTubeAPIException):
    """Authentication error."""
    
    def __init__(self, message: str, auth_type: Optional[str] = None):
        details = {"auth_type": auth_type} if auth_type else {}
        super().__init__(message, status_code=401, details=details, log_level="WARNING")
```

**Deliverable**: Complete exception handling system ready for YouTube-specific errors.

---

## 📋 **Phase 2: Core API Infrastructure** (Week 3-4)

### **Task 2.1: Data Models and Schemas**
Create Pydantic models for YouTube API requests and responses.

**Edit `app/models/youtube_schemas.py`**:
```python
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime

# ===== ACTUAL YOUTUBE API DATA MODELS =====
# Based on real YouTube138 RapidAPI response schemas

class YouTubeChannelAvatar(BaseModel):
    """YouTube channel avatar with different sizes"""
    height: int = Field(..., description="Avatar height")
    width: int = Field(..., description="Avatar width")
    url: str = Field(..., description="Avatar URL")

class YouTubeChannelBadge(BaseModel):
    """YouTube channel badge"""
    text: str = Field(..., description="Badge text")
    type: str = Field(..., description="Badge type")

class YouTubeChannel(BaseModel):
    """YouTube channel information"""
    channelId: str = Field(..., description="Channel ID")
    title: str = Field(..., description="Channel name")
    avatar: List[YouTubeChannelAvatar] = Field(default=[], description="Channel avatars")
    badges: Optional[List[YouTubeChannelBadge]] = Field(None, description="Channel badges")
    canonicalBaseUrl: Optional[str] = Field(None, description="Channel URL")

class YouTubeThumbnail(BaseModel):
    """YouTube video thumbnail"""
    height: int = Field(..., description="Thumbnail height")
    width: int = Field(..., description="Thumbnail width")
    url: str = Field(..., description="Thumbnail URL")

class YouTubeVideoStats(BaseModel):
    """YouTube video statistics"""
    views: int = Field(default=0, description="View count")

class YouTubeVideo(BaseModel):
    """Single YouTube video from search results"""
    videoId: str = Field(..., description="YouTube video ID")
    title: str = Field(..., description="Video title")
    descriptionSnippet: Optional[str] = Field(None, description="Video description snippet")
    lengthSeconds: Optional[int] = Field(None, description="Video duration in seconds")
    publishedTimeText: Optional[str] = Field(None, description="Published time text")
    isLiveNow: bool = Field(default=False, description="Is currently live")
    author: YouTubeChannel = Field(..., description="Video author/channel")
    stats: YouTubeVideoStats = Field(..., description="Video statistics")
    thumbnails: List[YouTubeThumbnail] = Field(default=[], description="Video thumbnails")
    movingThumbnails: Optional[List[YouTubeThumbnail]] = Field(None, description="Animated thumbnails")
    badges: Optional[List[str]] = Field(None, description="Video badges (CC, etc.)")
    
    @property
    def youtube_url(self) -> str:
        """Generate YouTube video URL"""
        return f"https://www.youtube.com/watch?v={self.videoId}"
    
    @property
    def duration_formatted(self) -> str:
        """Get formatted duration"""
        if not self.lengthSeconds:
            return "Unknown"
        
        minutes = self.lengthSeconds // 60
        seconds = self.lengthSeconds % 60
        return f"{minutes}:{seconds:02d}"

class YouTubeCommentAuthor(BaseModel):
    """YouTube comment author"""
    channelId: str = Field(..., description="Author channel ID")
    title: str = Field(..., description="Author name")
    avatar: List[YouTubeChannelAvatar] = Field(default=[], description="Author avatars")
    badges: Optional[List[str]] = Field(None, description="Author badges")
    isChannelOwner: bool = Field(default=False, description="Is video owner")

class YouTubeCommentStats(BaseModel):
    """YouTube comment statistics"""
    votes: int = Field(default=0, description="Comment likes/votes")
    replies: int = Field(default=0, description="Reply count")

class YouTubeCommentPinned(BaseModel):
    """YouTube comment pinned status"""
    status: bool = Field(default=False, description="Is pinned")
    text: Optional[str] = Field(None, description="Pinned text")

class YouTubeComment(BaseModel):
    """YouTube comment from video"""
    commentId: str = Field(..., description="Comment ID")
    content: str = Field(..., description="Comment text")
    publishedTimeText: str = Field(..., description="Published time text")
    author: YouTubeCommentAuthor = Field(..., description="Comment author")
    stats: YouTubeCommentStats = Field(..., description="Comment statistics")
    creatorHeart: bool = Field(default=False, description="Has creator heart")
    pinned: Optional[YouTubeCommentPinned] = Field(None, description="Pinned status")
    cursorReplies: Optional[str] = Field(None, description="Cursor for replies")

class YouTubeSearchData(BaseModel):
    """Data section from search response"""
    contents: List[YouTubeVideo] = Field(default=[], description="Search results")
    cursorNext: Optional[str] = Field(None, description="Pagination cursor")
    estimatedResults: int = Field(default=0, description="Estimated total results")
    refinements: Optional[List[str]] = Field(None, description="Search refinements")

class YouTubeSearchResponse(BaseModel):
    """Response from /search/ endpoint"""
    contents: List[YouTubeVideo] = Field(default=[], description="Search results")
    cursorNext: Optional[str] = Field(None, description="Pagination cursor")
    estimatedResults: int = Field(default=0, description="Estimated total results")
    refinements: Optional[List[str]] = Field(None, description="Search refinements")

class YouTubeCommentsFilter(BaseModel):
    """Comment filter option"""
    cursorFilter: Optional[str] = Field(None, description="Filter cursor")
    selected: bool = Field(default=False, description="Is selected")
    title: str = Field(..., description="Filter title")

class YouTubeCommentsResponse(BaseModel):
    """Response from /video/comments/ endpoint"""
    comments: List[YouTubeComment] = Field(default=[], description="Video comments")
    cursorNext: Optional[str] = Field(None, description="Pagination cursor")
    totalCommentsCount: int = Field(default=0, description="Total comment count")
    filters: List[YouTubeCommentsFilter] = Field(default=[], description="Comment filters")

# ===== API REQUEST/RESPONSE MODELS =====

class YouTubeSearchAnalysisRequest(BaseModel):
    """Request model for YouTube search analysis."""
    
    query: str = Field(
        ...,
        description="Search query for YouTube videos",
        min_length=1,
        max_length=200
    )
    max_videos: int = Field(
        default=20,
        description="Maximum number of videos to analyze",
        ge=1,
        le=50
    )
    max_comments_per_video: int = Field(
        default=50,
        description="Maximum comments per video to analyze",
        ge=10,
        le=100
    )
    language: str = Field(
        default="en",
        description="Language code (e.g., 'en', 'es', 'fr')",
        min_length=2,
        max_length=5
    )
    region: str = Field(
        default="US",
        description="Region code (e.g., 'US', 'UK', 'CA')",
        min_length=2,
        max_length=5
    )
    ai_analysis_prompt: str = Field(
        default="Analyze sentiment, themes, and purchase intent",
        description="Custom AI analysis instructions",
        min_length=10,
        max_length=500
    )
    model: str = Field(
        default="gpt-4.1-2025-04-14",
        description="OpenAI model to use for analysis"
    )
    max_quote_length: int = Field(
        default=200,
        description="Maximum length for extracted quotes",
        ge=50,
        le=500
    )
    
    @validator('query')
    def validate_query(cls, v):
        query = v.strip()
        if not query:
            raise ValueError('Search query cannot be empty')
        return query

class YouTubeAnalysisItem(BaseModel):
    """Individual analysis result with source tracking."""
    
    quote: str = Field(..., description="Text that was analyzed (video title/description or comment)")
    sentiment: str = Field(..., description="Sentiment classification (positive, negative, neutral)")
    theme: str = Field(..., description="Main theme or topic identified")
    purchase_intent: str = Field(..., description="Purchase intent level (high, medium, low, none)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI analysis confidence score")
    
    # Source identification
    source_type: str = Field(..., description="'video_title', 'video_description', or 'comment'")
    video_id: str = Field(..., description="YouTube video ID")
    video_url: str = Field(..., description="Direct YouTube video URL (https://www.youtube.com/watch?v={videoId})")
    video_title: str = Field(..., description="Video title")
    video_author_channel: str = Field(..., description="Video channel name")
    
    # Quote author (different from video author if it's a comment)
    quote_author_name: str = Field(..., description="Name of who wrote the quote")
    quote_author_channel_id: Optional[str] = Field(None, description="Channel ID of quote author")
    
    # Optional fields based on source type
    comment_id: Optional[str] = Field(None, description="Comment ID if source is comment")
    comment_url: Optional[str] = Field(None, description="YouTube comment URL with timestamp")
    comment_like_count: Optional[int] = Field(None, description="Comment likes if source is comment")
    comment_reply_count: Optional[int] = Field(None, description="Comment replies if source is comment")
    
    # Video metadata
    video_view_count: int = Field(default=0, description="Video views")
    video_duration_seconds: Optional[int] = Field(None, description="Video duration")
    video_published_time: Optional[str] = Field(None, description="Video publish time (e.g., '5 years ago')")
    video_is_live: bool = Field(default=False, description="Is live video")
    
    # Comment timing (if source is comment)
    comment_published_time: Optional[str] = Field(None, description="Comment publish time (e.g., '1 year ago')")

class YouTubeAnalysisMetadata(BaseModel):
    """Analysis metadata and statistics."""
    
    total_videos_analyzed: int
    total_comments_found: int
    relevant_insights_extracted: int
    processing_time_seconds: float
    model_used: str
    
    youtube_api_usage: Dict[str, Any]
    openai_api_usage: Dict[str, Any]
    
    sentiment_distribution: Dict[str, int]
    purchase_intent_distribution: Dict[str, int]
    top_themes: List[Dict[str, Any]]
    
    youtube_specific: Optional[Dict[str, Any]] = None

class YouTubeUnifiedAnalysisResponse(BaseModel):
    """Unified response model for YouTube search analysis."""
    
    comment_analyses: List[YouTubeAnalysisItem]
    metadata: YouTubeAnalysisMetadata
```

**Deliverable**: Complete data models for all YouTube API requests and responses.

### **Task 2.2: YouTube API Client**
Create the core client for YouTube138 RapidAPI.

**Steps for Cursor Agent**:
1. Edit `app/services/youtube_shared/youtube_api_client.py`
2. Copy the TikTok/Instagram API client structure but adapt for YouTube endpoints
3. Implement these methods with **EXACT** parameters:
   - `search_videos(query, hl="en", gl="US", cursor=None)` → `/search/`
   - `get_video_comments(video_id, hl="en", gl="US", cursor=None)` → `/video/comments/`
4. Include rate limiting with 0.5 second delays between requests
5. Add proper error handling for YouTube API responses

**Real API Parameters** (from your actual tests):
```python
# 1. Search endpoint:
url = "https://youtube138.p.rapidapi.com/search/"
querystring = {
    "q": "despacito",           # Required: search query
    "hl": "en",                 # Optional: language (default: en)
    "gl": "US",                 # Optional: region (default: US)
    # Pagination handled via response cursorNext
}

# 2. Comments endpoint:
url = "https://youtube138.p.rapidapi.com/video/comments/"
querystring = {
    "id": "kJQP7kiw5Fk",        # Required: video ID
    "hl": "en",                 # Optional: language (default: en)
    "gl": "US",                 # Optional: region (default: US)
    # Pagination handled via response cursorNext
}

# Common headers for all endpoints:
headers = {
    "x-rapidapi-key": "YOUR_KEY",
    "x-rapidapi-host": "youtube138.p.rapidapi.com"
}
```

**Key Implementation Notes**:
- **Search response**: Videos are in `response["contents"]` array
- **Comments response**: Comments are in `response["comments"]` array
- **Video ID format**: Use `video["videoId"]` for comment collection
- **Pagination**: Both endpoints use `cursorNext` for pagination
- **Comment sorting**: Available filters in `response["filters"]` ("Top comments" vs "Newest first")
- **URL generation**: `https://www.youtube.com/watch?v={videoId}` for videos
- **Comment URLs**: `https://www.youtube.com/watch?v={videoId}&lc={commentId}` for comments
- Handle 429 rate limit errors with retry logic
- Log all API calls for debugging

**Deliverable**: Complete YouTube API client with all required endpoints.

### **Task 2.3: Comment Collection Service**
**Steps for Cursor Agent**:
1. Edit `app/services/youtube_shared/youtube_comment_collector.py`
2. Create `collect_all_comments(videos, max_comments_per_video)` method
3. For each video, call `api_client.get_video_comments(video.videoId)` using video ID
4. Handle pagination if more than max_comments_per_video available
5. Group comments by video_id in returned dictionary
6. Track metadata: total comments, API calls, processing time

**Deliverable**: Service that collects comments for multiple videos efficiently.

### **Task 2.4: Data Cleaning Service**  
**Steps for Cursor Agent**:
1. Edit `app/services/youtube_shared/youtube_data_cleaners.py`
2. Copy TikTok/Instagram data cleaning logic and adapt for **real YouTube JSON structure**
3. Implement `clean_youtube_videos()` method with actual field paths:

```python
def clean_youtube_videos(raw_videos: List[Dict]) -> List[Dict]:
    """Clean YouTube videos using actual API response structure."""
    cleaned_videos = []
    
    for video in raw_videos:
        # Extract video data safely
        cleaned_video = {
            "video_id": video["videoId"],                    # Video ID
            "title": video["title"],                         # Video title
            "description": video.get("descriptionSnippet", ""),  # Description snippet
            "video_url": f"https://www.youtube.com/watch?v={video['videoId']}",  # YouTube URL
            "duration_seconds": video.get("lengthSeconds", 0),  # Duration
            "view_count": video.get("stats", {}).get("views", 0),  # Views
            "published_time": video.get("publishedTimeText", ""),  # Published time
            "is_live": video.get("isLiveNow", False),        # Live status
            "channel_id": video["author"]["channelId"],      # Channel ID
            "channel_name": video["author"]["title"],        # Channel name
            "channel_url": video["author"].get("canonicalBaseUrl", ""),  # Channel URL
            "thumbnail_url": get_best_thumbnail(video.get("thumbnails", [])),  # Best thumbnail
            "badges": video.get("badges", []),               # Video badges
        }
        cleaned_videos.append(cleaned_video)
    
    return cleaned_videos

def get_best_thumbnail(thumbnails: List[Dict]) -> str:
    """Get highest quality thumbnail URL."""
    if not thumbnails:
        return ""
    
    # Sort by resolution (width * height) and get the best one
    best_thumbnail = max(thumbnails, key=lambda t: t.get("width", 0) * t.get("height", 0))
    return best_thumbnail.get("url", "")

def clean_youtube_comments(raw_comments: List[Dict]) -> List[Dict]:
    """Clean YouTube comments using actual API response structure."""
    cleaned_comments = []
    
    for comment in raw_comments:
        cleaned_comment = {
            "comment_id": comment["commentId"],              # Comment ID
            "text": comment["content"],                       # Comment text
            "author_name": comment["author"]["title"],       # Author name
            "author_channel_id": comment["author"]["channelId"],  # Author channel
            "like_count": comment.get("stats", {}).get("votes", 0),  # Likes
            "reply_count": comment.get("stats", {}).get("replies", 0),  # Replies
            "published_time": comment.get("publishedTimeText", ""),  # Published time (e.g., "1 year ago")
            "is_channel_owner": comment["author"].get("isChannelOwner", False),  # Is video owner
            "has_creator_heart": comment.get("creatorHeart", False),  # Creator heart
            "is_pinned": comment.get("pinned", {}).get("status", False),  # Pinned status
        }
        cleaned_comments.append(cleaned_comment)
    
    return cleaned_comments
```

4. Add YouTube-specific features:
   - Extract video duration and format it properly
   - Handle live videos vs regular videos
   - Extract channel information and badges
   - Calculate engagement rates where possible
   - Filter spam comments by checking patterns

**Deliverable**: Clean, normalized YouTube data ready for AI analysis.

---

## 📋 **Phase 3: AI Analysis Integration** (Week 5-6)

### **Task 3.1: OpenAI Analysis Service**
**Steps for Cursor Agent**:
1. Edit `app/services/youtube_shared/youtube_ai_analyzer.py`
2. Copy TikTok/Instagram AI analyzer but adapt prompts for YouTube
3. Create method `analyze_videos_with_comments()`
4. For each video, build comprehensive prompt with:
   - Video title and description
   - All comments for that video (in 'top comments' order, limited by user's max_comments_per_video)
   - Video metadata (duration, views, channel info)
   - User's custom analysis instructions
5. Call OpenAI with structured JSON output
6. **CRITICAL**: For each analyzed quote, include:
   - Original video URL: `https://www.youtube.com/watch?v={videoId}`
   - Comment URL (if from comment): `https://www.youtube.com/watch?v={videoId}&lc={commentId}`
   - Whether quote is from video title, description, or comment
   - Quote author info (channel owner vs commenter)
   - All metadata needed for `YouTubeAnalysisItem` schema

**Key YouTube Prompt Adaptations**:
- Include video duration and view count context
- Add channel information and verification status
- Include live video status if applicable
- Adapt examples for YouTube content style
- Consider video vs comment context differently

**Sample Analysis Data Flow**:
```json
// Input to AI: Video + Comments
{
  "video": {
    "videoId": "kJQP7kiw5Fk",
    "url": "https://www.youtube.com/watch?v=kJQP7kiw5Fk",
    "title": "Luis Fonsi - Despacito ft. Daddy Yankee",
    "description": "#LuisFonsi #Despacito #Imposible #Calypso Music video by Luis...",
    "channel": "Luis Fonsi",
    "views": 7870471715,
    "duration": "4:42"
  },
  "comments": [
    {"text": "2017: People came to listen song. 2021: People come to check views.", "author": "Armaan singh", "likes": 414947},
    {"text": "This song never gets old! Still listening in 2024", "author": "MusicLover123", "likes": 25000}
  ]
}

// Output from AI: Analysis Items
[
  {
    "quote": "Luis Fonsi - Despacito ft. Daddy Yankee",
    "sentiment": "positive",
    "theme": "music collaboration",
    "purchase_intent": "low",
    "source_type": "video_title",
    "video_url": "https://www.youtube.com/watch?v=kJQP7kiw5Fk",
    "quote_author_name": "Luis Fonsi"
  },
  {
    "quote": "2017: People came to listen song. 2021: People come to check views.",
    "sentiment": "neutral", 
    "theme": "viral content observation",
    "purchase_intent": "none",
    "source_type": "comment",
    "video_url": "https://www.youtube.com/watch?v=kJQP7kiw5Fk",
    "comment_url": "https://www.youtube.com/watch?v=kJQP7kiw5Fk&lc=UgwW1S95-KHLW2bUI-14AaABAg",
    "quote_author_name": "Armaan singh",
    "comment_like_count": 414947
  }
]
```

**Deliverable**: AI analysis service that provides insights on YouTube content with full source tracking.

### **Task 3.2: Response Builder Service**
**Steps for Cursor Agent**:
1. Edit `app/services/youtube_shared/youtube_response_builder.py`
2. Copy TikTok/Instagram response builder structure
3. Adapt metadata to include YouTube-specific metrics:
   - Video duration analysis
   - View count statistics
   - Channel verification breakdown
   - Live vs regular video analysis
   - YouTube API usage tracking
4. Calculate sentiment and purchase intent distributions
5. Generate top themes analysis

**Deliverable**: Service that builds comprehensive YouTube analysis responses.

---

## 📋 **Phase 4: Service Orchestration & Endpoints** (Week 7-8)

### **Task 4.1: Search Analysis Service**
**Steps for Cursor Agent**:
1. Edit `app/services/youtube_search/search_service.py`
2. Copy TikTok/Instagram service structure
3. Implement `analyze_youtube_search()` method with 4-stage pipeline:
   - Stage 1: Call `api_client.search_videos()`
   - Stage 2: Clean videos with `data_cleaner.clean_youtube_videos()`
   - Stage 3: Collect & clean comments, then AI analysis
   - Stage 4: Build final response
4. Add comprehensive error handling and logging
5. Track processing time and API usage
6. Handle pagination for both videos and comments

**Deliverable**: Complete YouTube search analysis orchestration service.

### **Task 4.2: FastAPI Endpoints**
**Steps for Cursor Agent**:
1. Edit `app/main.py`
2. Copy TikTok/Instagram main.py structure 
3. Create one main endpoint:
   - `POST /analyze-youtube-search` → `search_service.analyze_youtube_search()`
4. Add authentication, rate limiting, and error handling
5. Include comprehensive API documentation
6. Use correct request model: `YouTubeSearchAnalysisRequest`

**Deliverable**: Complete FastAPI application with YouTube search endpoint.

---

## 🧪 **Testing & Deployment** (Week 8)

### **Task 5.1: Basic Testing**
**Steps for Cursor Agent**:
1. Create test file `tests/test_youtube_endpoints.py`
2. Test the search endpoint with sample data
3. Verify error handling
4. Test rate limiting

### **Task 5.2: Environment Setup**
**Steps for Cursor Agent**:
1. Create `.env` file with real API keys
2. Test with actual YouTube138 API
3. Verify OpenAI integration
4. Test end-to-end analysis

### **Task 5.3: Deployment Preparation**
**Steps for Cursor Agent**:
1. Create `Dockerfile` (copy from TikTok/Instagram projects)
2. Update `README.md` with YouTube-specific instructions
3. Test deployment locally
4. Prepare for Railway deployment

---

## 🔄 **Implementation Strategy for Cursor Agent**

### **Recommended Order**:
1. **Start with Phase 1** - Get basic structure working
2. **Test each component individually** - Don't wait until the end
3. **Use mock data initially** - Test without API calls first  
4. **Gradual integration** - Add real API calls once structure works
5. **Iterative testing** - Test each phase before moving to next

### **Key Success Factors**:
- **Reuse 80% from TikTok/Instagram APIs** - Copy working patterns
- **Test incrementally** - Don't build everything then test
- **Start simple** - Basic functionality first, advanced features later
- **Handle errors gracefully** - YouTube API can be unreliable

**This plan gives you narrow, focused tasks perfect for Cursor agent mode. Each task has clear deliverables and can be implemented independently.**
