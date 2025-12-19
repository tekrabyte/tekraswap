"""Input validation utilities.

This module provides validation functions for common input types
used in the Solana DEX swap application.
"""

import re
from typing import Optional
from .exceptions import ValidationException


# Solana address regex pattern (base58, 32-44 characters)
SOLANA_ADDRESS_PATTERN = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')


def validate_solana_address(address: str, field_name: str = "address") -> str:
    """Validate Solana address format.
    
    Args:
        address: The address string to validate
        field_name: Name of the field (for error messages)
    
    Returns:
        The validated address (trimmed)
    
    Raises:
        ValidationException: If address format is invalid
    
    Examples:
        >>> validate_solana_address("So11111111111111111111111111111111111111112")
        'So11111111111111111111111111111111111111112'
        
        >>> validate_solana_address("invalid")
        ValidationException: Invalid address format
    """
    if not address:
        raise ValidationException(
            f"{field_name} is required",
            details={"field": field_name}
        )
    
    address = address.strip()
    
    if not SOLANA_ADDRESS_PATTERN.match(address):
        raise ValidationException(
            f"Invalid {field_name} format. Must be a valid Solana address (32-44 base58 characters)",
            details={
                "field": field_name,
                "value": address,
                "pattern": "base58, 32-44 characters"
            }
        )
    
    return address


def validate_positive_amount(amount: int, field_name: str = "amount") -> int:
    """Validate that amount is positive.
    
    Args:
        amount: The amount to validate
        field_name: Name of the field (for error messages)
    
    Returns:
        The validated amount
    
    Raises:
        ValidationException: If amount is not positive
    
    Examples:
        >>> validate_positive_amount(1000)
        1000
        
        >>> validate_positive_amount(0)
        ValidationException: amount must be positive
    """
    if not isinstance(amount, (int, float)):
        raise ValidationException(
            f"{field_name} must be a number",
            details={"field": field_name, "type": type(amount).__name__}
        )
    
    if amount <= 0:
        raise ValidationException(
            f"{field_name} must be positive (greater than 0)",
            details={"field": field_name, "value": amount}
        )
    
    return int(amount)


def validate_slippage_bps(slippage_bps: int) -> int:
    """Validate slippage basis points.
    
    Args:
        slippage_bps: Slippage in basis points (1 bps = 0.01%)
    
    Returns:
        The validated slippage value
    
    Raises:
        ValidationException: If slippage is out of valid range
    
    Examples:
        >>> validate_slippage_bps(50)  # 0.5%
        50
        
        >>> validate_slippage_bps(10000)  # 100%
        10000
        
        >>> validate_slippage_bps(20000)  # 200% - too high
        ValidationException: slippageBps out of range
    """
    if not isinstance(slippage_bps, int):
        raise ValidationException(
            "slippageBps must be an integer",
            details={"type": type(slippage_bps).__name__}
        )
    
    if slippage_bps < 0:
        raise ValidationException(
            "slippageBps cannot be negative",
            details={"value": slippage_bps}
        )
    
    if slippage_bps > 10000:  # Max 100% slippage
        raise ValidationException(
            "slippageBps cannot exceed 10000 (100%)",
            details={"value": slippage_bps, "max": 10000}
        )
    
    return slippage_bps


def validate_interval(interval: str) -> str:
    """Validate chart interval parameter.
    
    Args:
        interval: Time interval (e.g., '1h', '1d', '1w')
    
    Returns:
        The validated interval
    
    Raises:
        ValidationException: If interval is not supported
    """
    valid_intervals = ['1h', '1d', '1w', '1m']
    
    if interval not in valid_intervals:
        raise ValidationException(
            f"Invalid interval. Must be one of: {', '.join(valid_intervals)}",
            details={
                "field": "interval",
                "value": interval,
                "valid_values": valid_intervals
            }
        )
    
    return interval
