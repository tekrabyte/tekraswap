"""Custom exception classes for better error handling.

This module defines custom exceptions used throughout the backend application
to provide more specific error information and better error handling.
"""

from typing import Optional, Dict, Any


class BaseAPIException(Exception):
    """Base exception class for all API-related exceptions.
    
    Attributes:
        message: Human-readable error message
        status_code: HTTP status code to return
        details: Additional error details (optional)
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class TokenServiceException(BaseAPIException):
    """Exception raised when token service operations fail.
    
    Examples:
        - Failed to fetch token metadata
        - Invalid token address
        - RPC connection errors
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=503, details=details)


class JupiterServiceException(BaseAPIException):
    """Exception raised when Jupiter API operations fail.
    
    Examples:
        - Quote request failed
        - Swap transaction building failed
        - Jupiter API unavailable
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=503, details=details)


class ValidationException(BaseAPIException):
    """Exception raised when input validation fails.
    
    Examples:
        - Invalid Solana address format
        - Invalid amount (negative or zero)
        - Missing required parameters
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class RateLimitException(BaseAPIException):
    """Exception raised when rate limit is exceeded.
    
    Used to prevent API abuse and ensure fair usage.
    """
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(
            message,
            status_code=429,
            details={"retry_after": retry_after}
        )


class ExternalAPIException(BaseAPIException):
    """Exception raised when external API calls fail.
    
    Examples:
        - DexScreener API timeout
        - GeckoTerminal API error
        - Helius RPC error
    """
    
    def __init__(
        self,
        service_name: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        full_message = f"{service_name} API Error: {message}"
        super().__init__(full_message, status_code=502, details=details)
