import httpx
from typing import Optional, Dict, Any, List
import logging
from config import settings
from database import get_database

logger = logging.getLogger(__name__)

class TokenService:
    """Service for fetching token metadata"""
    
    def __init__(self):
        self.rpc_url = settings.SOLANA_RPC_URL
    
    async def get_token_metadata(
        self,
        mint_address: str,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get token metadata from cache or fetch from blockchain"""
        
        try:
            db = await get_database()
            
            # Check cache first
            if use_cache:
                cached = await db.tokens.find_one({"mint": mint_address})
                if cached:
                    logger.info(f"Token metadata found in cache: {mint_address}")
                    cached.pop('_id', None)
                    return cached
            
            # Fetch from Jupiter token list API
            metadata = await self._fetch_from_jupiter_list(mint_address)
            
            if metadata:
                # Cache the metadata
                await db.tokens.update_one(
                    {"mint": mint_address},
                    {"$set": metadata},
                    upsert=True
                )
                logger.info(f"Token metadata cached: {mint_address}")
                return metadata
            
            # If not found, try to get basic info from RPC
            basic_info = await self._fetch_basic_info(mint_address)
            if basic_info:
                await db.tokens.update_one(
                    {"mint": mint_address},
                    {"$set": basic_info},
                    upsert=True
                )
                return basic_info
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching token metadata: {e}")
            return None
    
    async def _fetch_from_jupiter_list(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """Fetch token from Jupiter's token list"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("https://token.jup.ag/all")
                response.raise_for_status()
                tokens = response.json()
                
                for token in tokens:
                    if token.get("address") == mint_address:
                        return {
                            "mint": token.get("address"),
                            "symbol": token.get("symbol", "UNKNOWN"),
                            "name": token.get("name", "Unknown Token"),
                            "decimals": token.get("decimals", 9),
                            "logoURI": token.get("logoURI"),
                            "tags": token.get("tags", [])
                        }
                return None
        except Exception as e:
            logger.error(f"Error fetching from Jupiter list: {e}")
            return None
    
    async def _fetch_basic_info(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """Fetch basic token info from Solana RPC"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getAccountInfo",
                    "params": [
                        mint_address,
                        {"encoding": "jsonParsed"}
                    ]
                }
                
                response = await client.post(self.rpc_url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                if data.get("result") and data["result"].get("value"):
                    account_data = data["result"]["value"]["data"]
                    if isinstance(account_data, dict) and "parsed" in account_data:
                        parsed = account_data["parsed"]
                        if parsed.get("type") == "mint":
                            info = parsed.get("info", {})
                            return {
                                "mint": mint_address,
                                "symbol": "TOKEN",
                                "name": f"Token {mint_address[:8]}",
                                "decimals": info.get("decimals", 9),
                                "logoURI": None,
                                "tags": []
                            }
                
                return None
        except Exception as e:
            logger.error(f"Error fetching basic info from RPC: {e}")
            return None
    
    async def search_tokens(
        self,
        query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search tokens by symbol or name"""
        try:
            db = await get_database()
            results = await db.tokens.find(
                {
                    "$or": [
                        {"symbol": {"$regex": query, "$options": "i"}},
                        {"name": {"$regex": query, "$options": "i"}}
                    ]
                }
            ).limit(limit).to_list(length=limit)
            
            for result in results:
                result.pop('_id', None)
            
            return results
        except Exception as e:
            logger.error(f"Error searching tokens: {e}")
            return []

token_service = TokenService()
