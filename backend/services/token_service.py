"""Token service for Helius RPC integration"""
import os
import httpx
import logging
from typing import Optional, Dict, List
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed

logger = logging.getLogger(__name__)


class TokenService:
    """Service for token-related operations using Helius RPC"""
    
    def __init__(self):
        self.helius_rpc_url = os.environ.get('https://mainnet.helius-rpc.com/?api-key=c85bff04-bd73-403e-9ac8-9c949eb1b26c')
        if not self.helius_rpc_url:
            raise ValueError("HELIUS_RPC_URL not set in environment")
        self.client = AsyncClient(self.helius_rpc_url, commitment=Confirmed)
        
        # Default token list with user's tokens
        self.default_tokens = [
            {
                "address": "So11111111111111111111111111111111111111112",
                "symbol": "SOL",
                "name": "Wrapped SOL",
                "decimals": 9,
                "logoURI": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/So11111111111111111111111111111111111111112/logo.png"
            },
            {
                "address": "4ymWDE5kwxZ5rxN3mWLvJEBHESbZSiqBuvWmSVcGqZdj",
                "symbol": "TEKRA",
                "name": "TekraByte (Official)",
                "decimals": 9,
                "logoURI": "https://tekrabyte.com/crypto/meme_tekrabyte/logo.png"
            },
            {
                "address": "FShCGqGUWRZkqovteJBGegUJAcjRzHZiBmHYGgSqpump",
                "symbol": "TEKRA", 
                "name": "TekraByte (MemeCoin)",
                "decimals": 9,
                "logoURI": "https://tekrabyte.com/crypto/meme_tekrabyte/logo.png"
            },
            {
                "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "symbol": "SOL",
                "name": "Solana",
                "decimals": 6,
                "logoURI": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v/logo.png"
            },
            {
                "address": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
                "symbol": "SOL",
                "name": "Solana",
                "decimals": 6,
                "logoURI": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB/logo.png"
            }
        ]
    
    async def get_token_list(self) -> List[Dict]:
        """Get list of supported tokens"""
        return self.default_tokens
    
    async def get_token_metadata(self, token_address: str) -> Optional[Dict]:
        """Get token metadata from Helius DAS API"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as http_client:
                # Use Helius DAS API to get token metadata
                response = await http_client.post(
                    self.helius_rpc_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": "metadata-request",
                        "method": "getAsset",
                        "params": {
                            "id": token_address
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "result" in data and data["result"]:
                        result = data["result"]
                        content = result.get("content", {})
                        token_info = result.get("token_info", {})
                        
                        return {
                            "address": token_address,
                            "name": content.get("metadata", {}).get("name", "Unknown Token"),
                            "symbol": content.get("metadata", {}).get("symbol", "UNKNOWN"),
                            "decimals": token_info.get("decimals", 9),
                            "logoURI": content.get("links", {}).get("image"),
                            "supply": token_info.get("supply"),
                            "price_per_token": token_info.get("price_info", {}).get("price_per_token")
                        }
                
                # Fallback: try to get from token list
                for token in self.default_tokens:
                    if token["address"] == token_address:
                        return token
                
                # Return basic info if metadata not found
                return {
                    "address": token_address,
                    "name": "Unknown Token",
                    "symbol": "UNKNOWN",
                    "decimals": 9,
                    "logoURI": None
                }
                
        except Exception as e:
            logger.error(f"Error fetching token metadata: {e}")
            # Return from default list if available
            for token in self.default_tokens:
                if token["address"] == token_address:
                    return token
            return None
    
    async def get_token_balance(self, wallet_address: str, token_mint: str) -> Optional[Dict]:
        """Get token balance for a wallet"""
        try:
            wallet_pubkey = Pubkey.from_string(wallet_address)
            
            # Check if it's SOL (native)
            if token_mint == "So11111111111111111111111111111111111111112":
                balance_response = await self.client.get_balance(wallet_pubkey)
                if balance_response.value:
                    return {
                        "balance": balance_response.value / 1e9,  # Convert lamports to SOL
                        "decimals": 9,
                        "uiAmount": balance_response.value / 1e9
                    }
            else:
                # Get token accounts for the wallet
                token_mint_pubkey = Pubkey.from_string(token_mint)
                
                # Use getTokenAccountsByOwner
                response = await self.client.get_token_accounts_by_owner(
                    wallet_pubkey,
                    {"mint": token_mint_pubkey}
                )
                
                if response.value:
                    for account_info in response.value:
                        account_data = account_info.account.data
                        # Parse token account data
                        if hasattr(account_data, 'parsed'):
                            info = account_data.parsed.get('info', {})
                            token_amount = info.get('tokenAmount', {})
                            return {
                                "balance": float(token_amount.get('amount', 0)),
                                "decimals": token_amount.get('decimals', 9),
                                "uiAmount": float(token_amount.get('uiAmount', 0))
                            }
                
                # No balance found
                return {
                    "balance": 0,
                    "decimals": 9,
                    "uiAmount": 0
                }
                
        except Exception as e:
            logger.error(f"Error fetching token balance: {e}")
            return None
    
    async def get_multiple_token_balances(
        self, wallet_address: str, token_mints: List[str]
    ) -> Dict[str, Dict]:
        """Get balances for multiple tokens"""
        balances = {}
        for mint in token_mints:
            balance = await self.get_token_balance(wallet_address, mint)
            if balance:
                balances[mint] = balance
        return balances
    
    async def validate_token(self, token_address: str) -> bool:
        """Validate if token address is valid and exists"""
        try:
            # Try to get token metadata
            metadata = await self.get_token_metadata(token_address)
            return metadata is not None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False
    
    async def get_token_price_chart(self, token_address: str, interval: str = "1h") -> Optional[Dict]:
        """Get token price chart data from DexScreener"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as http_client:
                # Get token info from DexScreener
                response = await http_client.get(
                    f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Get the first pair (usually the most liquid)
                    if data.get("pairs") and len(data["pairs"]) > 0:
                        pair = data["pairs"][0]
                        
                        # Extract price history if available
                        price_change = pair.get("priceChange", {})
                        current_price = float(pair.get("priceUsd", 0))
                        
                        # Generate chart data based on price changes
                        from datetime import datetime, timedelta, timezone
                        now = datetime.now(timezone.utc)
                        chart_data = []
                        
                        # Calculate historical prices based on percentage changes
                        h24_change = float(price_change.get("h24", 0)) / 100 if price_change.get("h24") else 0
                        h6_change = float(price_change.get("h6", 0)) / 100 if price_change.get("h6") else 0
                        h1_change = float(price_change.get("h1", 0)) / 100 if price_change.get("h1") else 0
                        m5_change = float(price_change.get("m5", 0)) / 100 if price_change.get("m5") else 0
                        
                        # Calculate base prices
                        price_24h_ago = current_price / (1 + h24_change) if h24_change != -1 else current_price
                        price_6h_ago = current_price / (1 + h6_change) if h6_change != -1 else current_price
                        price_1h_ago = current_price / (1 + h1_change) if h1_change != -1 else current_price
                        
                        # Generate 24 hourly data points with interpolation
                        for i in range(24):
                            hours_ago = 24 - i
                            timestamp = now - timedelta(hours=hours_ago)
                            
                            # Interpolate price based on available data points
                            if hours_ago >= 24:
                                price = price_24h_ago
                            elif hours_ago >= 6:
                                # Interpolate between 24h and 6h
                                ratio = (24 - hours_ago) / 18
                                price = price_24h_ago + (price_6h_ago - price_24h_ago) * ratio
                            elif hours_ago >= 1:
                                # Interpolate between 6h and 1h
                                ratio = (6 - hours_ago) / 5
                                price = price_6h_ago + (price_1h_ago - price_6h_ago) * ratio
                            else:
                                # Interpolate between 1h and current
                                ratio = (1 - hours_ago)
                                price = price_1h_ago + (current_price - price_1h_ago) * ratio
                            
                            chart_data.append({
                                "timestamp": int(timestamp.timestamp() * 1000),
                                "price": price,
                                "volume": float(pair.get("volume", {}).get("h24", 0)) / 24  # Approximate hourly volume
                            })
                        
                        return {
                            "data": chart_data,
                            "current_price": current_price,
                            "price_change_24h": h24_change,
                            "volume_24h": float(pair.get("volume", {}).get("h24", 0)),
                            "pair_address": pair.get("pairAddress"),
                            "dex": pair.get("dexId")
                        }
                
                logger.warning(f"No pairs found for token {token_address} on DexScreener")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching price chart from DexScreener: {e}")
            return None
    
    async def close(self):
        """Close the RPC client"""
        await self.client.close()


# Singleton instance
_token_service_instance = None


def get_token_service() -> TokenService:
    """Get or create token service instance"""
    global _token_service_instance
    if _token_service_instance is None:
        _token_service_instance = TokenService()
    return _token_service_instance
