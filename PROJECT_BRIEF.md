# 🎥 YouTube Social Listening API - Project Brief

## What We're Building

A YouTube social listening API that searches for videos based on keywords and analyzes the sentiment, themes, and purchase intent of both video content and comments. This follows the same proven architecture as our successful TikTok and Instagram APIs.

## Core Functionality

**Single Endpoint**: `/analyze-youtube-search`

**User Flow**:
1. User provides a search query (e.g., "iPhone 15 review")
2. System searches YouTube for relevant videos
3. For each video, we collect the title, description, and top comments
4. AI analyzes all content for sentiment, themes, and purchase intent
5. Return structured insights with full source tracking

## Key Features

**Content Analysis**:
- Video titles and descriptions
- Top comments from each video (user-configurable limit)
- Sentiment classification (positive, negative, neutral)
- Theme identification (product satisfaction, price concerns, etc.)
- Purchase intent detection (high, medium, low, none)

**Source Tracking**:
- Every analyzed quote links back to its source
- Video quotes link to the YouTube video
- Comment quotes link to the specific comment with timestamp
- Full attribution including author names and engagement metrics

**Configurable Limits**:
- Number of videos to analyze per search
- Number of comments to collect per video
- Custom AI analysis prompts
- Language and region preferences

## Technical Architecture

**Data Pipeline**:
Search Videos → Clean Data → Collect Comments → AI Analysis → Build Response

**API Integration**:
- YouTube138 RapidAPI for video search and comment collection
- OpenAI for sentiment and theme analysis
- FastAPI for the web service
- Pydantic for data validation and response schemas

**Key Components**:
- YouTube API client (handles search and comments)
- Comment collector (gathers comments for multiple videos)
- Data cleaner (normalizes YouTube API responses)
- AI analyzer (processes content through OpenAI)
- Response builder (formats final API response)

## Success Criteria

**Accuracy**: All quotes traceable to original YouTube sources
**Performance**: Process 20 videos with 50 comments each in under 60 seconds
**Reliability**: Robust error handling for API failures and rate limits
**Usability**: Clear, structured responses with rich metadata
**Scalability**: Configurable limits to handle different use cases

## Business Value

This API enables businesses to understand public sentiment about their products, competitors, or industry topics by analyzing YouTube discussions. The full source tracking allows users to dive deeper into specific feedback and engage with their community directly on YouTube.

## Implementation Approach

Reuse 80% of the proven codebase from our TikTok and Instagram APIs, adapting only the data models and API client for YouTube's specific response format. This ensures rapid development while maintaining the reliability and performance of our existing systems.
