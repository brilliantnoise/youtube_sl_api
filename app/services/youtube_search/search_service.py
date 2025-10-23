"""
YouTube Search Analysis Service
Orchestrates the complete pipeline: search → collect → clean → analyze → build response
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.services.youtube_shared.youtube_api_client import YouTubeAPIClient
from app.services.youtube_shared.youtube_comment_collector import YouTubeCommentCollector
from app.services.youtube_shared.youtube_data_cleaners import YouTubeDataCleaner
from app.services.youtube_shared.youtube_ai_analyzer import YouTubeAIAnalyzer
from app.services.youtube_shared.youtube_response_builder import YouTubeResponseBuilder
from app.core.config import settings
from app.core.exceptions import (
    YouTubeDataCollectionError,
    YouTubeAnalysisError,
    YouTubeValidationError
)

logger = logging.getLogger(__name__)


class YouTubeSearchAnalysisService:
    """
    Orchestrates the complete YouTube search analysis pipeline.
    
    Pipeline stages:
    1. Search Videos: Query YouTube API for relevant videos
    2. Clean Data: Normalize video data
    3. Collect & Clean Comments: Gather and clean comments for each video
    4. AI Analysis: Analyze content with OpenAI
    5. Build Response: Create comprehensive response with metadata
    """
    
    def __init__(
        self,
        api_client: Optional[YouTubeAPIClient] = None,
        comment_collector: Optional[YouTubeCommentCollector] = None,
        ai_analyzer: Optional[YouTubeAIAnalyzer] = None
    ):
        """
        Initialize the search analysis service.
        
        Args:
            api_client: YouTube API client (creates new if not provided)
            comment_collector: Comment collector (creates new if not provided)
            ai_analyzer: AI analyzer (creates new if not provided)
        """
        self.api_client = api_client or YouTubeAPIClient()
        self.comment_collector = comment_collector or YouTubeCommentCollector(self.api_client)
        self.ai_analyzer = ai_analyzer or YouTubeAIAnalyzer()
        
        logger.info("YouTube Search Analysis Service initialized")
    
    async def analyze_youtube_search(
        self,
        query: str,
        max_videos: int = 20,
        max_comments_per_video: int = 50,
        language: str = "en",
        region: str = "US",
        ai_analysis_prompt: str = "Analyze sentiment, themes, and purchase intent",
        model: str = None,
        max_quote_length: int = 200
    ) -> Dict[str, Any]:
        """
        Complete YouTube search analysis pipeline.
        
        Args:
            query: Search query for YouTube videos
            max_videos: Maximum number of videos to analyze
            max_comments_per_video: Maximum comments per video
            language: Language code (e.g., 'en', 'es')
            region: Region code (e.g., 'US', 'UK')
            ai_analysis_prompt: Custom AI analysis instructions
            model: OpenAI model to use (uses default if not provided)
            max_quote_length: Maximum length for extracted quotes
            
        Returns:
            Complete analysis response with metadata
            
        Raises:
            YouTubeValidationError: Invalid input parameters
            YouTubeDataCollectionError: Error collecting YouTube data
            YouTubeAnalysisError: Error during AI analysis
        """
        start_time = datetime.utcnow()
        
        # Validate inputs
        self._validate_inputs(query, max_videos, max_comments_per_video)
        
        logger.info(
            f"Starting YouTube search analysis: query='{query}', "
            f"max_videos={max_videos}, max_comments={max_comments_per_video}, "
            f"language={language}, region={region}"
        )
        
        try:
            # ========== STAGE 1: Search Videos ==========
            logger.info("=" * 60)
            logger.info("Stage 1: Searching for videos")
            logger.info(f"Query: {query}, Max Videos: {max_videos}, Language: {language}, Region: {region}")
            stage1_start = datetime.utcnow()
            
            try:
                raw_videos = await self._search_videos(
                    query, max_videos, language, region
                )
                logger.info(f"✅ Stage 1: Successfully fetched raw videos")
            except Exception as e:
                logger.error(f"❌ Stage 1 FAILED: {type(e).__name__}: {str(e)}")
                raise
            
            stage1_time = (datetime.utcnow() - stage1_start).total_seconds()
            logger.info(
                f"Stage 1 complete: {len(raw_videos)} videos found "
                f"in {stage1_time:.2f}s"
            )
            logger.info("=" * 60)
            
            if not raw_videos:
                logger.warning("No videos found for query")
                return self._build_empty_response(
                    query, "No videos found for the search query"
                )
            
            # ========== STAGE 2: Clean Video Data ==========
            logger.info("=" * 60)
            logger.info("Stage 2: Cleaning video data")
            logger.info(f"Input: {len(raw_videos)} raw videos")
            stage2_start = datetime.utcnow()
            
            try:
                cleaned_videos = YouTubeDataCleaner.clean_youtube_videos(raw_videos)
                logger.info(f"✅ Stage 2: Successfully cleaned videos")
            except Exception as e:
                logger.error(f"❌ Stage 2 FAILED: {type(e).__name__}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                raise
            
            stage2_time = (datetime.utcnow() - stage2_start).total_seconds()
            logger.info(
                f"Stage 2 complete: {len(cleaned_videos)} videos cleaned "
                f"in {stage2_time:.2f}s"
            )
            logger.info("=" * 60)
            
            if not cleaned_videos:
                logger.warning("No valid videos after cleaning")
                return self._build_empty_response(
                    query, "No valid videos after data cleaning"
                )
            
            # ========== STAGE 3: Collect & Clean Comments ==========
            logger.info("=" * 60)
            logger.info("Stage 3: Collecting and cleaning comments")
            logger.info(f"Processing {len(cleaned_videos)} cleaned videos")
            stage3_start = datetime.utcnow()
            
            try:
                # Collect comments for all videos (using cleaned_videos instead of raw_videos)
                logger.info("  → Collecting comments...")
                comment_collection_result = await self.comment_collector.collect_all_comments(
                    videos=cleaned_videos,  # FIX: Use cleaned_videos instead of raw_videos
                    max_comments_per_video=max_comments_per_video,
                    language=language,
                    region=region
                )
                logger.info(f"  ✅ Comments collected")
            except Exception as e:
                logger.error(f"❌ Stage 3 (comment collection) FAILED: {type(e).__name__}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                raise
            
            comments_by_video = comment_collection_result["comments_by_video"]
            comment_metadata = comment_collection_result["metadata"]
            
            # Clean all comments
            cleaned_comments_by_video = {}
            total_cleaned_comments = 0
            
            try:
                logger.info("  → Cleaning comments...")
                for video_id, raw_comments in comments_by_video.items():
                    cleaned_comments = YouTubeDataCleaner.clean_youtube_comments(raw_comments)
                    cleaned_comments_by_video[video_id] = cleaned_comments
                    total_cleaned_comments += len(cleaned_comments)
                logger.info(f"  ✅ Comments cleaned")
            except Exception as e:
                logger.error(f"❌ Stage 3 (comment cleaning) FAILED: {type(e).__name__}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                raise
            
            stage3_time = (datetime.utcnow() - stage3_start).total_seconds()
            logger.info(
                f"Stage 3 complete: {total_cleaned_comments} comments cleaned "
                f"from {len(cleaned_comments_by_video)} videos "
                f"in {stage3_time:.2f}s"
            )
            logger.info("=" * 60)
            
            # ========== STAGE 4: AI Analysis ==========
            logger.info("=" * 60)
            logger.info("Stage 4: AI analysis of content and comments")
            stage4_start = datetime.utcnow()
            
            try:
                # Prepare data for AI analysis (pair videos with their comments)
                logger.info("  → Preparing data for AI analysis...")
                videos_with_comments = []
                for cleaned_video in cleaned_videos:
                    video_id = cleaned_video.get("video_id")
                    video_comments = cleaned_comments_by_video.get(video_id, [])
                    
                    videos_with_comments.append({
                        "video": cleaned_video,
                        "comments": video_comments
                    })
                
                logger.info(f"  → Prepared {len(videos_with_comments)} videos with comments for AI")
                logger.info(f"  → Calling AI analyzer...")
                
                # Analyze with AI
                analysis_result = await self.ai_analyzer.analyze_videos_with_comments(
                    videos_with_comments=videos_with_comments,
                    custom_instructions=ai_analysis_prompt,
                    max_quote_length=max_quote_length,
                    max_concurrent=5  # Process 5 videos concurrently
                )
                
                logger.info(f"  ✅ AI analysis complete")
            except Exception as e:
                logger.error(f"❌ Stage 4 FAILED: {type(e).__name__}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                raise
            
            analyses = analysis_result["analyses"]
            ai_metadata = analysis_result["metadata"]
            
            stage4_time = (datetime.utcnow() - stage4_start).total_seconds()
            logger.info(
                f"Stage 4 complete: {len(analyses)} insights extracted "
                f"in {stage4_time:.2f}s"
            )
            logger.info("=" * 60)
            
            # ========== STAGE 5: Build Final Response ==========
            logger.info("=" * 60)
            logger.info("Stage 5: Building final response")
            logger.info(f"  → Building response from {len(analyses)} analyses")
            stage5_start = datetime.utcnow()
            
            total_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Gather YouTube API usage
            youtube_api_usage = {
                "total_api_calls": self.api_client.api_calls,
                "search_calls": 1,  # At least one search call
                "comment_calls": comment_metadata.get("api_calls_made", 0),
                "request_delay": self.api_client.request_delay,
                "timeout": self.api_client.timeout
            }
            
            # Gather OpenAI API usage
            openai_api_usage = {
                "total_tokens": ai_metadata.get("total_tokens_used", 0),
                "total_cost_usd": ai_metadata.get("total_cost_usd", 0.0),
                "model": ai_metadata.get("model_used", model or settings.DEFAULT_MODEL),
                "successful_analyses": ai_metadata.get("successful_analyses", 0),
                "failed_analyses": ai_metadata.get("failed_analyses", 0)
            }
            
            # Prepare YouTube-specific data
            youtube_specific = {
                "search_query": query,
                "language": language,
                "region": region,
                "videos_found": len(raw_videos),
                "videos_cleaned": len(cleaned_videos),
                "total_comments_collected": comment_metadata.get("total_comments_collected", 0),
                "videos_with_comments": comment_metadata.get("videos_with_comments", 0),
                "videos_without_comments": comment_metadata.get("videos_without_comments", 0),
                "comment_collection_errors": len(comment_metadata.get("errors", [])),
                "pipeline_stages": {
                    "stage1_search_time": round(stage1_time, 2),
                    "stage2_clean_time": round(stage2_time, 2),
                    "stage3_comments_time": round(stage3_time, 2),
                    "stage4_analysis_time": round(stage4_time, 2),
                    "stage5_build_time": round(
                        (datetime.utcnow() - stage5_start).total_seconds(), 2
                    )
                }
            }
            
            # Build unified response
            try:
                logger.info("  → Calling response builder...")
                response = YouTubeResponseBuilder.build_unified_response(
                    analyses=analyses,
                    videos_analyzed=len(cleaned_videos),
                    comments_found=total_cleaned_comments,
                    processing_time=total_time,
                    model_used=ai_metadata.get("model_used", model or settings.DEFAULT_MODEL),
                    youtube_api_usage=youtube_api_usage,
                    openai_api_usage=openai_api_usage,
                    youtube_specific_data=youtube_specific
                )
                logger.info("  ✅ Response built successfully")
            except Exception as e:
                logger.error(f"❌ Stage 5 (response building) FAILED: {type(e).__name__}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                raise
            
            stage5_time = (datetime.utcnow() - stage5_start).total_seconds()
            logger.info(
                f"Stage 5 complete: Response built in {stage5_time:.2f}s"
            )
            logger.info("=" * 60)
            
            logger.info("🎉" * 30)
            logger.info(
                f"✅ Analysis pipeline complete: {len(analyses)} insights from "
                f"{len(cleaned_videos)} videos in {total_time:.2f}s total"
            )
            logger.info("🎉" * 30)
            
            return response
        
        except YouTubeDataCollectionError as e:
            logger.error(f"❌ Data collection error: {e.message}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        
        except YouTubeAnalysisError as e:
            logger.error(f"❌ Analysis error: {e.message}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        
        except Exception as e:
            logger.error(f"❌ Unexpected error in analysis pipeline: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise YouTubeAnalysisError(
                f"Analysis pipeline failed: {str(e)}"
            )
    
    async def _search_videos(
        self,
        query: str,
        max_videos: int,
        language: str,
        region: str
    ) -> List[Dict[str, Any]]:
        """
        Search for videos using the YouTube API.
        
        Args:
            query: Search query
            max_videos: Maximum videos to retrieve
            language: Language code
            region: Region code
            
        Returns:
            List of raw video objects
        """
        try:
            videos = await self.api_client.search_videos_batch(
                query=query,
                max_videos=max_videos,
                hl=language,
                gl=region
            )
            
            logger.info(f"Retrieved {len(videos)} videos from YouTube API")
            return videos
        
        except Exception as e:
            logger.error(f"Error searching videos: {str(e)}")
            raise YouTubeDataCollectionError(
                f"Failed to search videos: {str(e)}",
                api_endpoint="/search/"
            )
    
    def _validate_inputs(
        self,
        query: str,
        max_videos: int,
        max_comments_per_video: int
    ):
        """
        Validate input parameters.
        
        Args:
            query: Search query
            max_videos: Maximum videos
            max_comments_per_video: Maximum comments per video
            
        Raises:
            YouTubeValidationError: Invalid parameters
        """
        if not query or not query.strip():
            raise YouTubeValidationError(
                "Search query cannot be empty",
                field="query",
                value=query
            )
        
        if max_videos < 1 or max_videos > settings.MAX_VIDEOS_PER_REQUEST:
            raise YouTubeValidationError(
                f"max_videos must be between 1 and {settings.MAX_VIDEOS_PER_REQUEST}",
                field="max_videos",
                value=max_videos
            )
        
        if max_comments_per_video < 10 or max_comments_per_video > settings.MAX_COMMENTS_PER_VIDEO:
            raise YouTubeValidationError(
                f"max_comments_per_video must be between 10 and {settings.MAX_COMMENTS_PER_VIDEO}",
                field="max_comments_per_video",
                value=max_comments_per_video
            )
    
    def _build_empty_response(
        self,
        query: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        Build an empty response when no data is available.
        
        Args:
            query: Search query
            reason: Reason for empty response
            
        Returns:
            Empty response with metadata
        """
        logger.info(f"Building empty response: {reason}")
        
        return YouTubeResponseBuilder.build_unified_response(
            analyses=[],
            videos_analyzed=0,
            comments_found=0,
            processing_time=0.0,
            model_used=settings.DEFAULT_MODEL,
            youtube_api_usage={
                "total_api_calls": self.api_client.api_calls,
                "search_calls": 1,
                "comment_calls": 0
            },
            openai_api_usage={
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "model": settings.DEFAULT_MODEL
            },
            youtube_specific_data={
                "search_query": query,
                "reason": reason
            }
        )
    
    def get_service_stats(self) -> Dict[str, Any]:
        """
        Get statistics from all services.
        
        Returns:
            Dictionary with service statistics
        """
        return {
            "youtube_api": self.api_client.get_api_usage_stats(),
            "comment_collector": self.comment_collector.get_api_usage_stats(),
            "ai_analyzer": self.ai_analyzer.get_usage_stats()
        }
    
    def reset_stats(self):
        """Reset statistics for all services."""
        self.api_client.reset_stats()
        self.ai_analyzer.reset_stats()
        logger.info("Service statistics reset")
