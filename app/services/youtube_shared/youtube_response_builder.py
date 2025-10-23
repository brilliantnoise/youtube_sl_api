"""
YouTube Response Builder Service
Builds comprehensive API responses from analysis data with metadata and statistics.
"""

import logging
from typing import Dict, List, Any, Optional
from collections import Counter
from datetime import datetime

from app.models.youtube_schemas import (
    YouTubeUnifiedAnalysisResponse,
    YouTubeAnalysisItem,
    YouTubeAnalysisMetadata
)

logger = logging.getLogger(__name__)


class YouTubeResponseBuilder:
    """Service for building comprehensive YouTube analysis responses."""
    
    @staticmethod
    def build_unified_response(
        analyses: List[Dict[str, Any]],
        videos_analyzed: int,
        comments_found: int,
        processing_time: float,
        model_used: str,
        youtube_api_usage: Dict[str, Any],
        openai_api_usage: Dict[str, Any],
        youtube_specific_data: Optional[Dict[str, Any]] = None
    ) -> YouTubeUnifiedAnalysisResponse:
        """
        Build a unified YouTube analysis response.
        
        Args:
            analyses: List of analysis items (YouTubeAnalysisItem dicts)
            videos_analyzed: Total number of videos analyzed
            comments_found: Total number of comments found
            processing_time: Processing time in seconds
            model_used: OpenAI model used for analysis
            youtube_api_usage: YouTube API usage statistics
            openai_api_usage: OpenAI API usage statistics
            youtube_specific_data: Optional YouTube-specific metadata
            
        Returns:
            YouTubeUnifiedAnalysisResponse Pydantic model instance
        """
        logger.info(f"Building unified response with {len(analyses)} analysis items")
        
        # Calculate distributions
        sentiment_dist = YouTubeResponseBuilder._calculate_sentiment_distribution(analyses)
        purchase_intent_dist = YouTubeResponseBuilder._calculate_purchase_intent_distribution(analyses)
        top_themes = YouTubeResponseBuilder._calculate_top_themes(analyses)
        
        # Merge YouTube-specific statistics
        youtube_specific = youtube_specific_data.copy() if youtube_specific_data else {}
        if youtube_specific_data:
            youtube_specific.update(
                YouTubeResponseBuilder._calculate_youtube_specific_stats(
                    analyses, 
                    youtube_specific_data
                )
            )
        
        # Build metadata as Pydantic model
        metadata = YouTubeAnalysisMetadata(
            total_videos_analyzed=videos_analyzed,
            total_comments_found=comments_found,
            relevant_insights_extracted=len(analyses),
            processing_time_seconds=round(processing_time, 2),
            model_used=model_used,
            youtube_api_usage=youtube_api_usage,
            openai_api_usage=openai_api_usage,
            sentiment_distribution=sentiment_dist,
            purchase_intent_distribution=purchase_intent_dist,
            top_themes=top_themes,
            youtube_specific=youtube_specific
        )
        
        # Convert analyses to Pydantic models
        analysis_items = [YouTubeAnalysisItem(**analysis) for analysis in analyses]
        
        # Build response as Pydantic model
        response = YouTubeUnifiedAnalysisResponse(
            comment_analyses=analysis_items,
            metadata=metadata
        )
        
        logger.info(
            f"Response built: {len(analyses)} insights, "
            f"{sentiment_dist.get('positive', 0)} positive, "
            f"{sentiment_dist.get('negative', 0)} negative, "
            f"{purchase_intent_dist.get('high', 0)} high intent"
        )
        
        return response
    
    @staticmethod
    def _calculate_sentiment_distribution(analyses: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Calculate sentiment distribution from analyses.
        
        Args:
            analyses: List of analysis items
            
        Returns:
            Dictionary with counts for each sentiment
        """
        sentiments = [a.get("sentiment", "neutral").lower() for a in analyses]
        counter = Counter(sentiments)
        
        return {
            "positive": counter.get("positive", 0),
            "negative": counter.get("negative", 0),
            "neutral": counter.get("neutral", 0)
        }
    
    @staticmethod
    def _calculate_purchase_intent_distribution(analyses: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Calculate purchase intent distribution from analyses.
        
        Args:
            analyses: List of analysis items
            
        Returns:
            Dictionary with counts for each intent level
        """
        intents = [a.get("purchase_intent", "none").lower() for a in analyses]
        counter = Counter(intents)
        
        return {
            "high": counter.get("high", 0),
            "medium": counter.get("medium", 0),
            "low": counter.get("low", 0),
            "none": counter.get("none", 0)
        }
    
    @staticmethod
    def _calculate_top_themes(analyses: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Calculate top themes from analyses.
        
        Args:
            analyses: List of analysis items
            limit: Maximum number of themes to return
            
        Returns:
            List of theme dictionaries with counts and examples
        """
        themes = [a.get("theme", "general") for a in analyses]
        counter = Counter(themes)
        
        # Build theme objects with examples
        theme_objects = []
        for theme, count in counter.most_common(limit):
            # Find examples for this theme
            examples = [
                a.get("quote", "")[:100] + ("..." if len(a.get("quote", "")) > 100 else "")
                for a in analyses 
                if a.get("theme") == theme
            ][:3]  # Limit to 3 examples per theme
            
            # Calculate average confidence for this theme
            confidences = [
                a.get("confidence_score", 0.0) 
                for a in analyses 
                if a.get("theme") == theme
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            theme_objects.append({
                "theme": theme,
                "count": count,
                "percentage": round((count / len(analyses) * 100), 2) if analyses else 0,
                "average_confidence": round(avg_confidence, 3),
                "examples": examples
            })
        
        return theme_objects
    
    @staticmethod
    def _calculate_youtube_specific_stats(
        analyses: List[Dict[str, Any]],
        youtube_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate YouTube-specific statistics.
        
        Args:
            analyses: List of analysis items
            youtube_data: YouTube-specific data from videos/comments
            
        Returns:
            Dictionary with YouTube-specific statistics
        """
        stats = {}
        
        # Source type distribution
        source_types = [a.get("source_type", "comment") for a in analyses]
        source_counter = Counter(source_types)
        stats["source_distribution"] = {
            "video_titles": source_counter.get("video_title", 0),
            "video_descriptions": source_counter.get("video_description", 0),
            "comments": source_counter.get("comment", 0)
        }
        
        # Video statistics
        if analyses:
            # Unique videos with insights
            unique_videos = len(set(a.get("video_id") for a in analyses if a.get("video_id")))
            stats["unique_videos_with_insights"] = unique_videos
            
            # Average views on videos with insights
            view_counts = [a.get("video_view_count", 0) for a in analyses]
            stats["average_views_per_video"] = round(sum(view_counts) / len(view_counts)) if view_counts else 0
            
            # Live video insights
            live_insights = sum(1 for a in analyses if a.get("video_is_live", False))
            stats["insights_from_live_videos"] = live_insights
            
            # Duration analysis
            durations = [a.get("video_duration_seconds", 0) for a in analyses if a.get("video_duration_seconds")]
            if durations:
                stats["average_video_duration_seconds"] = round(sum(durations) / len(durations))
                stats["average_video_duration_formatted"] = YouTubeResponseBuilder._format_duration(
                    stats["average_video_duration_seconds"]
                )
            
            # Comment engagement statistics (only for comment sources)
            comment_analyses = [a for a in analyses if a.get("source_type") == "comment"]
            if comment_analyses:
                comment_likes = [a.get("comment_like_count", 0) for a in comment_analyses]
                comment_replies = [a.get("comment_reply_count", 0) for a in comment_analyses]
                
                stats["comment_engagement"] = {
                    "average_likes": round(sum(comment_likes) / len(comment_likes)) if comment_likes else 0,
                    "average_replies": round(sum(comment_replies) / len(comment_replies)) if comment_replies else 0,
                    "total_comment_likes": sum(comment_likes),
                    "total_comment_replies": sum(comment_replies)
                }
        
        # Add any additional YouTube-specific data passed in
        if youtube_data:
            stats["additional_metrics"] = youtube_data
        
        return stats
    
    @staticmethod
    def _format_duration(seconds: int) -> str:
        """
        Format duration from seconds to HH:MM:SS or MM:SS.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        if not seconds or seconds <= 0:
            return "0:00"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    @staticmethod
    def build_error_response(
        error_message: str,
        error_code: str = "ANALYSIS_ERROR",
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build an error response.
        
        Args:
            error_message: Error message
            error_code: Error code
            details: Optional error details
            
        Returns:
            Error response dictionary
        """
        return {
            "error": error_code,
            "message": error_message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def calculate_insights_summary(analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate a high-level summary of insights.
        
        Args:
            analyses: List of analysis items
            
        Returns:
            Dictionary with summary statistics
        """
        if not analyses:
            return {
                "total_insights": 0,
                "overall_sentiment": "neutral",
                "overall_purchase_intent": "none",
                "key_findings": []
            }
        
        # Calculate overall sentiment (weighted by confidence)
        sentiment_scores = {
            "positive": sum(
                a.get("confidence_score", 0) 
                for a in analyses 
                if a.get("sentiment") == "positive"
            ),
            "negative": sum(
                a.get("confidence_score", 0) 
                for a in analyses 
                if a.get("sentiment") == "negative"
            ),
            "neutral": sum(
                a.get("confidence_score", 0) 
                for a in analyses 
                if a.get("sentiment") == "neutral"
            )
        }
        overall_sentiment = max(sentiment_scores, key=sentiment_scores.get)
        
        # Calculate overall purchase intent (weighted by confidence)
        intent_scores = {
            "high": sum(
                a.get("confidence_score", 0) 
                for a in analyses 
                if a.get("purchase_intent") == "high"
            ),
            "medium": sum(
                a.get("confidence_score", 0) 
                for a in analyses 
                if a.get("purchase_intent") == "medium"
            ),
            "low": sum(
                a.get("confidence_score", 0) 
                for a in analyses 
                if a.get("purchase_intent") == "low"
            ),
            "none": sum(
                a.get("confidence_score", 0) 
                for a in analyses 
                if a.get("purchase_intent") == "none"
            )
        }
        overall_purchase_intent = max(intent_scores, key=intent_scores.get)
        
        # Get top insights by confidence
        top_insights = sorted(
            analyses, 
            key=lambda a: a.get("confidence_score", 0), 
            reverse=True
        )[:5]
        
        key_findings = [
            {
                "quote": insight.get("quote", "")[:150] + ("..." if len(insight.get("quote", "")) > 150 else ""),
                "theme": insight.get("theme", ""),
                "sentiment": insight.get("sentiment", ""),
                "purchase_intent": insight.get("purchase_intent", ""),
                "confidence": insight.get("confidence_score", 0)
            }
            for insight in top_insights
        ]
        
        return {
            "total_insights": len(analyses),
            "overall_sentiment": overall_sentiment,
            "overall_purchase_intent": overall_purchase_intent,
            "average_confidence": round(
                sum(a.get("confidence_score", 0) for a in analyses) / len(analyses), 
                3
            ),
            "key_findings": key_findings
        }
    
    @staticmethod
    def filter_analyses_by_criteria(
        analyses: List[Dict[str, Any]],
        min_confidence: Optional[float] = None,
        sentiment_filter: Optional[List[str]] = None,
        purchase_intent_filter: Optional[List[str]] = None,
        theme_filter: Optional[List[str]] = None,
        source_type_filter: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter analyses based on various criteria.
        
        Args:
            analyses: List of analysis items
            min_confidence: Minimum confidence score (0.0-1.0)
            sentiment_filter: List of sentiments to include
            purchase_intent_filter: List of purchase intents to include
            theme_filter: List of themes to include
            source_type_filter: List of source types to include
            
        Returns:
            Filtered list of analysis items
        """
        filtered = analyses
        
        if min_confidence is not None:
            filtered = [a for a in filtered if a.get("confidence_score", 0) >= min_confidence]
        
        if sentiment_filter:
            filtered = [a for a in filtered if a.get("sentiment") in sentiment_filter]
        
        if purchase_intent_filter:
            filtered = [a for a in filtered if a.get("purchase_intent") in purchase_intent_filter]
        
        if theme_filter:
            filtered = [a for a in filtered if a.get("theme") in theme_filter]
        
        if source_type_filter:
            filtered = [a for a in filtered if a.get("source_type") in source_type_filter]
        
        logger.info(f"Filtered {len(analyses)} analyses to {len(filtered)} based on criteria")
        return filtered
    
    @staticmethod
    def group_analyses_by_video(analyses: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group analyses by video ID.
        
        Args:
            analyses: List of analysis items
            
        Returns:
            Dictionary mapping video_id to list of analyses
        """
        grouped = {}
        for analysis in analyses:
            video_id = analysis.get("video_id")
            if video_id:
                if video_id not in grouped:
                    grouped[video_id] = []
                grouped[video_id].append(analysis)
        
        return grouped
    
    @staticmethod
    def group_analyses_by_theme(analyses: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group analyses by theme.
        
        Args:
            analyses: List of analysis items
            
        Returns:
            Dictionary mapping theme to list of analyses
        """
        grouped = {}
        for analysis in analyses:
            theme = analysis.get("theme", "general")
            if theme not in grouped:
                grouped[theme] = []
            grouped[theme].append(analysis)
        
        return grouped
