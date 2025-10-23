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
