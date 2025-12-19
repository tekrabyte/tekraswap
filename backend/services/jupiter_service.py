import httpx
from typing import Optional, Dict, Any
import logging
from config import settings

logger = logging.getLogger(__name__)

class JupiterService:
    """Service for interacting with Jupiter Aggregator API"""
    
    def __init__(self):
        self.base_url = settings.JUPITER_API_URL
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def get_quote(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: int = 50,
        only_direct_routes: bool = False,
        as_legacy_transaction: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Fetch a quote from Jupiter Aggregator"""
        
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "slippageBps": slippage_bps,
            "onlyDirectRoutes": str(only_direct_routes).lower(),
            "asLegacyTransaction": str(as_legacy_transaction).lower(),
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info(f"Fetching quote: {input_mint} -> {output_mint}, amount: {amount}")
                response = await client.get(
                    f"{self.base_url}/quote",
                    params=params,
                    headers=self.headers
                )
                response.raise_for_status()
                quote_data = response.json()
                logger.info(f"Quote received: outAmount={quote_data.get('outAmount')}")
                return quote_data
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching quote: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error fetching quote: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching quote: {e}")
            return None
    
    async def get_swap_transaction(
        self,
        user_public_key: str,
        quote_response: Dict[str, Any],
        wrap_and_unwrap_sol: bool = True,
        use_shared_accounts: bool = True,
        fee_account: Optional[str] = None,
        compute_unit_price_micro_lamports: Optional[int] = None,
        as_legacy_transaction: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get swap transaction from Jupiter"""
        
        payload = {
            "userPublicKey": user_public_key,
            "quoteResponse": quote_response,
            "wrapAndUnwrapSol": wrap_and_unwrap_sol,
            "useSharedAccounts": use_shared_accounts,
            "asLegacyTransaction": as_legacy_transaction,
        }
        
        if fee_account:
            payload["feeAccount"] = fee_account
        
        if compute_unit_price_micro_lamports is not None:
            payload["computeUnitPriceMicroLamports"] = compute_unit_price_micro_lamports
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info(f"Creating swap transaction for user: {user_public_key}")
                response = await client.post(
                    f"{self.base_url}/swap",
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()
                swap_data = response.json()
                logger.info("Swap transaction created successfully")
                return swap_data
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error creating swap: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error creating swap: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating swap: {e}")
            return None

jupiter_service = JupiterService()
