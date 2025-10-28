"""
YouTube Social Media Analysis API
Main FastAPI application with endpoints for YouTube search analysis.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Security, status, Request
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.exceptions import (
    YouTubeAPIException,
    YouTubeValidationError,
    YouTubeDataCollectionError,
    YouTubeAnalysisError,
    RateLimitExceededError,
    AuthenticationError
)
from app.models.youtube_schemas import (
    YouTubeSearchAnalysisRequest,
    YouTubeUnifiedAnalysisResponse
)
from app.services.youtube_search.search_service import YouTubeSearchAnalysisService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# API Key security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("=" * 60)
    logger.info("Starting YouTube Social Media Analysis API")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"API Version: {settings.API_VERSION}")
    logger.info(f"Port: {settings.PORT}")
    logger.info(f"Default Model: {settings.DEFAULT_MODEL}")
    logger.info(f"Max Videos Per Request: {settings.MAX_VIDEOS_PER_REQUEST}")
    logger.info(f"Max Comments Per Video: {settings.MAX_COMMENTS_PER_VIDEO}")
    logger.info(f"YouTube API Key: {'✓ SET' if settings.YOUTUBE_RAPIDAPI_KEY else '✗ MISSING'}")
    logger.info(f"OpenAI API Key: {'✓ SET' if settings.OPENAI_API_KEY else '✗ MISSING'}")
    logger.info(f"Service API Key: {'✓ SET' if settings.SERVICE_API_KEY else '✗ MISSING'}")
    logger.info("=" * 60)
    logger.info("✅ API Ready!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down YouTube Social Media Analysis API")


# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="""
    YouTube Social Listening API for analyzing video content and comments.
    
    ## Features
    - 🔍 **Search Videos**: Search YouTube by keyword
    - 💬 **Analyze Comments**: Collect and analyze top comments
    - 🤖 **AI Insights**: Sentiment, themes, and purchase intent analysis
    - 📊 **Rich Metadata**: Comprehensive statistics and source tracking
    
    ## Authentication
    All endpoints require an API key via the `X-API-Key` header.
    
    ## Rate Limits
    - 10 requests per minute per IP address
    - Configurable limits for videos and comments
    
    ## Endpoints
    - `POST /analyze-youtube-search` - Analyze YouTube search results
    - `GET /health` - Health check
    - `GET /` - API information
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== Security ==========

def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify API key.
    
    Args:
        api_key: API key from header
        
    Returns:
        API key if valid
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Please provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if api_key != settings.SERVICE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key


# ========== Exception Handlers ==========

@app.exception_handler(YouTubeAPIException)
async def youtube_exception_handler(request: Request, exc: YouTubeAPIException):
    """Handle YouTube API exceptions."""
    logger.error(f"YouTube API Exception: {exc.error_code} - {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.exception_handler(YouTubeValidationError)
async def validation_error_handler(request: Request, exc: YouTubeValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation Error: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.exception_handler(YouTubeDataCollectionError)
async def data_collection_error_handler(request: Request, exc: YouTubeDataCollectionError):
    """Handle data collection errors."""
    logger.error(f"Data Collection Error: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.exception_handler(YouTubeAnalysisError)
async def analysis_error_handler(request: Request, exc: YouTubeAnalysisError):
    """Handle analysis errors."""
    logger.error(f"Analysis Error: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.exception_handler(RateLimitExceededError)
async def rate_limit_error_handler(request: Request, exc: RateLimitExceededError):
    """Handle rate limit errors."""
    logger.warning(f"Rate Limit Exceeded: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.exception_handler(AuthenticationError)
async def auth_error_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors."""
    logger.warning(f"Authentication Error: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
            "details": {}
        }
    )


# ========== Endpoints ==========

@app.get("/", tags=["Info"])
async def root() -> Dict[str, Any]:
    """
    API information and status.
    
    Returns general information about the API, version, and capabilities.
    """
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "operational",
        "environment": settings.ENVIRONMENT,
        "endpoints": {
            "analyze": "/analyze-youtube-search",
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "features": [
            "YouTube video search",
            "Comment collection and analysis",
            "AI-powered sentiment analysis",
            "Theme identification",
            "Purchase intent detection",
            "Full source tracking"
        ],
        "limits": {
            "max_videos_per_request": settings.MAX_VIDEOS_PER_REQUEST,
            "default_videos_per_request": settings.DEFAULT_VIDEOS_PER_REQUEST,
            "max_comments_per_video": settings.MAX_COMMENTS_PER_VIDEO
        }
    }


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.
    
    Returns the health status of the API. Useful for monitoring and load balancers.
    """
    return {
        "status": "healthy",
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.post(
    "/analyze-youtube-search",
    response_model=YouTubeUnifiedAnalysisResponse,
    tags=["Analysis"],
    summary="Analyze YouTube Search Results",
    description="""
    Search YouTube for videos and analyze the content and comments for sentiment, 
    themes, and purchase intent.
    
    ## Process
    1. Searches YouTube for videos matching your query
    2. Collects top comments from each video
    3. Analyzes content using AI (OpenAI)
    4. Returns insights with full source tracking
    
    ## Parameters
    - **query**: Search term (e.g., "iPhone 15 review")
    - **max_videos**: Number of videos to analyze (1-50, default: 20)
    - **max_comments_per_video**: Comments per video (10-100, default: 50)
    - **language**: Language code (default: "en")
    - **region**: Region code (default: "US")
    - **ai_analysis_prompt**: Custom AI instructions (optional)
    - **model**: OpenAI model (optional, default from config)
    - **max_quote_length**: Max quote length (50-500, default: 200)
    
    ## Response
    Returns analyzed insights with:
    - Sentiment classification (positive/negative/neutral)
    - Theme identification
    - Purchase intent (high/medium/low/none)
    - Full source tracking (video URLs, comment URLs)
    - Comprehensive metadata and statistics
    
    ## Rate Limits
    - 10 requests per minute per IP
    - Recommended: Start with 5-10 videos for faster results
    
    ## Cost
    - YouTube API: ~$0.00 (free tier available)
    - OpenAI: ~$0.05 per video analyzed (GPT-4)
    """,
    responses={
        200: {
            "description": "Successful analysis",
            "content": {
                "application/json": {
                    "example": {
                        "comment_analyses": [
                            {
                                "quote": "This iPhone 15 is amazing!",
                                "sentiment": "positive",
                                "theme": "product satisfaction",
                                "purchase_intent": "high",
                                "confidence_score": 0.92,
                                "source_type": "comment",
                                "video_url": "https://www.youtube.com/watch?v=...",
                                "comment_url": "https://www.youtube.com/watch?v=...&lc=...",
                                "video_title": "iPhone 15 Pro Review",
                                "quote_author_name": "TechLover123",
                                "comment_like_count": 342
                            }
                        ],
                        "metadata": {
                            "total_videos_analyzed": 20,
                            "total_comments_found": 847,
                            "relevant_insights_extracted": 156,
                            "processing_time_seconds": 45.3,
                            "sentiment_distribution": {
                                "positive": 98,
                                "negative": 23,
                                "neutral": 35
                            }
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid request parameters"},
        401: {"description": "Missing or invalid API key"},
        429: {"description": "Rate limit exceeded"},
        502: {"description": "YouTube API error"},
        503: {"description": "AI analysis error"}
    }
)
@limiter.limit("10/minute")
async def analyze_youtube_search(
    request: Request,
    analysis_request: YouTubeSearchAnalysisRequest,
    api_key: str = Security(verify_api_key)
) -> YouTubeUnifiedAnalysisResponse:
    """
    Analyze YouTube search results for sentiment, themes, and purchase intent.
    
    This endpoint orchestrates the complete analysis pipeline:
    1. Search YouTube for videos
    2. Collect comments from videos
    3. Clean and normalize data
    4. Analyze with AI
    5. Return structured insights
    """
    logger.info(
        f"Received analysis request: query='{analysis_request.query}', "
        f"max_videos={analysis_request.max_videos}, "
        f"max_comments={analysis_request.max_comments_per_video}"
    )
    
    try:
        # Initialize service
        service = YouTubeSearchAnalysisService()
        
        # Run analysis
        result = await service.analyze_youtube_search(
            query=analysis_request.query,
            max_videos=analysis_request.max_videos,
            max_comments_per_video=analysis_request.max_comments_per_video,
            language=analysis_request.language,
            region=analysis_request.region,
            ai_analysis_prompt=analysis_request.ai_analysis_prompt,
            model=analysis_request.model,
            max_quote_length=analysis_request.max_quote_length
        )
        
        logger.info(
            f"Analysis complete: {result.metadata.relevant_insights_extracted} "
            f"insights from {result.metadata.total_videos_analyzed} videos "
            f"in {result.metadata.processing_time_seconds}s"
        )
        
        return result
    
    except YouTubeValidationError as e:
        logger.warning(f"Validation error: {e.message}")
        raise
    
    except YouTubeDataCollectionError as e:
        logger.error(f"Data collection error: {e.message}")
        raise
    
    except YouTubeAnalysisError as e:
        logger.error(f"Analysis error: {e.message}")
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error in analysis endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during analysis"
        )


# ========== Development/Debug Endpoints ==========

if settings.ENVIRONMENT == "development":
    
    @app.get("/debug/config", tags=["Debug"])
    async def debug_config(api_key: str = Security(verify_api_key)) -> Dict[str, Any]:
        """
        Get current configuration (development only).
        
        Returns sanitized configuration for debugging.
        """
        return {
            "api_title": settings.API_TITLE,
            "api_version": settings.API_VERSION,
            "environment": settings.ENVIRONMENT,
            "youtube_api": {
                "host": settings.YOUTUBE_RAPIDAPI_HOST,
                "base_url": settings.YOUTUBE_BASE_URL,
                "request_delay": settings.YOUTUBE_REQUEST_DELAY
            },
            "openai": {
                "model": settings.DEFAULT_MODEL
            },
            "limits": {
                "max_videos_per_request": settings.MAX_VIDEOS_PER_REQUEST,
                "default_videos_per_request": settings.DEFAULT_VIDEOS_PER_REQUEST,
                "max_comments_per_video": settings.MAX_COMMENTS_PER_VIDEO,
                "request_timeout": settings.REQUEST_TIMEOUT
            },
            "server": {
                "port": settings.PORT
            }
        }


# Run the application
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )
