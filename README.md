# 🎥 YouTube Social Listening API

A YouTube social listening API that searches for videos based on keywords and analyzes the sentiment, themes, and purchase intent of both video content and comments.

## 🚀 Features

- **Video Search**: Search YouTube for videos by keyword
- **Content Analysis**: Analyze video titles, descriptions, and comments
- **AI-Powered Insights**: Sentiment analysis, theme identification, and purchase intent detection
- **Full Source Tracking**: Every quote links back to its YouTube source
- **Configurable Limits**: Customize number of videos and comments to analyze

## 📋 Project Status

**In Development** - Following implementation plan

## 🛠️ Technology Stack

- **FastAPI**: Modern web framework
- **Pydantic**: Data validation
- **OpenAI**: AI analysis
- **YouTube138 RapidAPI**: Video search and comment collection
- **Python 3.11+**

## 📦 Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

## 🔑 Required API Keys

- YouTube RapidAPI key (YouTube138)
- OpenAI API key
- Service API key (for authentication)

## 📖 API Documentation

Once running, visit: `http://localhost:8000/docs`

## 🏗️ Project Structure

```
youtube_sl_api/
├── app/
│   ├── core/          # Configuration and exceptions
│   ├── models/        # Data models and schemas
│   └── services/      # Business logic
│       ├── youtube_search/    # Search orchestration
│       └── youtube_shared/    # Shared utilities
├── requirements.txt
└── README.md
```

## 📝 License

Proprietary - All rights reserved

