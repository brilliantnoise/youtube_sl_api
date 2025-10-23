"""
YouTube API Client for YouTube138 RapidAPI
Handles video search and comment collection with rate limiting and error handling.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime

from app.core.config import settings
from app.core.exceptions import (
    YouTubeDataCollectionError,
    RateLimitExceededError,
    AuthenticationError
)

logger = logging.getLogger(__name__)


class YouTubeAPIClient:
    """Client for YouTube138 RapidAPI endpoints."""
    
    def __init__(self):
        """Initialize the YouTube API client."""
        self.base_url = settings.YOUTUBE_BASE_URL
        self.headers = {
            "x-rapidapi-key": settings.YOUTUBE_RAPIDAPI_KEY,
            "x-rapidapi-host": settings.YOUTUBE_RAPIDAPI_HOST
        }
        self.request_delay = settings.YOUTUBE_REQUEST_DELAY
        self.timeout = settings.REQUEST_TIMEOUT
        
        # Track API usage
        self.api_calls = 0
        self.last_request_time = None
        
        logger.info(f"YouTube API Client initialized with base URL: {self.base_url}")
    
    async def _make_request(
        self, 
        endpoint: str, 
        params: Dict[str, Any],
        method: str = "GET"
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the YouTube API with rate limiting and error handling.
        
        Args:
            endpoint: API endpoint path (e.g., "/search/")
            params: Query parameters
            method: HTTP method (default: GET)
            
        Returns:
            API response as dictionary
            
        Raises:
            YouTubeDataCollectionError: On API errors
            RateLimitExceededError: On rate limit exceeded
            AuthenticationError: On authentication errors
        """
        # Rate limiting: wait if needed
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < self.request_delay:
                wait_time = self.request_delay - elapsed
                logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"API Request: {method} {endpoint} with params: {params}")
                
                if method == "GET":
                    response = await client.get(url, headers=self.headers, params=params)
                else:
                    response = await client.request(
                        method, url, headers=self.headers, params=params
                    )
                
                # Update tracking
                self.api_calls += 1
                self.last_request_time = datetime.now()
                
                # Handle response status codes
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"API Response: Success ({len(str(data))} bytes)")
                    return data
                
                elif response.status_code == 401:
                    raise AuthenticationError(
                        "Invalid or missing RapidAPI key",
                        auth_type="rapidapi"
                    )
                
                elif response.status_code == 403:
                    raise AuthenticationError(
                        "Access forbidden - check API key permissions",
                        auth_type="rapidapi"
                    )
                
                elif response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", 60)
                    raise RateLimitExceededError(
                        "YouTube API rate limit exceeded",
                        service="YouTube138 RapidAPI",
                        retry_after=int(retry_after)
                    )
                
                elif response.status_code == 404:
                    raise YouTubeDataCollectionError(
                        f"Endpoint not found: {endpoint}",
                        api_endpoint=endpoint,
                        http_status=404
                    )
                
                else:
                    raise YouTubeDataCollectionError(
                        f"YouTube API error: {response.status_code} - {response.text[:200]}",
                        api_endpoint=endpoint,
                        http_status=response.status_code
                    )
        
        except httpx.TimeoutException as e:
            logger.error(f"Request timeout for {endpoint}: {str(e)}")
            raise YouTubeDataCollectionError(
                f"Request timeout after {self.timeout} seconds",
                api_endpoint=endpoint
            )
        
        except httpx.RequestError as e:
            logger.error(f"Request error for {endpoint}: {str(e)}")
            raise YouTubeDataCollectionError(
                f"Network error: {str(e)}",
                api_endpoint=endpoint
            )
        
        except Exception as e:
            if isinstance(e, (YouTubeDataCollectionError, RateLimitExceededError, AuthenticationError)):
                raise
            logger.error(f"Unexpected error for {endpoint}: {str(e)}")
            raise YouTubeDataCollectionError(
                f"Unexpected error: {str(e)}",
                api_endpoint=endpoint
            )
    
    async def search_videos(
        self,
        query: str,
        hl: str = "en",
        gl: str = "US",
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for YouTube videos by query.
        
        Args:
            query: Search query string
            hl: Language code (default: "en")
            gl: Region/country code (default: "US")
            cursor: Pagination cursor from previous response (optional)
            
        Returns:
            Dictionary with structure:
            {
                "contents": [list of video objects],
                "cursorNext": "pagination cursor",
                "estimatedResults": int,
                "refinements": [list of suggested refinements]
            }
            
        Raises:
            YouTubeDataCollectionError: On API errors
        """
        params = {
            "q": query,
            "hl": hl,
            "gl": gl
        }
        
        # Add cursor for pagination if provided
        if cursor:
            params["cursor"] = cursor
        
        logger.info(f"Searching videos for query: '{query}' (hl={hl}, gl={gl})")
        
        try:
            response = await self._make_request("/search/", params)
            
            # Validate response structure
            if not isinstance(response, dict):
                raise YouTubeDataCollectionError(
                    "Invalid response format from YouTube API",
                    api_endpoint="/search/"
                )
            
            # Extract contents (videos are in the "contents" array)
            contents = response.get("contents", [])
            cursor_next = response.get("cursorNext")
            estimated_results = response.get("estimatedResults", 0)
            
            logger.info(
                f"Search results: {len(contents)} videos, "
                f"estimated total: {estimated_results}, "
                f"has_more: {bool(cursor_next)}"
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error searching videos: {str(e)}")
            raise
    
    async def get_video_comments(
        self,
        video_id: str,
        hl: str = "en",
        gl: str = "US",
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comments for a YouTube video.
        
        Args:
            video_id: YouTube video ID
            hl: Language code (default: "en")
            gl: Region/country code (default: "US")
            cursor: Pagination cursor from previous response (optional)
            
        Returns:
            Dictionary with structure:
            {
                "comments": [list of comment objects],
                "cursorNext": "pagination cursor",
                "totalCommentsCount": int,
                "filters": [list of filter options]
            }
            
        Raises:
            YouTubeDataCollectionError: On API errors
        """
        params = {
            "id": video_id,
            "hl": hl,
            "gl": gl
        }
        
        # Add cursor for pagination if provided
        if cursor:
            params["cursor"] = cursor
        
        logger.info(f"Fetching comments for video: {video_id} (hl={hl}, gl={gl})")
        
        try:
            response = await self._make_request("/video/comments/", params)
            
            # Validate response structure
            if not isinstance(response, dict):
                raise YouTubeDataCollectionError(
                    "Invalid response format from YouTube API",
                    api_endpoint="/video/comments/"
                )
            
            # Extract comments
            comments = response.get("comments", [])
            cursor_next = response.get("cursorNext")
            total_count = response.get("totalCommentsCount", 0)
            
            logger.info(
                f"Comments fetched: {len(comments)} comments, "
                f"total: {total_count}, "
                f"has_more: {bool(cursor_next)}"
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error fetching comments for video {video_id}: {str(e)}")
            raise
    
    async def search_videos_batch(
        self,
        query: str,
        max_videos: int,
        hl: str = "en",
        gl: str = "US"
    ) -> List[Dict[str, Any]]:
        """
        Search for videos and handle pagination to get desired number of results.
        
        Args:
            query: Search query
            max_videos: Maximum number of videos to retrieve
            hl: Language code
            gl: Region code
            
        Returns:
            List of video objects
        """
        all_videos = []
        cursor = None
        
        logger.info(f"Starting batch search for {max_videos} videos")
        
        while len(all_videos) < max_videos:
            response = await self.search_videos(query, hl, gl, cursor)
            videos = response.get("contents", [])
            
            if not videos:
                logger.warning("No more videos available")
                break
            
            # Add videos up to max_videos limit
            remaining = max_videos - len(all_videos)
            all_videos.extend(videos[:remaining])
            
            # Check if we have more pages
            cursor = response.get("cursorNext")
            if not cursor or len(all_videos) >= max_videos:
                break
            
            logger.info(f"Fetched {len(all_videos)}/{max_videos} videos, continuing...")
        
        logger.info(f"Batch search complete: {len(all_videos)} videos retrieved")
        return all_videos
    
    async def get_video_comments_batch(
        self,
        video_id: str,
        max_comments: int,
        hl: str = "en",
        gl: str = "US"
    ) -> List[Dict[str, Any]]:
        """
        Get comments for a video and handle pagination.
        
        Args:
            video_id: YouTube video ID
            max_comments: Maximum number of comments to retrieve
            hl: Language code
            gl: Region code
            
        Returns:
            List of comment objects
        """
        all_comments = []
        cursor = None
        
        logger.info(f"Starting batch comment fetch for video {video_id} ({max_comments} max)")
        
        while len(all_comments) < max_comments:
            try:
                response = await self.get_video_comments(video_id, hl, gl, cursor)
                comments = response.get("comments", [])
                
                if not comments:
                    logger.info(f"No more comments available for video {video_id}")
                    break
                
                # Add comments up to max_comments limit
                remaining = max_comments - len(all_comments)
                all_comments.extend(comments[:remaining])
                
                # Check if we have more pages
                cursor = response.get("cursorNext")
                if not cursor or len(all_comments) >= max_comments:
                    break
                
                logger.debug(f"Fetched {len(all_comments)}/{max_comments} comments, continuing...")
            
            except YouTubeDataCollectionError as e:
                # Some videos may have comments disabled
                logger.warning(f"Could not fetch comments for video {video_id}: {e.message}")
                break
        
        logger.info(f"Batch comment fetch complete: {len(all_comments)} comments for video {video_id}")
        return all_comments
    
    def get_api_usage_stats(self) -> Dict[str, Any]:
        """
        Get statistics about API usage.
        
        Returns:
            Dictionary with API usage statistics
        """
        return {
            "total_api_calls": self.api_calls,
            "base_url": self.base_url,
            "request_delay": self.request_delay,
            "timeout": self.timeout
        }
    
    def reset_stats(self):
        """Reset API usage statistics."""
        self.api_calls = 0
        self.last_request_time = None
        logger.info("API usage statistics reset")
