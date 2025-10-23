"""
YouTube Data Cleaners
Normalizes raw YouTube API responses into clean, consistent data structures.
Based on real YouTube138 RapidAPI response formats.
"""

import logging
import re
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class YouTubeDataCleaner:
    """Cleans and normalizes YouTube API response data."""
    
    # Spam detection patterns
    SPAM_PATTERNS = [
        r'(?i)(check out my channel)',
        r'(?i)(subscribe to my channel)',
        r'(?i)(follow me on)',
        r'(?i)(click here)',
        r'(?i)(win free)',
        r'(?i)(make money online)',
        r'(?i)(work from home)',
        r'https?://bit\.ly/',
        r'https?://tinyurl\.com/',
    ]
    
    @staticmethod
    def get_best_thumbnail(thumbnails: List[Dict]) -> str:
        """
        Get highest quality thumbnail URL.
        
        Args:
            thumbnails: List of thumbnail objects with width, height, url
            
        Returns:
            Best quality thumbnail URL or empty string
        """
        if not thumbnails:
            return ""
        
        try:
            # Sort by resolution (width * height) and get the best one
            best_thumbnail = max(
                thumbnails,
                key=lambda t: t.get("width", 0) * t.get("height", 0)
            )
            return best_thumbnail.get("url", "")
        except (TypeError, ValueError) as e:
            logger.warning(f"Error finding best thumbnail: {e}")
            return thumbnails[0].get("url", "") if thumbnails else ""
    
    @staticmethod
    def format_duration(seconds: Optional[int]) -> str:
        """
        Format video duration from seconds to HH:MM:SS or MM:SS.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        if not seconds or seconds <= 0:
            return "Unknown"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    @staticmethod
    def is_likely_spam(text: str) -> bool:
        """
        Check if comment text appears to be spam.
        
        Args:
            text: Comment text to check
            
        Returns:
            True if likely spam, False otherwise
        """
        if not text:
            return False
        
        # Check against spam patterns
        for pattern in YouTubeDataCleaner.SPAM_PATTERNS:
            if re.search(pattern, text):
                return True
        
        # Check for excessive capital letters (>70% uppercase)
        if len(text) > 20:
            uppercase_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if uppercase_ratio > 0.7:
                return True
        
        # Check for excessive emojis/special characters (>50%)
        if len(text) > 10:
            special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
            special_ratio = special_chars / len(text)
            if special_ratio > 0.5:
                return True
        
        return False
    
    @staticmethod
    def calculate_engagement_rate(
        likes: int,
        replies: int,
        views: int = None
    ) -> Optional[float]:
        """
        Calculate engagement rate for a comment or video.
        
        Args:
            likes: Number of likes
            replies: Number of replies
            views: Number of views (optional, for videos)
            
        Returns:
            Engagement rate as percentage or None
        """
        total_engagement = likes + replies
        
        if views and views > 0:
            return round((total_engagement / views) * 100, 4)
        
        return None
    
    @staticmethod
    def clean_youtube_videos(raw_videos: List[Dict]) -> List[Dict]:
        """
        Clean YouTube videos using actual API response structure.
        YouTube138 API returns: {type: "video", video: {...actual video data...}}
        
        Args:
            raw_videos: List of raw video objects from YouTube138 API
            
        Returns:
            List of cleaned video dictionaries
        """
        cleaned_videos = []
        
        logger.info(f"Cleaning {len(raw_videos)} YouTube videos")
        
        for idx, item in enumerate(raw_videos):
            try:
                # YouTube138 API wraps video data in a 'video' key
                if item.get("type") != "video":
                    logger.debug(f"Item at index {idx} is not a video (type: {item.get('type')}), skipping")
                    continue
                    
                video = item.get("video", {})
                if not video:
                    logger.warning(f"Video at index {idx} missing video data, skipping")
                    continue
                
                # Extract required fields
                video_id = video.get("videoId")
                if not video_id:
                    logger.warning(f"Video at index {idx} missing videoId, skipping")
                    continue
                
                # Extract channel/author information
                author = video.get("author", {})
                channel_id = author.get("channelId", "")
                channel_name = author.get("title", "Unknown Channel")
                channel_url = author.get("canonicalBaseUrl", "")
                
                # Extract video metadata
                title = video.get("title", "Untitled Video")
                description = video.get("descriptionSnippet", "")
                duration_seconds = video.get("lengthSeconds")
                published_time = video.get("publishedTimeText", "")
                is_live = video.get("isLiveNow", False)
                
                # Extract statistics
                stats = video.get("stats", {})
                view_count = stats.get("views", 0)
                
                # Extract thumbnails
                thumbnails = video.get("thumbnails", [])
                thumbnail_url = YouTubeDataCleaner.get_best_thumbnail(thumbnails)
                
                # Extract badges
                badges = video.get("badges", [])
                
                # Build cleaned video object
                cleaned_video = {
                    "video_id": video_id,
                    "title": title,
                    "description": description,
                    "video_url": f"https://www.youtube.com/watch?v={video_id}",
                    "duration_seconds": duration_seconds,
                    "duration_formatted": YouTubeDataCleaner.format_duration(duration_seconds),
                    "view_count": view_count,
                    "published_time": published_time,
                    "is_live": is_live,
                    "channel_id": channel_id,
                    "channel_name": channel_name,
                    "channel_url": f"https://www.youtube.com{channel_url}" if channel_url else "",
                    "thumbnail_url": thumbnail_url,
                    "badges": badges,
                    "has_captions": "CC" in badges if badges else False,
                }
                
                cleaned_videos.append(cleaned_video)
            
            except Exception as e:
                logger.error(f"Error cleaning video at index {idx}: {str(e)}")
                continue
        
        logger.info(f"Successfully cleaned {len(cleaned_videos)}/{len(raw_videos)} videos")
        return cleaned_videos
    
    @staticmethod
    def clean_youtube_comments(raw_comments: List[Dict]) -> List[Dict]:
        """
        Clean YouTube comments using actual API response structure.
        
        Args:
            raw_comments: List of raw comment objects from YouTube138 API
            
        Returns:
            List of cleaned comment dictionaries
        """
        cleaned_comments = []
        
        logger.info(f"Cleaning {len(raw_comments)} YouTube comments")
        
        for idx, comment in enumerate(raw_comments):
            try:
                # Extract required fields
                comment_id = comment.get("commentId")
                if not comment_id:
                    logger.warning(f"Comment at index {idx} missing commentId, skipping")
                    continue
                
                # Extract comment content
                text = comment.get("content", "")
                
                # Skip if likely spam
                if YouTubeDataCleaner.is_likely_spam(text):
                    logger.debug(f"Skipping likely spam comment: {comment_id}")
                    continue
                
                # Extract author information
                author = comment.get("author", {})
                author_name = author.get("title", "Unknown User")
                author_channel_id = author.get("channelId", "")
                is_channel_owner = author.get("isChannelOwner", False)
                author_badges = author.get("badges", [])
                
                # Extract statistics
                stats = comment.get("stats", {})
                like_count = stats.get("votes", 0)
                reply_count = stats.get("replies", 0)
                
                # Extract metadata
                published_time = comment.get("publishedTimeText", "")
                has_creator_heart = comment.get("creatorHeart", False)
                
                # Extract pinned status
                pinned = comment.get("pinned", {})
                is_pinned = pinned.get("status", False) if pinned else False
                
                # Calculate engagement score (likes + replies)
                engagement_score = like_count + reply_count
                
                # Build cleaned comment object
                cleaned_comment = {
                    "comment_id": comment_id,
                    "text": text,
                    "author_name": author_name,
                    "author_channel_id": author_channel_id,
                    "author_badges": author_badges if author_badges else [],
                    "like_count": like_count,
                    "reply_count": reply_count,
                    "engagement_score": engagement_score,
                    "published_time": published_time,
                    "is_channel_owner": is_channel_owner,
                    "has_creator_heart": has_creator_heart,
                    "is_pinned": is_pinned,
                    "text_length": len(text),
                }
                
                cleaned_comments.append(cleaned_comment)
            
            except Exception as e:
                logger.error(f"Error cleaning comment at index {idx}: {str(e)}")
                continue
        
        logger.info(
            f"Successfully cleaned {len(cleaned_comments)}/{len(raw_comments)} comments "
            f"(filtered {len(raw_comments) - len(cleaned_comments)} spam/invalid)"
        )
        return cleaned_comments
    
    @staticmethod
    def clean_video_with_comments(
        video: Dict[str, Any],
        comments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Clean a video and its comments together, maintaining relationships.
        
        Args:
            video: Raw video object
            comments: List of raw comment objects for this video
            
        Returns:
            Dictionary with cleaned video and comments
        """
        # Clean video
        cleaned_videos = YouTubeDataCleaner.clean_youtube_videos([video])
        cleaned_video = cleaned_videos[0] if cleaned_videos else None
        
        if not cleaned_video:
            logger.error("Failed to clean video")
            return None
        
        # Clean comments
        cleaned_comments = YouTubeDataCleaner.clean_youtube_comments(comments)
        
        # Add comment statistics to video
        cleaned_video["total_comments"] = len(cleaned_comments)
        cleaned_video["total_comment_likes"] = sum(
            c.get("like_count", 0) for c in cleaned_comments
        )
        cleaned_video["average_comment_length"] = round(
            sum(c.get("text_length", 0) for c in cleaned_comments) / len(cleaned_comments)
        ) if cleaned_comments else 0
        
        return {
            "video": cleaned_video,
            "comments": cleaned_comments,
            "comment_stats": {
                "total": len(cleaned_comments),
                "with_likes": sum(1 for c in cleaned_comments if c.get("like_count", 0) > 0),
                "with_replies": sum(1 for c in cleaned_comments if c.get("reply_count", 0) > 0),
                "from_channel_owner": sum(1 for c in cleaned_comments if c.get("is_channel_owner")),
                "with_creator_heart": sum(1 for c in cleaned_comments if c.get("has_creator_heart")),
                "pinned": sum(1 for c in cleaned_comments if c.get("is_pinned")),
            }
        }
    
    @staticmethod
    def clean_batch(
        videos: List[Dict[str, Any]],
        comments_by_video: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Clean multiple videos and their comments in batch.
        
        Args:
            videos: List of raw video objects
            comments_by_video: Dictionary mapping video_id to comments
            
        Returns:
            List of cleaned video+comments objects
        """
        cleaned_batch = []
        
        logger.info(f"Cleaning batch of {len(videos)} videos with comments")
        
        for video in videos:
            video_id = video.get("videoId")
            if not video_id:
                continue
            
            # Get comments for this video
            video_comments = comments_by_video.get(video_id, [])
            
            # Clean video with comments
            cleaned = YouTubeDataCleaner.clean_video_with_comments(video, video_comments)
            if cleaned:
                cleaned_batch.append(cleaned)
        
        logger.info(f"Successfully cleaned {len(cleaned_batch)} videos with comments")
        return cleaned_batch
    
    @staticmethod
    def extract_video_metadata_summary(cleaned_videos: List[Dict]) -> Dict[str, Any]:
        """
        Extract summary statistics from cleaned videos.
        
        Args:
            cleaned_videos: List of cleaned video objects
            
        Returns:
            Dictionary with summary statistics
        """
        if not cleaned_videos:
            return {
                "total_videos": 0,
                "total_views": 0,
                "average_duration_seconds": 0,
                "live_videos": 0,
                "videos_with_captions": 0
            }
        
        total_views = sum(v.get("view_count", 0) for v in cleaned_videos)
        durations = [v.get("duration_seconds", 0) for v in cleaned_videos if v.get("duration_seconds")]
        
        return {
            "total_videos": len(cleaned_videos),
            "total_views": total_views,
            "average_views": round(total_views / len(cleaned_videos)),
            "average_duration_seconds": round(sum(durations) / len(durations)) if durations else 0,
            "live_videos": sum(1 for v in cleaned_videos if v.get("is_live")),
            "videos_with_captions": sum(1 for v in cleaned_videos if v.get("has_captions")),
            "unique_channels": len(set(v.get("channel_id") for v in cleaned_videos if v.get("channel_id")))
        }
