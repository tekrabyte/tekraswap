"""Jupiter Swap Service.

This module provides integration with Jupiter Aggregator V6 API
for getting swap quotes and building swap transactions on Solana.

Jupiter API Documentation: https://dev.jup.ag/api-reference

Note: lite-api.jup.ag will be deprecated on January 31, 2026.
      This implementation uses api.jup.ag (requires API key from portal.jup.ag)
"""

import os
import httpx
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from utils.exceptions import JupiterServiceException, ValidationException
from utils.validators import validate_solana_address, validate_positive_amount, validate_slippage_bps

logger = logging.getLogger(__name__)


class JupiterService:
    """Service for interacting with Jupiter Aggregator API.
    
    This service provides methods to:
    - Get swap quotes with best routes
    - Build swap transactions
    - Query supported tokens and DEXes
    
    Attributes:
        api_url: Base URL for Jupiter API
        api_key: API key for authenticated requests (optional but recommended)
        timeout: Request timeout in seconds
    """
    
    def __init__(self):
        """Initialize Jupiter Service.
        
        Environment Variables:
            JUPITER_API_URL: Custom API URL (default: https://api.jup.ag/swap/v1)
            JUPITER_API_KEY: Jupiter API key from portal.jup.ag (optional)
        """
        # Use api.jup.ag (new endpoint) instead of lite-api.jup.ag (being deprecated)
        self.api_url = os.environ.get(
            'JUPITER_API_URL',
            'https://api.jup.ag/swap/v1'
        )
        self.api_key = os.environ.get('JUPITER_API_KEY')
        self.timeout = 30.0
        
        if not self.api_key:
            logger.warning(
                "JUPITER_API_KEY not set. API may have rate limits. "
                "Get your key at: https://portal.jup.ag"
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for Jupiter API requests.
        
        Returns:
            Dictionary of headers including API key if available
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        if self.api_key:
            headers["x-api-key"] = self.api_key
        
        return headers
    
    async def get_quote(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: int = 50,
        swap_mode: str = "ExactIn",
        only_direct_routes: bool = False,
        max_accounts: int = 64
    ) -> Optional[Dict[str, Any]]:
        """Get a swap quote from Jupiter.
        
        This method requests the best swap route from Jupiter's routing engine.
        The quote can then be used to build a swap transaction.
        
        Args:
            input_mint: Input token mint address
            output_mint: Output token mint address  
            amount: Amount to swap (in raw token units, before decimals)
                   - For ExactIn: this is the input amount
                   - For ExactOut: this is the desired output amount
            slippage_bps: Slippage tolerance in basis points (default: 50 = 0.5%)
                         - ExactIn: slippage applies to output amount
                         - ExactOut: slippage applies to input amount
            swap_mode: "ExactIn" or "ExactOut" (default: "ExactIn")
                      - ExactIn: Swap exact input amount, output varies
                      - ExactOut: Get exact output amount, input varies
            only_direct_routes: If True, only use direct single-hop routes
            max_accounts: Maximum accounts for the transaction (default: 64)
        
        Returns:
            Quote response dictionary containing:
            - inputMint: Input token address
            - outputMint: Output token address  
            - inAmount: Input amount (string)
            - outAmount: Output amount (string)
            - otherAmountThreshold: Minimum amount after slippage
            - priceImpactPct: Price impact percentage (string)
            - routePlan: Array of swap route steps
            - contextSlot: Blockchain slot number
            - timeTaken: Quote calculation time (ms)
            
            Returns None if quote request fails.
        
        Raises:
            ValidationException: If input parameters are invalid
            JupiterServiceException: If Jupiter API request fails
        
        Examples:
            >>> service = JupiterService()
            >>> # Swap 1 SOL to USDC
            >>> quote = await service.get_quote(
            ...     input_mint="So11111111111111111111111111111111111111112",
            ...     output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            ...     amount=1_000_000_000,  # 1 SOL (9 decimals)
            ...     slippage_bps=50
            ... )
            >>> print(f"Output: {quote['outAmount']}")
        """
        try:
            # Validate inputs
            input_mint = validate_solana_address(input_mint, "inputMint")
            output_mint = validate_solana_address(output_mint, "outputMint")
            amount = validate_positive_amount(amount, "amount")
            slippage_bps = validate_slippage_bps(slippage_bps)
            
            if swap_mode not in ["ExactIn", "ExactOut"]:
                raise ValidationException(
                    f"Invalid swapMode: {swap_mode}. Must be 'ExactIn' or 'ExactOut'"
                )
            
            # Build query parameters
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": str(amount),
                "slippageBps": slippage_bps,
                "swapMode": swap_mode,
                "onlyDirectRoutes": str(only_direct_routes).lower(),
                "maxAccounts": max_accounts,
            }
            
            logger.info(
                f"Requesting Jupiter quote: {amount} {input_mint[:8]}... -> {output_mint[:8]}..."
            )
            
            # Make API request
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_url}/quote",
                    params=params,
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    quote = response.json()
                    logger.info(
                        f"Quote received: {quote.get('inAmount')} -> {quote.get('outAmount')} "
                        f"(impact: {quote.get('priceImpactPct', 'N/A')}%)"
                    )
                    return quote
                else:
                    error_detail = response.text
                    logger.error(
                        f"Jupiter quote failed: {response.status_code} - {error_detail}"
                    )
                    raise JupiterServiceException(
                        f"Failed to get quote from Jupiter (status {response.status_code})",
                        details={"status_code": response.status_code, "error": error_detail}
                    )
        
        except ValidationException:
            raise
        except JupiterServiceException:
            raise
        except httpx.TimeoutException:
            logger.error("Jupiter API timeout")
            raise JupiterServiceException(
                "Jupiter API request timed out",
                details={"timeout": self.timeout}
            )
        except Exception as e:
            logger.error(f"Unexpected error getting Jupiter quote: {e}")
            raise JupiterServiceException(
                f"Unexpected error: {str(e)}",
                details={"error_type": type(e).__name__}
            )
    
    async def get_swap_transaction(
        self,
        quote_response: Dict[str, Any],
        user_public_key: str,
        wrap_unwrap_sol: bool = True,
        priority_fee_lamports: Optional[int] = None,
        dynamic_compute_unit_limit: bool = True
    ) -> Optional[str]:
        """Build a swap transaction from a quote.
        
        This method takes a quote response and builds a serialized transaction
        that can be signed and sent by the user's wallet.
        
        Args:
            quote_response: Quote response from get_quote()
            user_public_key: User's wallet public key
            wrap_unwrap_sol: Auto wrap/unwrap SOL to WSOL (default: True)
            priority_fee_lamports: Priority fee in lamports (optional)
                                  If not set, uses auto priority fee
            dynamic_compute_unit_limit: Simulate to get accurate compute units (default: True)
        
        Returns:
            Base64-encoded serialized transaction string ready to be signed,
            or None if transaction building fails.
        
        Raises:
            ValidationException: If inputs are invalid
            JupiterServiceException: If transaction building fails
        
        Examples:
            >>> quote = await service.get_quote(...)
            >>> tx = await service.get_swap_transaction(
            ...     quote_response=quote,
            ...     user_public_key="7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
            ... )
            >>> # Send tx to wallet for signing
        """
        try:
            # Validate user public key
            user_public_key = validate_solana_address(user_public_key, "userPublicKey")
            
            # Build request body
            request_body = {
                "userPublicKey": user_public_key,
                "quoteResponse": quote_response,
                "wrapAndUnwrapSol": wrap_unwrap_sol,
                "dynamicComputeUnitLimit": dynamic_compute_unit_limit,
            }
            
            # Add priority fee if specified
            if priority_fee_lamports is not None:
                request_body["prioritizationFeeLamports"] = {
                    "priorityLevelWithMaxLamports": {
                        "priorityLevel": "high",
                        "maxLamports": priority_fee_lamports,
                        "global": False
                    }
                }
            
            logger.info(f"Building swap transaction for user: {user_public_key[:8]}...")
            
            # Make API request
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/swap",
                    json=request_body,
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    swap_response = response.json()
                    transaction = swap_response.get("swapTransaction")
                    
                    if transaction:
                        logger.info("Swap transaction built successfully")
                        return transaction
                    else:
                        logger.error("No transaction in Jupiter response")
                        raise JupiterServiceException(
                            "No transaction returned from Jupiter",
                            details={"response": swap_response}
                        )
                else:
                    error_detail = response.text
                    logger.error(
                        f"Jupiter swap failed: {response.status_code} - {error_detail}"
                    )
                    raise JupiterServiceException(
                        f"Failed to build swap transaction (status {response.status_code})",
                        details={"status_code": response.status_code, "error": error_detail}
                    )
        
        except ValidationException:
            raise
        except JupiterServiceException:
            raise
        except httpx.TimeoutException:
            logger.error("Jupiter API timeout")
            raise JupiterServiceException(
                "Jupiter API request timed out",
                details={"timeout": self.timeout}
            )
        except Exception as e:
            logger.error(f"Unexpected error building swap transaction: {e}")
            raise JupiterServiceException(
                f"Unexpected error: {str(e)}",
                details={"error_type": type(e).__name__}
            )
    
    async def health_check(self) -> bool:
        """Check if Jupiter API is available.
        
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try to get a simple quote
                response = await client.get(
                    f"{self.api_url}/quote",
                    params={
                        "inputMint": "So11111111111111111111111111111111111111112",
                        "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                        "amount": "1000000000",
                        "slippageBps": "50"
                    },
                    headers=self._get_headers()
                )
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Jupiter health check failed: {e}")
            return False


# Singleton instance
_service: Optional[JupiterService] = None


def get_jupiter_service() -> JupiterService:
    """Get or create the Jupiter service singleton instance.
    
    Returns:
        JupiterService instance
    
    Examples:
        >>> service = get_jupiter_service()
        >>> quote = await service.get_quote(...)
    """
    global _service
    if _service is None:
        _service = JupiterService()
    return _service
