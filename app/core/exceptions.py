import logging
from typing import Optional, Dict, Any
from datetime import datetime

class YouTubeAPIException(Exception):
    """Base exception for YouTube API errors."""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 500, 
        error_code: Optional[str] = None, 
        details: Optional[Dict[str, Any]] = None,
        log_level: str = "ERROR"
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self._generate_error_code()
        self.details = self._sanitize_details(details or {})
        self.log_level = log_level
        self.timestamp = datetime.utcnow().isoformat()
        
        # Log the exception
        logger = logging.getLogger(self.__class__.__module__)
        getattr(logger, log_level.lower(), logger.error)(
            f"{self.error_code}: {self.message}",
            extra={
                "error_code": self.error_code,
                "status_code": self.status_code,
                "details": self.details,
                "timestamp": self.timestamp
            }
        )
        
        super().__init__(self.message)
    
    def _generate_error_code(self) -> str:
        """Generate error code from class name."""
        class_name = self.__class__.__name__
        if class_name.endswith('Error'):
            class_name = class_name[:-5]
        return class_name.upper()
    
    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize details to prevent sensitive information leakage."""
        sanitized = {}
        sensitive_keys = {'password', 'token', 'key', 'secret', 'auth', 'api_key'}
        
        for key, value in details.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str) and len(value) > 1000:
                sanitized[key] = value[:1000] + "...[TRUNCATED]"
            else:
                sanitized[key] = value
                
        return sanitized
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
            "status_code": self.status_code
        }

class YouTubeValidationError(YouTubeAPIException):
    """Request validation error."""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["provided_value"] = value
        super().__init__(message, status_code=400, details=details)

class YouTubeDataCollectionError(YouTubeAPIException):
    """YouTube data collection error."""
    
    def __init__(self, message: str, api_endpoint: Optional[str] = None, http_status: Optional[int] = None):
        details = {}
        if api_endpoint:
            details["api_endpoint"] = api_endpoint
        if http_status:
            details["http_status"] = http_status
        super().__init__(message, status_code=502, details=details)

class YouTubeAnalysisError(YouTubeAPIException):
    """AI analysis error."""
    
    def __init__(self, message: str, model: Optional[str] = None, video_id: Optional[str] = None):
        details = {}
        if model:
            details["model"] = model
        if video_id:
            details["video_id"] = video_id
        super().__init__(message, status_code=503, details=details)

class RateLimitExceededError(YouTubeAPIException):
    """Rate limit exceeded error."""
    
    def __init__(self, message: str, service: Optional[str] = None, retry_after: Optional[int] = None):
        details = {}
        if service:
            details["service"] = service
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, status_code=429, details=details, log_level="WARNING")

class AuthenticationError(YouTubeAPIException):
    """Authentication error."""
    
    def __init__(self, message: str, auth_type: Optional[str] = None):
        details = {"auth_type": auth_type} if auth_type else {}
        super().__init__(message, status_code=401, details=details, log_level="WARNING")
