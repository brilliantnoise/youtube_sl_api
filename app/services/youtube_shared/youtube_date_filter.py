"""
YouTube Date Filter Service
Filters comments by date range using parsed relative dates from YouTube API.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.utils.date_parser import parse_relative_date, is_datetime_in_range

logger = logging.getLogger(__name__)


class YouTubeDateFilter:
    """
    Service for filtering YouTube comments by date range.
    
    YouTube provides relative date strings (e.g., "1 month ago"), which this service
    converts to absolute dates and filters against a specified date range.
    """
    
    def __init__(self):
        """Initialize the date filter service."""
        logger.info("YouTube Date Filter initialized")
    
    def filter_comments_by_date_range(
        self,
        comments_by_video: Dict[str, List[Dict]],
        start_date: datetime,
        end_date: datetime,
        reference_date: datetime
    ) -> Dict[str, Any]:
        """
        Filter comments by date range.
        
        Takes a dictionary of comments grouped by video_id and filters out comments
        that fall outside the specified date range. Comments with unparseable dates
        are logged as warnings and excluded.
        
        Args:
            comments_by_video: Dictionary mapping video_id to list of comment dicts
                Each comment dict should have a 'published_time' field with relative date string
            start_date: Start of date range (inclusive), timezone-aware
            end_date: End of date range (inclusive), timezone-aware
            reference_date: Reference datetime for parsing relative dates (usually current time)
            
        Returns:
            Dictionary with structure:
            {
                "filtered_comments_by_video": {video_id: [filtered_comments]},
                "filter_stats": {
                    "total_comments_before": int,
                    "total_comments_after": int,
                    "comments_filtered_out": int,
                    "comments_unparseable": int,
                    "videos_with_comments": int,
                    "videos_without_comments": int,
                    "videos_total": int,
                    "date_range": {
                        "start": str (ISO format),
                        "end": str (ISO format),
                        "timezone": str
                    }
                }
            }
            
        Example:
            >>> filter_result = date_filter.filter_comments_by_date_range(
            ...     comments_by_video={"video1": [comment1, comment2]},
            ...     start_date=datetime(2024, 1, 1, tzinfo=UTC),
            ...     end_date=datetime(2024, 12, 31, tzinfo=UTC),
            ...     reference_date=datetime.now(UTC)
            ... )
        """
        logger.info(
            f"Starting date filter: {start_date.date()} to {end_date.date()} "
            f"(timezone: {start_date.tzinfo})"
        )
        
        filtered_comments_by_video = {}
        
        # Statistics tracking
        total_comments_before = 0
        total_comments_after = 0
        comments_filtered_out = 0
        comments_unparseable = 0
        videos_with_comments = 0
        videos_without_comments = 0
        
        # Process each video's comments
        for video_id, comments in comments_by_video.items():
            total_comments_before += len(comments)
            
            logger.debug(
                f"Filtering {len(comments)} comments for video {video_id}"
            )
            
            filtered_comments = []
            
            for comment in comments:
                # Check if comment is in date range
                if self._is_comment_in_range(
                    comment=comment,
                    start_date=start_date,
                    end_date=end_date,
                    reference_date=reference_date
                ):
                    filtered_comments.append(comment)
                else:
                    # Check if it was filtered out or unparseable
                    relative_date_str = comment.get("published_time", "")
                    parsed_date = parse_relative_date(relative_date_str, reference_date)
                    
                    if parsed_date is None:
                        comments_unparseable += 1
                        logger.debug(
                            f"Comment {comment.get('comment_id', 'unknown')} has "
                            f"unparseable date: '{relative_date_str}'"
                        )
                    else:
                        comments_filtered_out += 1
                        logger.debug(
                            f"Comment {comment.get('comment_id', 'unknown')} filtered out: "
                            f"'{relative_date_str}' → {parsed_date.date()} (outside range)"
                        )
            
            # Store filtered comments for this video
            filtered_comments_by_video[video_id] = filtered_comments
            total_comments_after += len(filtered_comments)
            
            # Track video statistics
            if len(filtered_comments) > 0:
                videos_with_comments += 1
                logger.debug(
                    f"Video {video_id}: {len(filtered_comments)}/{len(comments)} "
                    f"comments in date range"
                )
            else:
                videos_without_comments += 1
                logger.debug(
                    f"Video {video_id}: No comments in date range "
                    f"(had {len(comments)} total)"
                )
        
        videos_total = len(comments_by_video)
        
        # Build statistics
        filter_stats = {
            "total_comments_before": total_comments_before,
            "total_comments_after": total_comments_after,
            "comments_filtered_out": comments_filtered_out,
            "comments_unparseable": comments_unparseable,
            "videos_with_comments": videos_with_comments,
            "videos_without_comments": videos_without_comments,
            "videos_total": videos_total,
            "date_range": {
                "start": start_date.date().isoformat(),
                "end": end_date.date().isoformat(),
                "timezone": str(start_date.tzinfo)
            }
        }
        
        logger.info(
            f"Date filter complete: {total_comments_before} → {total_comments_after} comments "
            f"({comments_filtered_out} filtered out, {comments_unparseable} unparseable). "
            f"Videos: {videos_with_comments} with comments, {videos_without_comments} without."
        )
        
        if comments_unparseable > 0:
            logger.warning(
                f"{comments_unparseable} comments had unparseable dates and were excluded"
            )
        
        return {
            "filtered_comments_by_video": filtered_comments_by_video,
            "filter_stats": filter_stats
        }
    
    def _is_comment_in_range(
        self,
        comment: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        reference_date: datetime
    ) -> bool:
        """
        Check if a single comment falls within the date range.
        
        Args:
            comment: Comment dictionary with 'published_time' field
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            reference_date: Reference datetime for parsing relative dates
            
        Returns:
            True if comment is in range, False if out of range or unparseable
        """
        # Get relative date string from comment
        relative_date_str = comment.get("published_time", "")
        
        if not relative_date_str:
            logger.warning(
                f"Comment {comment.get('comment_id', 'unknown')} missing 'published_time' field"
            )
            return False
        
        # Parse relative date to absolute date
        parsed_date = parse_relative_date(relative_date_str, reference_date)
        
        if parsed_date is None:
            logger.debug(
                f"Could not parse date '{relative_date_str}' for comment "
                f"{comment.get('comment_id', 'unknown')}"
            )
            return False
        
        # Ensure parsed_date has timezone info
        if parsed_date.tzinfo is None and start_date.tzinfo is not None:
            # If parsed_date is naive but start_date is aware, make parsed_date aware
            parsed_date = start_date.tzinfo.localize(parsed_date)
        elif parsed_date.tzinfo is not None and start_date.tzinfo is None:
            # If parsed_date is aware but start_date is naive, make parsed_date naive
            parsed_date = parsed_date.replace(tzinfo=None)
        
        # Check if date is in range
        in_range = is_datetime_in_range(parsed_date, start_date, end_date)
        
        return in_range
    
    def get_date_filter_summary(
        self,
        filter_stats: Dict[str, Any]
    ) -> str:
        """
        Generate a human-readable summary of date filtering results.
        
        Args:
            filter_stats: Statistics dictionary from filter_comments_by_date_range
            
        Returns:
            Formatted summary string
            
        Example:
            >>> summary = date_filter.get_date_filter_summary(filter_stats)
            >>> print(summary)
            Date Filter Summary:
            - Date Range: 2024-01-01 to 2024-12-31 (UTC)
            - Comments: 100 → 45 (55 filtered out, 0 unparseable)
            - Videos: 10 total (8 with comments, 2 without)
        """
        date_range = filter_stats.get("date_range", {})
        
        summary = (
            f"Date Filter Summary:\n"
            f"- Date Range: {date_range.get('start')} to {date_range.get('end')} "
            f"({date_range.get('timezone', 'UTC')})\n"
            f"- Comments: {filter_stats.get('total_comments_before', 0)} → "
            f"{filter_stats.get('total_comments_after', 0)} "
            f"({filter_stats.get('comments_filtered_out', 0)} filtered out, "
            f"{filter_stats.get('comments_unparseable', 0)} unparseable)\n"
            f"- Videos: {filter_stats.get('videos_total', 0)} total "
            f"({filter_stats.get('videos_with_comments', 0)} with comments, "
            f"{filter_stats.get('videos_without_comments', 0)} without)"
        )
        
        return summary


# Example usage and testing
if __name__ == "__main__":
    import pytz
    from datetime import timedelta
    
    # Setup logging for testing
    logging.basicConfig(level=logging.DEBUG)
    
    print("=" * 70)
    print("Testing YouTube Date Filter Service")
    print("=" * 70)
    
    # Create test data
    reference_date = datetime(2024, 11, 19, 12, 0, 0, tzinfo=pytz.UTC)
    
    # Mock comments with various relative dates
    test_comments_by_video = {
        "video1": [
            {
                "comment_id": "c1",
                "text": "Great video!",
                "published_time": "1 day ago",
                "author_name": "User1"
            },
            {
                "comment_id": "c2",
                "text": "Very helpful",
                "published_time": "1 week ago",
                "author_name": "User2"
            },
            {
                "comment_id": "c3",
                "text": "Thanks!",
                "published_time": "1 month ago",
                "author_name": "User3"
            },
        ],
        "video2": [
            {
                "comment_id": "c4",
                "text": "Amazing!",
                "published_time": "3 days ago",
                "author_name": "User4"
            },
            {
                "comment_id": "c5",
                "text": "Love it",
                "published_time": "6 months ago",
                "author_name": "User5"
            },
        ],
        "video3": [
            {
                "comment_id": "c6",
                "text": "Good stuff",
                "published_time": "1 year ago",
                "author_name": "User6"
            },
        ]
    }
    
    # Test 1: Filter for last 2 weeks
    print("\n" + "=" * 70)
    print("Test 1: Filter for last 2 weeks")
    print("=" * 70)
    
    end_date = reference_date
    start_date = reference_date - timedelta(days=14)
    
    date_filter = YouTubeDateFilter()
    result = date_filter.filter_comments_by_date_range(
        comments_by_video=test_comments_by_video,
        start_date=start_date,
        end_date=end_date,
        reference_date=reference_date
    )
    
    print("\nFiltered Results:")
    for video_id, comments in result["filtered_comments_by_video"].items():
        print(f"  {video_id}: {len(comments)} comments")
        for comment in comments:
            print(f"    - {comment['comment_id']}: {comment['published_time']}")
    
    print("\n" + date_filter.get_date_filter_summary(result["filter_stats"]))
    
    # Test 2: Filter for last 1 month
    print("\n" + "=" * 70)
    print("Test 2: Filter for last 1 month")
    print("=" * 70)
    
    end_date = reference_date
    start_date = reference_date - timedelta(days=30)
    
    result = date_filter.filter_comments_by_date_range(
        comments_by_video=test_comments_by_video,
        start_date=start_date,
        end_date=end_date,
        reference_date=reference_date
    )
    
    print("\nFiltered Results:")
    for video_id, comments in result["filtered_comments_by_video"].items():
        print(f"  {video_id}: {len(comments)} comments")
        for comment in comments:
            print(f"    - {comment['comment_id']}: {comment['published_time']}")
    
    print("\n" + date_filter.get_date_filter_summary(result["filter_stats"]))
    
    # Test 3: Filter with unparseable dates
    print("\n" + "=" * 70)
    print("Test 3: Filter with unparseable/invalid dates")
    print("=" * 70)
    
    test_comments_invalid = {
        "video1": [
            {
                "comment_id": "c1",
                "text": "Valid",
                "published_time": "1 day ago",
                "author_name": "User1"
            },
            {
                "comment_id": "c2",
                "text": "Invalid date",
                "published_time": "sometime in the past",  # Unparseable
                "author_name": "User2"
            },
            {
                "comment_id": "c3",
                "text": "Missing date",
                "published_time": "",  # Empty
                "author_name": "User3"
            },
        ]
    }
    
    result = date_filter.filter_comments_by_date_range(
        comments_by_video=test_comments_invalid,
        start_date=reference_date - timedelta(days=7),
        end_date=reference_date,
        reference_date=reference_date
    )
    
    print("\nFiltered Results:")
    for video_id, comments in result["filtered_comments_by_video"].items():
        print(f"  {video_id}: {len(comments)} comments (out of 3 total)")
    
    print("\n" + date_filter.get_date_filter_summary(result["filter_stats"]))
    
    print("\n" + "=" * 70)
    print("✅ YouTube Date Filter Service Tests Complete")
    print("=" * 70)

