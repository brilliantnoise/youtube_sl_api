"""
Date Parser Utility
Converts YouTube's relative date strings ("1 year ago", "2 months ago") to absolute dates.
Handles timezone conversions and date validation.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
import pytz
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)


# Timezone mapping for common regions
REGION_TIMEZONE_MAP = {
    # North America
    "US": "America/New_York",
    "CA": "America/Toronto",
    "MX": "America/Mexico_City",
    
    # Europe
    "UK": "Europe/London",
    "GB": "Europe/London",
    "FR": "Europe/Paris",
    "DE": "Europe/Berlin",
    "IT": "Europe/Rome",
    "ES": "Europe/Madrid",
    "NL": "Europe/Amsterdam",
    "SE": "Europe/Stockholm",
    "NO": "Europe/Oslo",
    "DK": "Europe/Copenhagen",
    "FI": "Europe/Helsinki",
    "PL": "Europe/Warsaw",
    "CH": "Europe/Zurich",
    "AT": "Europe/Vienna",
    "BE": "Europe/Brussels",
    "IE": "Europe/Dublin",
    "PT": "Europe/Lisbon",
    "GR": "Europe/Athens",
    "CZ": "Europe/Prague",
    "RO": "Europe/Bucharest",
    
    # Asia Pacific
    "JP": "Asia/Tokyo",
    "CN": "Asia/Shanghai",
    "IN": "Asia/Kolkata",
    "KR": "Asia/Seoul",
    "AU": "Australia/Sydney",
    "NZ": "Pacific/Auckland",
    "SG": "Asia/Singapore",
    "HK": "Asia/Hong_Kong",
    "TW": "Asia/Taipei",
    "TH": "Asia/Bangkok",
    "MY": "Asia/Kuala_Lumpur",
    "PH": "Asia/Manila",
    "ID": "Asia/Jakarta",
    "VN": "Asia/Ho_Chi_Minh",
    "PK": "Asia/Karachi",
    "BD": "Asia/Dhaka",
    
    # Middle East
    "AE": "Asia/Dubai",
    "SA": "Asia/Riyadh",
    "IL": "Asia/Jerusalem",
    "TR": "Europe/Istanbul",
    
    # South America
    "BR": "America/Sao_Paulo",
    "AR": "America/Argentina/Buenos_Aires",
    "CL": "America/Santiago",
    "CO": "America/Bogota",
    "PE": "America/Lima",
    "VE": "America/Caracas",
    
    # Africa
    "ZA": "Africa/Johannesburg",
    "EG": "Africa/Cairo",
    "NG": "Africa/Lagos",
    "KE": "Africa/Nairobi",
}


def get_region_timezone(region_code: str) -> str:
    """
    Get timezone string for a region code.
    
    Args:
        region_code: ISO 3166-1 alpha-2 country code (e.g., "US", "UK", "JP")
        
    Returns:
        Timezone string (e.g., "America/New_York") or "UTC" as fallback
        
    Examples:
        >>> get_region_timezone("US")
        'America/New_York'
        >>> get_region_timezone("JP")
        'Asia/Tokyo'
        >>> get_region_timezone("XX")  # Unknown
        'UTC'
    """
    timezone = REGION_TIMEZONE_MAP.get(region_code.upper(), "UTC")
    
    if timezone == "UTC":
        logger.warning(f"Unknown region code '{region_code}', using UTC timezone")
    else:
        logger.debug(f"Mapped region '{region_code}' to timezone '{timezone}'")
    
    return timezone


def parse_iso_date_with_timezone(date_str: str, timezone_str: str) -> datetime:
    """
    Parse ISO date string and apply timezone.
    
    Args:
        date_str: Date string in ISO format "YYYY-MM-DD"
        timezone_str: Timezone string (e.g., "America/New_York", "UTC")
        
    Returns:
        Timezone-aware datetime object at start of day (00:00:00)
        
    Raises:
        ValueError: If date string is invalid
        
    Examples:
        >>> parse_iso_date_with_timezone("2024-11-19", "America/New_York")
        datetime.datetime(2024, 11, 19, 0, 0, tzinfo=<DstTzInfo 'America/New_York' EST-1 day, 19:00:00 STD>)
    """
    try:
        # Parse date string
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        
        # Get timezone
        tz = pytz.timezone(timezone_str)
        
        # Localize to timezone (at start of day)
        localized_date = tz.localize(date_obj)
        
        logger.debug(f"Parsed '{date_str}' with timezone '{timezone_str}' → {localized_date}")
        
        return localized_date
    
    except ValueError as e:
        logger.error(f"Failed to parse date '{date_str}': {str(e)}")
        raise ValueError(f"Invalid date format '{date_str}'. Expected YYYY-MM-DD (e.g., '2024-11-19')")
    
    except pytz.exceptions.UnknownTimeZoneError as e:
        logger.error(f"Unknown timezone '{timezone_str}': {str(e)}")
        raise ValueError(f"Unknown timezone '{timezone_str}'")


def validate_date_range(
    start_date: str,
    end_date: str,
    timezone_str: str = "UTC"
) -> Tuple[datetime, datetime]:
    """
    Validate and parse date range.
    
    Args:
        start_date: Start date in ISO format "YYYY-MM-DD"
        end_date: End date in ISO format "YYYY-MM-DD"
        timezone_str: Timezone to apply (default: "UTC")
        
    Returns:
        Tuple of (start_datetime, end_datetime) as timezone-aware objects
        
    Raises:
        ValueError: If dates are invalid or start_date > end_date
        
    Examples:
        >>> validate_date_range("2024-01-01", "2024-12-31", "UTC")
        (datetime(...), datetime(...))
    """
    # Parse both dates
    start_dt = parse_iso_date_with_timezone(start_date, timezone_str)
    end_dt = parse_iso_date_with_timezone(end_date, timezone_str)
    
    # Set end_dt to end of day (23:59:59) to include full day
    end_dt = end_dt.replace(hour=23, minute=59, second=59)
    
    # Validate range
    if start_dt > end_dt:
        raise ValueError(
            f"Invalid date range: start_date ({start_date}) cannot be after end_date ({end_date}). "
            f"Please ensure start_date is earlier than or equal to end_date."
        )
    
    logger.info(f"Validated date range: {start_date} to {end_date} (timezone: {timezone_str})")
    
    return start_dt, end_dt


def parse_relative_date(relative_str: str, reference_date: datetime) -> Optional[datetime]:
    """
    Parse YouTube's relative date strings to absolute datetime.
    
    YouTube returns dates like:
    - "just now"
    - "5 minutes ago"
    - "1 hour ago"
    - "3 days ago"
    - "2 weeks ago"
    - "1 month ago"
    - "6 months ago"
    - "1 year ago"
    - "5 years ago"
    
    Args:
        relative_str: Relative date string from YouTube
        reference_date: Reference datetime (usually current time)
        
    Returns:
        Absolute datetime or None if parsing fails
        
    Examples:
        >>> ref = datetime(2024, 11, 19, 12, 0, 0)
        >>> parse_relative_date("1 day ago", ref)
        datetime.datetime(2024, 11, 18, 12, 0, 0)
        >>> parse_relative_date("3 months ago", ref)
        datetime.datetime(2024, 8, 19, 12, 0, 0)
    """
    if not relative_str:
        logger.warning("Empty relative date string")
        return None
    
    relative_str = relative_str.strip().lower()
    
    # Handle "just now" / "now"
    if relative_str in ["just now", "now"]:
        logger.debug(f"Parsed '{relative_str}' as current time")
        return reference_date
    
    # Regex patterns for different time units
    patterns = [
        # Seconds: "30 seconds ago", "1 second ago"
        (r'(\d+)\s*seconds?\s*ago', 'seconds'),
        
        # Minutes: "5 minutes ago", "1 minute ago"
        (r'(\d+)\s*minutes?\s*ago', 'minutes'),
        (r'a\s*minute\s*ago', 'minutes', 1),
        
        # Hours: "2 hours ago", "1 hour ago", "an hour ago"
        (r'(\d+)\s*hours?\s*ago', 'hours'),
        (r'an?\s*hour\s*ago', 'hours', 1),
        
        # Days: "3 days ago", "1 day ago", "a day ago"
        (r'(\d+)\s*days?\s*ago', 'days'),
        (r'a\s*day\s*ago', 'days', 1),
        
        # Weeks: "2 weeks ago", "1 week ago", "a week ago"
        (r'(\d+)\s*weeks?\s*ago', 'weeks'),
        (r'a\s*week\s*ago', 'weeks', 1),
        
        # Months: "6 months ago", "1 month ago", "a month ago"
        (r'(\d+)\s*months?\s*ago', 'months'),
        (r'a\s*month\s*ago', 'months', 1),
        
        # Years: "2 years ago", "1 year ago", "a year ago"
        (r'(\d+)\s*years?\s*ago', 'years'),
        (r'a\s*year\s*ago', 'years', 1),
    ]
    
    for pattern_data in patterns:
        if len(pattern_data) == 2:
            pattern, unit = pattern_data
            default_value = None
        else:
            pattern, unit, default_value = pattern_data
        
        match = re.search(pattern, relative_str)
        if match:
            # Get the numeric value
            if default_value is not None:
                value = default_value
            else:
                value = int(match.group(1))
            
            # Calculate absolute date
            try:
                if unit == 'seconds':
                    result = reference_date - timedelta(seconds=value)
                elif unit == 'minutes':
                    result = reference_date - timedelta(minutes=value)
                elif unit == 'hours':
                    result = reference_date - timedelta(hours=value)
                elif unit == 'days':
                    result = reference_date - timedelta(days=value)
                elif unit == 'weeks':
                    result = reference_date - timedelta(weeks=value)
                elif unit == 'months':
                    result = reference_date - relativedelta(months=value)
                elif unit == 'years':
                    result = reference_date - relativedelta(years=value)
                else:
                    logger.warning(f"Unknown time unit: {unit}")
                    return None
                
                logger.debug(f"Parsed '{relative_str}' as {result} (ref: {reference_date})")
                return result
            
            except Exception as e:
                logger.error(f"Error calculating date for '{relative_str}': {str(e)}")
                return None
    
    # If no pattern matched
    logger.warning(f"Could not parse relative date string: '{relative_str}'")
    return None


def is_datetime_in_range(
    dt: datetime,
    start_date: datetime,
    end_date: datetime
) -> bool:
    """
    Check if a datetime falls within a date range.
    
    Args:
        dt: Datetime to check
        start_date: Start of range (inclusive)
        end_date: End of range (inclusive)
        
    Returns:
        True if dt is within range, False otherwise
        
    Examples:
        >>> start = datetime(2024, 1, 1)
        >>> end = datetime(2024, 12, 31)
        >>> is_datetime_in_range(datetime(2024, 6, 15), start, end)
        True
        >>> is_datetime_in_range(datetime(2025, 1, 1), start, end)
        False
    """
    # Ensure all datetimes are timezone-aware or all naive
    if dt.tzinfo is None and start_date.tzinfo is not None:
        # Convert naive dt to aware using start_date's timezone
        dt = start_date.tzinfo.localize(dt)
    elif dt.tzinfo is not None and start_date.tzinfo is None:
        # Convert aware dt to naive
        dt = dt.replace(tzinfo=None)
    
    return start_date <= dt <= end_date


# Example usage and testing
if __name__ == "__main__":
    # Setup logging for testing
    logging.basicConfig(level=logging.DEBUG)
    
    print("=" * 60)
    print("Testing Date Parser Utility")
    print("=" * 60)
    
    # Test 1: Timezone mapping
    print("\n1. Testing timezone mapping:")
    print(f"US → {get_region_timezone('US')}")
    print(f"UK → {get_region_timezone('UK')}")
    print(f"JP → {get_region_timezone('JP')}")
    print(f"XX (unknown) → {get_region_timezone('XX')}")
    
    # Test 2: ISO date parsing
    print("\n2. Testing ISO date parsing:")
    dt = parse_iso_date_with_timezone("2024-11-19", "America/New_York")
    print(f"2024-11-19 in America/New_York → {dt}")
    
    # Test 3: Date range validation
    print("\n3. Testing date range validation:")
    try:
        start, end = validate_date_range("2024-01-01", "2024-12-31", "UTC")
        print(f"Valid range: {start} to {end}")
    except ValueError as e:
        print(f"Error: {e}")
    
    try:
        start, end = validate_date_range("2024-12-31", "2024-01-01", "UTC")
        print(f"Valid range: {start} to {end}")
    except ValueError as e:
        print(f"Expected error: {e}")
    
    # Test 4: Relative date parsing
    print("\n4. Testing relative date parsing:")
    ref = datetime(2024, 11, 19, 12, 0, 0, tzinfo=pytz.UTC)
    test_strings = [
        "just now",
        "5 minutes ago",
        "1 hour ago",
        "3 days ago",
        "2 weeks ago",
        "1 month ago",
        "6 months ago",
        "1 year ago",
        "2 years ago",
        "a day ago",
        "an hour ago",
        "a month ago",
    ]
    
    for test_str in test_strings:
        result = parse_relative_date(test_str, ref)
        if result:
            delta = ref - result
            print(f"'{test_str}' → {result} (delta: {delta})")
        else:
            print(f"'{test_str}' → Failed to parse")
    
    print("\n" + "=" * 60)
    print("✅ Date Parser Utility Tests Complete")
    print("=" * 60)

