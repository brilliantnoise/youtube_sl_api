"""
YouTube Comment Collector Service
Collects comments for multiple videos with batch processing and error handling.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.services.youtube_shared.youtube_api_client import YouTubeAPIClient
from app.core.exceptions import YouTubeDataCollectionError

logger = logging.getLogger(__name__)


class YouTubeCommentCollector:
    """Service for collecting comments from multiple YouTube videos."""
    
    def __init__(self, api_client: Optional[YouTubeAPIClient] = None):
        """
        Initialize the comment collector.
        
        Args:
            api_client: YouTube API client instance (creates new one if not provided)
        """
        self.api_client = api_client or YouTubeAPIClient()
        logger.info("YouTube Comment Collector initialized")
    
    async def collect_all_comments(
        self,
        videos: List[Dict[str, Any]],
        max_comments_per_video: int,
        language: str = "en",
        region: str = "US"
    ) -> Dict[str, Any]:
        """
        Collect comments for multiple videos.
        
        Args:
            videos: List of video objects (must have 'video_id' or 'videoId' field)
            max_comments_per_video: Maximum comments to collect per video
            language: Language code for API requests
            region: Region code for API requests
            
        Returns:
            Dictionary with structure:
            {
                "comments_by_video": {
                    "video_id_1": [list of comment objects],
                    "video_id_2": [list of comment objects],
                    ...
                },
                "metadata": {
                    "total_videos_processed": int,
                    "total_comments_collected": int,
                    "videos_with_comments": int,
                    "videos_without_comments": int,
                    "api_calls_made": int,
                    "processing_time_seconds": float,
                    "errors": [list of error details]
                }
            }
        """
        start_time = datetime.now()
        
        logger.info(
            f"Starting comment collection for {len(videos)} videos "
            f"({max_comments_per_video} max per video)"
        )
        
        comments_by_video = {}
        total_comments = 0
        videos_with_comments = 0
        videos_without_comments = 0
        errors = []
        api_calls_before = self.api_client.api_calls
        
        # Process each video sequentially (rate limiting is handled by api_client)
        for idx, video in enumerate(videos, 1):
            # Support both raw videos (videoId) and cleaned videos (video_id)
            video_id = video.get("video_id") or video.get("videoId")
            
            if not video_id:
                logger.warning(f"Video at index {idx} missing 'video_id' or 'videoId', skipping")
                errors.append({
                    "video_index": idx,
                    "error": "Missing video_id/videoId field",
                    "video_data": str(video)[:100]
                })
                videos_without_comments += 1
                continue
            
            try:
                logger.info(
                    f"Collecting comments for video {idx}/{len(videos)}: {video_id}"
                )
                
                # Use batch method to handle pagination automatically
                comments = await self.api_client.get_video_comments_batch(
                    video_id=video_id,
                    max_comments=max_comments_per_video,
                    hl=language,
                    gl=region
                )
                
                # Store comments for this video
                comments_by_video[video_id] = comments
                total_comments += len(comments)
                
                if comments:
                    videos_with_comments += 1
                    logger.info(
                        f"Collected {len(comments)} comments for video {video_id}"
                    )
                else:
                    videos_without_comments += 1
                    logger.info(
                        f"No comments found for video {video_id} "
                        "(comments may be disabled)"
                    )
            
            except YouTubeDataCollectionError as e:
                logger.error(
                    f"Error collecting comments for video {video_id}: {e.message}"
                )
                videos_without_comments += 1
                comments_by_video[video_id] = []
                errors.append({
                    "video_id": video_id,
                    "video_index": idx,
                    "error": e.message,
                    "error_code": e.error_code
                })
            
            except Exception as e:
                logger.error(
                    f"Unexpected error collecting comments for video {video_id}: {str(e)}"
                )
                videos_without_comments += 1
                comments_by_video[video_id] = []
                errors.append({
                    "video_id": video_id,
                    "video_index": idx,
                    "error": str(e),
                    "error_type": type(e).__name__
                })
        
        # Calculate metadata
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        api_calls_made = self.api_client.api_calls - api_calls_before
        
        metadata = {
            "total_videos_processed": len(videos),
            "total_comments_collected": total_comments,
            "videos_with_comments": videos_with_comments,
            "videos_without_comments": videos_without_comments,
            "api_calls_made": api_calls_made,
            "processing_time_seconds": round(processing_time, 2),
            "average_comments_per_video": round(
                total_comments / len(videos), 2
            ) if videos else 0,
            "errors": errors
        }
        
        logger.info(
            f"Comment collection complete: "
            f"{total_comments} comments from {videos_with_comments}/{len(videos)} videos "
            f"in {processing_time:.2f}s ({api_calls_made} API calls)"
        )
        
        return {
            "comments_by_video": comments_by_video,
            "metadata": metadata
        }
    
    async def collect_comments_for_video(
        self,
        video_id: str,
        max_comments: int,
        language: str = "en",
        region: str = "US"
    ) -> Dict[str, Any]:
        """
        Collect comments for a single video.
        
        Args:
            video_id: YouTube video ID
            max_comments: Maximum comments to collect
            language: Language code
            region: Region code
            
        Returns:
            Dictionary with structure:
            {
                "video_id": str,
                "comments": [list of comment objects],
                "total_comments_collected": int,
                "has_more": bool,
                "error": Optional[str]
            }
        """
        logger.info(f"Collecting up to {max_comments} comments for video {video_id}")
        
        try:
            comments = await self.api_client.get_video_comments_batch(
                video_id=video_id,
                max_comments=max_comments,
                hl=language,
                gl=region
            )
            
            return {
                "video_id": video_id,
                "comments": comments,
                "total_comments_collected": len(comments),
                "has_more": len(comments) >= max_comments,
                "error": None
            }
        
        except YouTubeDataCollectionError as e:
            logger.error(f"Error collecting comments for video {video_id}: {e.message}")
            return {
                "video_id": video_id,
                "comments": [],
                "total_comments_collected": 0,
                "has_more": False,
                "error": e.message
            }
        
        except Exception as e:
            logger.error(
                f"Unexpected error collecting comments for video {video_id}: {str(e)}"
            )
            return {
                "video_id": video_id,
                "comments": [],
                "total_comments_collected": 0,
                "has_more": False,
                "error": str(e)
            }
    
    async def collect_comments_parallel(
        self,
        videos: List[Dict[str, Any]],
        max_comments_per_video: int,
        language: str = "en",
        region: str = "US",
        max_concurrent: int = 3
    ) -> Dict[str, Any]:
        """
        Collect comments for multiple videos using parallel requests.
        
        Note: Use with caution as this may trigger rate limits faster.
        Sequential collection is recommended for most use cases.
        
        Args:
            videos: List of video objects
            max_comments_per_video: Maximum comments per video
            language: Language code
            region: Region code
            max_concurrent: Maximum concurrent requests (default: 3)
            
        Returns:
            Same structure as collect_all_comments()
        """
        start_time = datetime.now()
        
        logger.info(
            f"Starting parallel comment collection for {len(videos)} videos "
            f"(max {max_concurrent} concurrent)"
        )
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def collect_with_semaphore(video: Dict[str, Any]) -> tuple:
            """Collect comments with concurrency control."""
            async with semaphore:
                video_id = video.get("videoId")
                if not video_id:
                    return video_id, [], {"error": "Missing videoId"}
                
                try:
                    comments = await self.api_client.get_video_comments_batch(
                        video_id=video_id,
                        max_comments=max_comments_per_video,
                        hl=language,
                        gl=region
                    )
                    return video_id, comments, None
                
                except Exception as e:
                    logger.error(f"Error for video {video_id}: {str(e)}")
                    return video_id, [], {"error": str(e)}
        
        # Gather all results
        api_calls_before = self.api_client.api_calls
        results = await asyncio.gather(
            *[collect_with_semaphore(video) for video in videos],
            return_exceptions=True
        )
        
        # Process results
        comments_by_video = {}
        total_comments = 0
        videos_with_comments = 0
        videos_without_comments = 0
        errors = []
        
        for result in results:
            if isinstance(result, Exception):
                errors.append({"error": str(result)})
                continue
            
            video_id, comments, error = result
            
            if video_id:
                comments_by_video[video_id] = comments
                total_comments += len(comments)
                
                if comments:
                    videos_with_comments += 1
                else:
                    videos_without_comments += 1
                
                if error:
                    errors.append({"video_id": video_id, **error})
        
        # Calculate metadata
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        api_calls_made = self.api_client.api_calls - api_calls_before
        
        metadata = {
            "total_videos_processed": len(videos),
            "total_comments_collected": total_comments,
            "videos_with_comments": videos_with_comments,
            "videos_without_comments": videos_without_comments,
            "api_calls_made": api_calls_made,
            "processing_time_seconds": round(processing_time, 2),
            "average_comments_per_video": round(
                total_comments / len(videos), 2
            ) if videos else 0,
            "errors": errors,
            "collection_mode": "parallel",
            "max_concurrent": max_concurrent
        }
        
        logger.info(
            f"Parallel comment collection complete: "
            f"{total_comments} comments from {videos_with_comments}/{len(videos)} videos "
            f"in {processing_time:.2f}s"
        )
        
        return {
            "comments_by_video": comments_by_video,
            "metadata": metadata
        }
    
    def get_api_usage_stats(self) -> Dict[str, Any]:
        """
        Get API usage statistics from the underlying client.
        
        Returns:
            Dictionary with API usage stats
        """
        return self.api_client.get_api_usage_stats()
