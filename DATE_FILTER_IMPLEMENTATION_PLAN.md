# Date Filter Implementation Plan
**Feature:** Add `start_date` and `end_date` parameters to filter comments by date range

---

## 📊 Current State Analysis

### What We Found:
1. **Comment Date Field**: YouTube138 API returns `publishedTimeText` as a **relative string** (e.g., "1 year ago", "2 months ago", "3 days ago")
   - Located in: `YouTubeComment.publishedTimeText` (line 88 in `youtube_schemas.py`)
   - Stored after cleaning: `cleaned_comment["published_time"]` (line 286 in `youtube_data_cleaners.py`)

2. **Challenge**: We need to convert relative date strings → absolute dates for filtering

3. **Current Pipeline Flow**:
   ```
   Stage 1: Search Videos
   Stage 2: Clean Videos
   Stage 3: Collect & Clean Comments  ← INSERT DATE FILTER HERE
   Stage 4: AI Analysis (costs money)
   Stage 5: Build Response
   ```

---

## 🎯 Implementation Strategy

### New Parameters:
```python
start_date: Optional[str] = None  # Format: "YYYY-MM-DD" (ISO 8601)
end_date: Optional[str] = None    # Format: "YYYY-MM-DD" (ISO 8601)
```

### Filtering Approach:
- Filter **AFTER** comment cleaning (Stage 3)
- Filter **BEFORE** AI analysis (Stage 4) to save OpenAI costs
- If a video has NO comments in date range: Include video with note "no comments in date range"

---

## 📝 Tasks Breakdown

### **Task 1: Create Date Parser Utility** ✅
**File:** `app/utils/date_parser.py` (NEW FILE)
**Purpose:** Convert relative date strings to absolute dates

**Functions:**
1. `parse_relative_date(relative_str: str, reference_date: datetime) -> Optional[datetime]`
   - Parse "1 year ago", "2 months ago", "3 days ago", "5 hours ago", "just now", etc.
   - Return absolute datetime or None if parsing fails
   - Handle edge cases: "1 day ago" vs "1 days ago", "a month ago", etc.

2. `get_region_timezone(region_code: str) -> str`
   - Map region codes to timezones (e.g., "US" → "America/New_York", "UK" → "Europe/London")
   - Return UTC as fallback

3. `parse_iso_date_with_timezone(date_str: str, timezone_str: str) -> datetime`
   - Parse "YYYY-MM-DD" string
   - Apply timezone
   - Return timezone-aware datetime

4. `validate_date_range(start_date: str, end_date: str) -> tuple[datetime, datetime]`
   - Validate ISO date format
   - Check start_date <= end_date
   - Raise custom error if invalid
   - Return tuple of parsed dates

**Dependencies:**
- `dateutil.parser` (for flexible parsing)
- `pytz` (for timezone handling)
- `re` (for regex pattern matching)

---

### **Task 2: Create Date Filter Service** ✅
**File:** `app/services/youtube_shared/youtube_date_filter.py` (NEW FILE)
**Purpose:** Filter comments by date range

**Class:** `YouTubeDateFilter`

**Methods:**
1. `filter_comments_by_date_range(
       comments_by_video: Dict[str, List[Dict]],
       start_date: datetime,
       end_date: datetime,
       reference_date: datetime
   ) -> Dict[str, Any]`
   - Input: Dictionary of {video_id: [comments]}
   - For each comment: Parse `published_time` → filter by date range
   - Return: {
       "filtered_comments_by_video": {...},
       "filter_stats": {
           "total_comments_before": int,
           "total_comments_after": int,
           "comments_filtered_out": int,
           "videos_with_comments": int,
           "videos_without_comments": int,
           "date_range": {"start": str, "end": str}
       }
   }

2. `_is_comment_in_range(
       comment: Dict,
       start_date: datetime,
       end_date: datetime,
       reference_date: datetime
   ) -> bool`
   - Helper: Check if single comment is in range
   - Parse relative date and compare

---

### **Task 3: Update Request Schema** ✅
**File:** `app/models/youtube_schemas.py`
**Changes:**

```python
class YouTubeSearchAnalysisRequest(BaseModel):
    # ... existing fields ...
    
    start_date: Optional[str] = Field(
        default=None,
        description="Filter comments from this date onwards (ISO format: YYYY-MM-DD). Optional.",
        regex=r'^\d{4}-\d{2}-\d{2}$'
    )
    end_date: Optional[str] = Field(
        default=None,
        description="Filter comments up to this date (ISO format: YYYY-MM-DD). Optional.",
        regex=r'^\d{4}-\d{2}-\d{2}$'
    )
    
    @validator('end_date')
    def validate_date_range(cls, end_date, values):
        start_date = values.get('start_date')
        
        # Both must be provided or both None
        if (start_date is None) != (end_date is None):
            raise ValueError('Both start_date and end_date must be provided together, or neither')
        
        # If both provided, validate range
        if start_date and end_date:
            try:
                from datetime import datetime
                start = datetime.fromisoformat(start_date)
                end = datetime.fromisoformat(end_date)
                
                if start > end:
                    raise ValueError(
                        f'start_date ({start_date}) cannot be after end_date ({end_date}). '
                        f'Please ensure start_date is earlier than or equal to end_date.'
                    )
            except ValueError as e:
                if "does not match format" in str(e):
                    raise ValueError('Invalid date format. Use YYYY-MM-DD (e.g., 2024-01-15)')
                raise
        
        return end_date
```

---

### **Task 4: Create Custom Exception** ✅
**File:** `app/core/exceptions.py`
**Changes:** Add new exception class

```python
class DateValidationError(YouTubeAPIException):
    """Exception for date validation errors."""
    
    def __init__(
        self,
        message: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        super().__init__(message)
        self.start_date = start_date
        self.end_date = end_date
        self.error_code = "DATE_VALIDATION_ERROR"
```

---

### **Task 5: Integrate Date Filter into Pipeline** ✅
**File:** `app/services/youtube_search/search_service.py`
**Changes:**

1. Add parameters to `analyze_youtube_search()`:
```python
async def analyze_youtube_search(
    # ... existing params ...
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
```

2. Insert between Stage 3 and Stage 4:
```python
# ========== STAGE 3.5: Filter Comments by Date (NEW) ==========
if start_date and end_date:
    logger.info("=" * 60)
    logger.info("Stage 3.5: Filtering comments by date range")
    logger.info(f"Date Range: {start_date} to {end_date}")
    stage3_5_start = datetime.utcnow()
    
    try:
        from app.utils.date_parser import get_region_timezone, validate_date_range
        from app.services.youtube_shared.youtube_date_filter import YouTubeDateFilter
        
        # Get timezone from region
        timezone_str = get_region_timezone(region)
        
        # Validate and parse dates
        start_dt, end_dt = validate_date_range(start_date, end_date, timezone_str)
        
        # Filter comments
        date_filter = YouTubeDateFilter()
        filter_result = date_filter.filter_comments_by_date_range(
            comments_by_video=cleaned_comments_by_video,
            start_date=start_dt,
            end_date=end_dt,
            reference_date=datetime.now(pytz.timezone(timezone_str))
        )
        
        # Update with filtered comments
        cleaned_comments_by_video = filter_result["filtered_comments_by_video"]
        filter_stats = filter_result["filter_stats"]
        total_cleaned_comments = filter_stats["total_comments_after"]
        
        logger.info(
            f"  → Filtered: {filter_stats['comments_filtered_out']} comments removed, "
            f"{filter_stats['total_comments_after']} remain"
        )
        
    except DateValidationError as e:
        logger.error(f"❌ Date validation failed: {e.message}")
        raise
    except Exception as e:
        logger.error(f"❌ Date filtering failed: {str(e)}")
        raise
    
    stage3_5_time = (datetime.utcnow() - stage3_5_start).total_seconds()
    logger.info(f"Stage 3.5 complete in {stage3_5_time:.2f}s")
    logger.info("=" * 60)
```

3. Update youtube_specific metadata:
```python
youtube_specific = {
    # ... existing fields ...
    "date_filter_applied": bool(start_date and end_date),
    "date_range": {
        "start": start_date,
        "end": end_date,
        "timezone": timezone_str,
        "comments_filtered": filter_stats if (start_date and end_date) else None
    } if (start_date and end_date) else None,
}
```

---

### **Task 6: Update FastAPI Endpoint** ✅
**File:** `app/main.py`
**Changes:**

Update endpoint to pass new parameters:
```python
@app.post("/analyze-youtube-search", response_model=YouTubeUnifiedAnalysisResponse)
async def analyze_youtube_search(
    request: YouTubeSearchAnalysisRequest,
    api_key: str = Depends(verify_api_key)
):
    try:
        result = await search_service.analyze_youtube_search(
            query=request.query,
            max_videos=request.max_videos,
            max_comments_per_video=request.max_comments_per_video,
            language=request.language,
            region=request.region,
            ai_analysis_prompt=request.ai_analysis_prompt,
            model=request.model,
            max_quote_length=request.max_quote_length,
            start_date=request.start_date,  # NEW
            end_date=request.end_date,      # NEW
        )
        # ... rest of endpoint ...
```

---

### **Task 7: Update Exception Handler** ✅
**File:** `app/main.py`
**Changes:**

Add exception handler for `DateValidationError`:
```python
@app.exception_handler(DateValidationError)
async def date_validation_error_handler(request: Request, exc: DateValidationError):
    logger.error(f"Date validation error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "Date Validation Error",
            "message": exc.message,
            "error_code": exc.error_code,
            "start_date": exc.start_date,
            "end_date": exc.end_date
        }
    )
```

---

### **Task 8: Update requirements.txt** ✅
**File:** `requirements.txt`
**Changes:** Add dependencies

```txt
python-dateutil>=2.8.2
pytz>=2024.1
```

---

### **Task 9: Update API Documentation** ✅
**File:** `API_USAGE.md`
**Changes:**

1. Update request body example:
```json
{
  "query": "iPhone 16 Pro review",
  "max_videos": 20,
  "max_comments_per_video": 50,
  "language": "en",
  "region": "US",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "ai_analysis_prompt": "Analyze sentiment, themes, and purchase intent",
  "model": "gpt-4.1-2025-04-14",
  "max_quote_length": 200
}
```

2. Add to parameter table:
| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|-------|-------------|
| `start_date` | string | Optional | `None` | YYYY-MM-DD | Filter comments from this date onwards (ISO format) |
| `end_date` | string | Optional | `None` | YYYY-MM-DD | Filter comments up to this date (ISO format) |

3. Add new section: "## Filtering Comments by Date"
```markdown
### Date Filtering
Filter comments to a specific time range using `start_date` and `end_date`:
- Both parameters must be provided together (or neither)
- Format: ISO 8601 date format `YYYY-MM-DD` (e.g., "2024-01-15")
- Timezone is inferred from the `region` parameter (e.g., "US" → America/New_York)
- Comments outside the date range are excluded BEFORE AI analysis (saves costs)
- Videos with no comments in range are included with metadata

#### Example: Analyze comments from Q1 2024
```json
{
  "query": "Tesla Model 3",
  "start_date": "2024-01-01",
  "end_date": "2024-03-31",
  "region": "US"
}
```

#### Error Handling:
- If `start_date > end_date`: Returns 400 error with message
- If only one date provided: Returns 400 error requiring both
- If invalid format: Returns 400 error with format requirements
```

---

### **Task 10: Testing** ✅
**Create:** `test_date_filter.py`

Test cases:
1. Parse various relative date formats ("1 year ago", "3 months ago", "just now", etc.)
2. Validate date range (valid, invalid, swapped dates)
3. Filter comments by date range (some in range, all out of range, all in range)
4. Handle timezone conversions
5. End-to-end API request with date filters

---

## 📋 Implementation Order

```
1. Task 8: Update requirements.txt (install dependencies first)
2. Task 1: Create date parser utility
3. Task 2: Create date filter service
4. Task 4: Create custom exception
5. Task 3: Update request schema
6. Task 5: Integrate into pipeline
7. Task 6: Update FastAPI endpoint
8. Task 7: Update exception handler
9. Task 9: Update API documentation
10. Task 10: Testing & validation
```

---

## 🎯 Expected Behavior

### Example Request:
```json
{
  "query": "iPhone 16 Pro",
  "max_videos": 10,
  "start_date": "2024-11-01",
  "end_date": "2024-11-19",
  "region": "US"
}
```

### Expected Result:
- Only analyzes comments published between Nov 1-19, 2024
- Comments outside range are filtered out
- Reduces AI analysis cost (fewer comments → fewer tokens)
- Response includes date filter metadata
- Videos with no matching comments show `"comments_in_date_range": 0`

---

## ⚠️ Edge Cases to Handle

1. **No comments in date range**: Return video with `comments_in_date_range: 0`
2. **Invalid date format**: Return 400 error with clear message
3. **Start date > end date**: Return 400 error: "start_date cannot be after end_date"
4. **Only one date provided**: Return 400 error: "Both dates required"
5. **Unparseable relative dates**: Log warning, skip comment (don't crash)
6. **Timezone edge cases**: Use UTC if region unmapped

---

## 📊 Success Criteria

✅ API accepts `start_date` and `end_date` parameters
✅ Comments are filtered BEFORE AI analysis
✅ Date parsing handles various relative formats
✅ Timezone inference works for major regions
✅ Proper error messages for invalid dates
✅ Metadata includes filter statistics
✅ Documentation updated with examples
✅ Tests pass for all edge cases

---

## 📝 Notes

- **Cost Savings**: Filtering before AI analysis saves OpenAI API costs
- **YouTube Data**: YouTube only provides relative dates, not absolute timestamps
- **Parsing Accuracy**: Relative dates are approximate (e.g., "1 month ago" could be 30-31 days)
- **Default Behavior**: If no dates provided, analyze ALL comments (backward compatible)

