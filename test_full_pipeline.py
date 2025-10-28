#!/usr/bin/env python3
"""
Full end-to-end test of the YouTube Social Listening API
"""
import subprocess
import time
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
service_api_key = os.getenv("SERVICE_API_KEY")
if not service_api_key:
    print("❌ ERROR: SERVICE_API_KEY not found in .env file")
    exit(1)

print("🚀 Starting FastAPI server...")
proc = subprocess.Popen(
    ['python3', '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT  # Capture errors to stdout
)

# Wait for server to start
print("⏳ Waiting for server to start...")
time.sleep(5)

try:
    # Make full request with all schema fields
    print("\n📡 Making full analysis request...")
    print("=" * 70)
    
    request_payload = {
        "query": "iPhone 15 Pro review",
        "max_videos": 3,  # Small dataset
        "max_comments_per_video": 15,  # Small dataset
        "language": "en",
        "region": "US",
        "ai_analysis_prompt": "Analyze sentiment, themes, and purchase intent for this product",
        "model": "gpt-4o-mini",  # Using faster/cheaper model for testing
        "max_quote_length": 150
    }
    
    print("REQUEST PAYLOAD:")
    print(json.dumps(request_payload, indent=2))
    print("=" * 70)
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": service_api_key
    }
    
    print("\n🔄 Processing (this may take 30-60 seconds)...")
    response = requests.post(
        'http://127.0.0.1:8000/analyze-youtube-search',
        json=request_payload,
        headers=headers,
        timeout=120
    )
    
    print(f"\n✅ Response Status: {response.status_code}")
    print("=" * 70)
    
    if response.status_code == 200:
        result = response.json()
        
        # Save to file for review
        with open('test_response.json', 'w') as f:
            json.dump(result, f, indent=2)
        print("\n💾 Full response saved to: test_response.json")
        
        # Print formatted response
        print("\n📊 FULL JSON RESPONSE:")
        print("=" * 70)
        print(json.dumps(result, indent=2))
        print("=" * 70)
        
        # Print summary
        metadata = result.get('metadata', {})
        print(f"\n📈 SUMMARY:")
        print(f"   Videos Analyzed: {metadata.get('total_videos_analyzed', 0)}")
        print(f"   Comments Found: {metadata.get('total_comments_found', 0)}")
        print(f"   Insights Extracted: {metadata.get('relevant_insights_extracted', 0)}")
        print(f"   Processing Time: {metadata.get('processing_time_seconds', 0)}s")
        print(f"   Model Used: {metadata.get('model_used', 'N/A')}")
        
        # Print sentiment distribution
        sentiment = metadata.get('sentiment_distribution', {})
        print(f"\n💭 SENTIMENT:")
        print(f"   Positive: {sentiment.get('positive', 0)}")
        print(f"   Negative: {sentiment.get('negative', 0)}")
        print(f"   Neutral: {sentiment.get('neutral', 0)}")
        
        # Print purchase intent
        intent = metadata.get('purchase_intent_distribution', {})
        print(f"\n🛒 PURCHASE INTENT:")
        print(f"   High: {intent.get('high', 0)}")
        print(f"   Medium: {intent.get('medium', 0)}")
        print(f"   Low: {intent.get('low', 0)}")
        print(f"   None: {intent.get('none', 0)}")
        
        # Print API usage
        youtube_usage = metadata.get('youtube_api_usage', {})
        openai_usage = metadata.get('openai_api_usage', {})
        print(f"\n💰 API USAGE:")
        print(f"   YouTube API Calls: {youtube_usage.get('total_api_calls', 0)}")
        print(f"   OpenAI Tokens: {openai_usage.get('total_tokens', 0)}")
        print(f"   OpenAI Cost: ${openai_usage.get('total_cost_usd', 0)}")
        
        # Show a sample insight
        analyses = result.get('comment_analyses', [])
        if analyses:
            print(f"\n📝 SAMPLE INSIGHT:")
            sample = analyses[0]
            print(f"   Quote: {sample.get('quote', 'N/A')[:100]}...")
            print(f"   Sentiment: {sample.get('sentiment', 'N/A')}")
            print(f"   Theme: {sample.get('theme', 'N/A')}")
            print(f"   Purchase Intent: {sample.get('purchase_intent', 'N/A')}")
            print(f"   Confidence: {sample.get('confidence_score', 0)}")
            print(f"   Source: {sample.get('source_type', 'N/A')}")
            print(f"   Video: {sample.get('video_title', 'N/A')}")
        
        print("\n✅ END-TO-END TEST SUCCESSFUL!")
        
    else:
        print(f"\n❌ Error Response:")
        print(response.text)
        
except requests.exceptions.Timeout:
    print("\n⏱️ Request timed out (may need more time for processing)")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    print("\n🛑 Stopping server...")
    proc.terminate()
    proc.wait(timeout=5)
    print("✅ Server stopped")

