"""
YouTube AI Analyzer Service
Analyzes YouTube videos and comments using OpenAI for sentiment, themes, and purchase intent.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.exceptions import YouTubeAnalysisError

logger = logging.getLogger(__name__)


class YouTubeAIAnalyzer:
    """Service for AI-powered analysis of YouTube content and comments."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the AI analyzer.
        
        Args:
            api_key: OpenAI API key (uses settings if not provided)
            model: OpenAI model to use (uses settings if not provided)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.DEFAULT_MODEL
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Track usage
        self.total_analyses = 0
        self.total_tokens_used = 0
        self.total_cost_usd = 0.0
        
        logger.info(f"YouTube AI Analyzer initialized with model: {self.model}")
    
    def _build_analysis_prompt(
        self,
        video: Dict[str, Any],
        comments: List[Dict[str, Any]],
        custom_instructions: str,
        max_quote_length: int = 200
    ) -> str:
        """
        Build comprehensive analysis prompt for a video and its comments.
        
        Args:
            video: Cleaned video object
            comments: List of cleaned comment objects
            custom_instructions: User's custom analysis instructions
            max_quote_length: Maximum length for extracted quotes
            
        Returns:
            Formatted prompt string
        """
        # Build video context
        video_context = f"""
VIDEO INFORMATION:
- Title: {video.get('title', 'Unknown')}
- Channel: {video.get('channel_name', 'Unknown')}
- Views: {video.get('view_count', 0):,}
- Duration: {video.get('duration_formatted', 'Unknown')}
- Published: {video.get('published_time', 'Unknown')}
- Is Live: {video.get('is_live', False)}
- Description: {video.get('description', 'No description')[:300]}
"""
        
        # Build comments context
        comments_text = []
        for idx, comment in enumerate(comments[:100], 1):  # Limit to top 100 comments
            author_badge = " [Channel Owner]" if comment.get('is_channel_owner') else ""
            heart = " ❤️" if comment.get('has_creator_heart') else ""
            pinned = " 📌" if comment.get('is_pinned') else ""
            
            comments_text.append(
                f"{idx}. {comment.get('author_name', 'Unknown')}{author_badge}{heart}{pinned} "
                f"({comment.get('like_count', 0)} likes, {comment.get('reply_count', 0)} replies): "
                f"{comment.get('text', '')}"
            )
        
        comments_context = "\n".join(comments_text) if comments_text else "No comments available"
        
        # Build the full prompt
        prompt = f"""You are analyzing YouTube video content and comments for sentiment, themes, and purchase intent.

{video_context}

TOP COMMENTS ({len(comments)} total):
{comments_context}

ANALYSIS TASK:
{custom_instructions}

INSTRUCTIONS:
1. Analyze the video title, description, and comments
2. Extract relevant quotes that demonstrate sentiment, themes, or purchase intent
3. For each quote, provide:
   - The exact quote (max {max_quote_length} characters)
   - Sentiment: positive, negative, or neutral
   - Theme: main topic or category (e.g., "product quality", "price concerns", "features", "comparison", etc.)
   - Purchase intent: high, medium, low, or none
   - Confidence score: 0.0 to 1.0
   - Source type: "video_title", "video_description", or "comment"
   - Comment index (if from comment): the number from the comment list above

4. Focus on quotes that provide meaningful insights about the video topic
5. Prioritize comments with high engagement (likes, replies) when selecting quotes
6. Consider YouTube-specific context:
   - Video view count and popularity
   - Channel owner responses (marked with [Channel Owner])
   - Creator hearts (❤️) and pinned comments (📌)
   - Video duration and format (live vs recorded)

Return your analysis as a JSON array of quote objects with this exact structure:
[
  {{
    "quote": "exact quote text (max {max_quote_length} chars)",
    "sentiment": "positive|negative|neutral",
    "theme": "theme name",
    "purchase_intent": "high|medium|low|none",
    "confidence_score": 0.85,
    "source_type": "video_title|video_description|comment",
    "comment_index": 1
  }}
]

Return ONLY the JSON array, no additional text.
"""
        return prompt
    
    def _extract_quote_metadata(
        self,
        analysis_item: Dict[str, Any],
        video: Dict[str, Any],
        comments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract full metadata for an analyzed quote.
        
        Args:
            analysis_item: AI analysis result for one quote
            video: Cleaned video object
            comments: List of cleaned comment objects
            
        Returns:
            Complete analysis item with all metadata
        """
        source_type = analysis_item.get("source_type", "comment")
        video_id = video.get("video_id", "")
        video_url = video.get("video_url", f"https://www.youtube.com/watch?v={video_id}")
        
        # Base metadata (common to all sources)
        metadata = {
            "quote": analysis_item.get("quote", ""),
            "sentiment": analysis_item.get("sentiment", "neutral"),
            "theme": analysis_item.get("theme", "general"),
            "purchase_intent": analysis_item.get("purchase_intent", "none"),
            "confidence_score": float(analysis_item.get("confidence_score", 0.5)),
            
            # Source identification
            "source_type": source_type,
            "video_id": video_id,
            "video_url": video_url,
            "video_title": video.get("title", ""),
            "video_author_channel": video.get("channel_name", ""),
            
            # Video metadata
            "video_view_count": video.get("view_count", 0),
            "video_duration_seconds": video.get("duration_seconds"),
            "video_published_time": video.get("published_time"),
            "video_is_live": video.get("is_live", False),
        }
        
        # Add source-specific metadata
        if source_type == "comment":
            comment_index = analysis_item.get("comment_index", 1) - 1  # Convert to 0-based
            
            if 0 <= comment_index < len(comments):
                comment = comments[comment_index]
                comment_id = comment.get("comment_id", "")
                
                metadata.update({
                    "quote_author_name": comment.get("author_name", "Unknown"),
                    "quote_author_channel_id": comment.get("author_channel_id"),
                    "comment_id": comment_id,
                    "comment_url": f"{video_url}&lc={comment_id}" if comment_id else video_url,
                    "comment_like_count": comment.get("like_count", 0),
                    "comment_reply_count": comment.get("reply_count", 0),
                    "comment_published_time": comment.get("published_time"),
                })
            else:
                # Comment index out of range, use defaults
                logger.warning(f"Comment index {comment_index} out of range for video {video_id}")
                metadata.update({
                    "quote_author_name": "Unknown",
                    "quote_author_channel_id": None,
                    "comment_id": None,
                    "comment_url": None,
                    "comment_like_count": 0,
                    "comment_reply_count": 0,
                    "comment_published_time": None,
                })
        
        elif source_type in ["video_title", "video_description"]:
            # Quote is from video itself, author is channel owner
            metadata.update({
                "quote_author_name": video.get("channel_name", "Unknown"),
                "quote_author_channel_id": video.get("channel_id"),
                "comment_id": None,
                "comment_url": None,
                "comment_like_count": None,
                "comment_reply_count": None,
                "comment_published_time": None,
            })
        
        return metadata
    
    async def analyze_video_with_comments(
        self,
        video: Dict[str, Any],
        comments: List[Dict[str, Any]],
        custom_instructions: str = "Analyze sentiment, themes, and purchase intent",
        max_quote_length: int = 200
    ) -> Dict[str, Any]:
        """
        Analyze a single video with its comments.
        
        Args:
            video: Cleaned video object
            comments: List of cleaned comment objects
            custom_instructions: Custom analysis instructions
            max_quote_length: Maximum quote length
            
        Returns:
            Dictionary with analysis results and metadata
        """
        video_id = video.get("video_id", "unknown")
        
        try:
            logger.info(
                f"Analyzing video {video_id} with {len(comments)} comments "
                f"using model {self.model}"
            )
            
            # Build prompt
            prompt = self._build_analysis_prompt(
                video, comments, custom_instructions, max_quote_length
            )
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing YouTube content and comments for sentiment, themes, and purchase intent. You return structured JSON data."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent analysis
                response_format={"type": "json_object"}
            )
            
            # Extract response
            content = response.choices[0].message.content
            
            # Track usage
            self.total_analyses += 1
            if response.usage:
                tokens_used = response.usage.total_tokens
                self.total_tokens_used += tokens_used
                
                # Estimate cost (approximate rates for GPT-4)
                # Input: ~$0.01/1K tokens, Output: ~$0.03/1K tokens
                input_cost = (response.usage.prompt_tokens / 1000) * 0.01
                output_cost = (response.usage.completion_tokens / 1000) * 0.03
                cost = input_cost + output_cost
                self.total_cost_usd += cost
            else:
                tokens_used = 0
                cost = 0.0
            
            # Parse JSON response
            try:
                parsed = json.loads(content)
                
                # Handle different response formats
                if isinstance(parsed, dict):
                    # Check if response has an "analyses" or similar key
                    if "analyses" in parsed:
                        analyses = parsed["analyses"]
                    elif "quotes" in parsed:
                        analyses = parsed["quotes"]
                    elif "results" in parsed:
                        analyses = parsed["results"]
                    else:
                        # Assume the dict has a list somewhere, try to find it
                        for value in parsed.values():
                            if isinstance(value, list):
                                analyses = value
                                break
                        else:
                            # No list found, wrap in list
                            analyses = [parsed]
                elif isinstance(parsed, list):
                    analyses = parsed
                else:
                    analyses = []
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI response as JSON: {e}")
                logger.debug(f"Response content: {content[:500]}")
                analyses = []
            
            # Extract full metadata for each analysis item
            enriched_analyses = []
            for item in analyses:
                try:
                    enriched = self._extract_quote_metadata(item, video, comments)
                    enriched_analyses.append(enriched)
                except Exception as e:
                    logger.error(f"Error enriching analysis item: {e}")
                    continue
            
            logger.info(
                f"Analysis complete for video {video_id}: "
                f"{len(enriched_analyses)} insights extracted "
                f"({tokens_used} tokens, ${cost:.4f})"
            )
            
            return {
                "video_id": video_id,
                "analyses": enriched_analyses,
                "metadata": {
                    "model": self.model,
                    "tokens_used": tokens_used,
                    "cost_usd": round(cost, 4),
                    "analysis_time": datetime.utcnow().isoformat(),
                }
            }
        
        except Exception as e:
            logger.error(f"Error analyzing video {video_id}: {str(e)}")
            raise YouTubeAnalysisError(
                f"Failed to analyze video: {str(e)}",
                model=self.model,
                video_id=video_id
            )
    
    async def analyze_videos_with_comments(
        self,
        videos_with_comments: List[Dict[str, Any]],
        custom_instructions: str = "Analyze sentiment, themes, and purchase intent",
        max_quote_length: int = 200,
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze multiple videos with their comments.
        
        Args:
            videos_with_comments: List of dicts with 'video' and 'comments' keys
            custom_instructions: Custom analysis instructions
            max_quote_length: Maximum quote length
            max_concurrent: Maximum concurrent API calls
            
        Returns:
            Dictionary with all analyses and aggregate metadata
        """
        logger.info(
            f"Starting analysis of {len(videos_with_comments)} videos "
            f"(max {max_concurrent} concurrent)"
        )
        
        start_time = datetime.utcnow()
        
        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_with_semaphore(item: Dict[str, Any]) -> Dict[str, Any]:
            """Analyze with concurrency control."""
            async with semaphore:
                return await self.analyze_video_with_comments(
                    video=item.get("video", {}),
                    comments=item.get("comments", []),
                    custom_instructions=custom_instructions,
                    max_quote_length=max_quote_length
                )
        
        # Analyze all videos concurrently (with rate limiting)
        results = await asyncio.gather(
            *[analyze_with_semaphore(item) for item in videos_with_comments],
            return_exceptions=True
        )
        
        # Process results
        all_analyses = []
        successful_analyses = 0
        failed_analyses = 0
        errors = []
        
        for result in results:
            if isinstance(result, Exception):
                failed_analyses += 1
                errors.append(str(result))
                logger.error(f"Analysis failed: {result}")
            else:
                successful_analyses += 1
                all_analyses.extend(result.get("analyses", []))
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        logger.info(
            f"Batch analysis complete: {successful_analyses} successful, "
            f"{failed_analyses} failed, {len(all_analyses)} total insights "
            f"in {processing_time:.2f}s"
        )
        
        return {
            "analyses": all_analyses,
            "metadata": {
                "total_videos_analyzed": len(videos_with_comments),
                "successful_analyses": successful_analyses,
                "failed_analyses": failed_analyses,
                "total_insights_extracted": len(all_analyses),
                "processing_time_seconds": round(processing_time, 2),
                "model_used": self.model,
                "total_tokens_used": self.total_tokens_used,
                "total_cost_usd": round(self.total_cost_usd, 4),
                "errors": errors
            }
        }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get API usage statistics.
        
        Returns:
            Dictionary with usage stats
        """
        return {
            "total_analyses": self.total_analyses,
            "total_tokens_used": self.total_tokens_used,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "model": self.model,
            "average_tokens_per_analysis": round(
                self.total_tokens_used / self.total_analyses
            ) if self.total_analyses > 0 else 0
        }
    
    def reset_stats(self):
        """Reset usage statistics."""
        self.total_analyses = 0
        self.total_tokens_used = 0
        self.total_cost_usd = 0.0
        logger.info("AI analyzer usage statistics reset")
