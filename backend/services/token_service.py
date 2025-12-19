"""Token Service for Solana blockchain interactions.

This module provides comprehensive token management functionality including:
- Token metadata retrieval via Helius RPC
- Token balance queries for wallets
- Real-time price data from DexScreener
- Historical price charts from GeckoTerminal

Integration:
- Helius RPC: For Solana blockchain data and DAS API
- DexScreener: For real-time token prices and market data
- GeckoTerminal: For historical OHLCV chart data

Documentation:
- Helius: https://www.helius.dev/docs/rpc/guides/overview
- DexScreener: https://api.dexscreener.com
- GeckoTerminal: https://api.geckoterminal.com
"""

import os
import httpx
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

# Solana blockchain libraries
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solana.rpc.types import TokenAccountOpts

from utils.exceptions import TokenServiceException, ExternalAPIException
from utils.validators import validate_solana_address

logger = logging.getLogger(__name__)

# Native SOL token mint address
SOL_MINT = "So11111111111111111111111111111111111111112"


class TokenService:
    """Service for managing Solana token operations.
    
    This service provides comprehensive token functionality including:
    - Fetching token metadata (name, symbol, decimals, logo)
    - Querying token balances for wallets
    - Retrieving real-time price data
    - Getting historical price charts
    
    Attributes:
        helius_rpc_url: Helius RPC endpoint URL
        client: Async Solana RPC client
        default_tokens: Dictionary of pre-configured popular tokens
    """
    
    def __init__(self):
        """Initialize Token Service.
        
        Environment Variables:
            HELIUS_RPC_URL: Helius RPC endpoint (required for best performance)
                          Falls back to public Solana node if not set.
        
        Example:
            HELIUS_RPC_URL="https://mainnet.helius-rpc.com/?api-key=YOUR_KEY"
        """
        # Get Helius RPC URL from environment
        self.helius_rpc_url = os.environ.get('HELIUS_RPC_URL')
        if not self.helius_rpc_url:
            self.helius_rpc_url = "https://api.mainnet-beta.solana.com"
            logger.warning(
                "HELIUS_RPC_URL not set. Using public Solana node. "
                "Performance may be limited. Get Helius key at: https://www.helius.dev"
            )

        # Initialize Solana RPC client
        self.client = AsyncClient(self.helius_rpc_url, commitment=Confirmed)
        
        # Pre-configured popular tokens with static metadata
        # This provides fallback data and improves response time
        self.default_tokens = {
            SOL_MINT: {
                "address": SOL_MINT,
                "symbol": "SOL",
                "name": "Solana",
                "decimals": 9,
                "logoURI": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/So11111111111111111111111111111111111111112/logo.png",
            },
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": {
                "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "symbol": "USDC",
                "name": "USD Coin",
                "decimals": 6,
                "logoURI": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v/logo.png",
            },
            "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": {
                "address": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
                "symbol": "USDT",
                "name": "USDT",
                "decimals": 6,
                "logoURI": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB/logo.png",
            },
            # User's TEKRA tokens
            "4ymWDE5kwxZ5rxN3mWLvJEBHESbZSiqBuvWmSVcGqZdj": {
                "address": "4ymWDE5kwxZ5rxN3mWLvJEBHESbZSiqBuvWmSVcGqZdj",
                "symbol": "TEKRA",
                "name": "TEKRA Token 1",
                "decimals": 9,
                "logoURI": None,
            },
            "FShCGqGUWRZkqovteJBGegUJAcjRzHZiBmHYGgSqpump": {
                "address": "FShCGqGUWRZkqovteJBGegUJAcjRzHZiBmHYGgSqpump",
                "symbol": "TEKRA",
                "name": "TEKRA Token 2",
                "decimals": 9,
                "logoURI": None,
            }
        }

    async def get_token_list(self) -> List[Dict[str, Any]]:
        """Get list of default/popular tokens.
        
        Returns a list of pre-configured popular tokens with their metadata.
        This is used for token selection UI and quick access to common tokens.
        
        Returns:
            List of token dictionaries containing:
            - address: Token mint address
            - symbol: Token symbol (e.g., "SOL", "USDC")
            - name: Full token name
            - decimals: Number of decimal places
            - logoURI: URL to token logo image
        
        Examples:
            >>> service = TokenService()
            >>> tokens = await service.get_token_list()
            >>> print(tokens[0]['symbol'])
            'SOL'
        """
        return list(self.default_tokens.values())

    async def _fetch_dexscreener_data(self, token_address: str) -> Optional[Dict]:
        """Helper untuk mengambil data real-time dari DexScreener"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as http_client:
                url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
                response = await http_client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("pairs"):
                        # Ambil pair dengan likuiditas tertinggi
                        # Filter pair yang di Solana saja
                        pairs = [p for p in data["pairs"] if p.get("chainId") == "solana"]
                        if not pairs:
                            return None
                            
                        pair = pairs[0] # Pair terbesar
                        return {
                            "price_usd": float(pair.get("priceUsd", 0)),
                            "volume_24h": float(pair.get("volume", {}).get("h24", 0)),
                            "market_cap": float(pair.get("fdv", 0) or pair.get("marketCap", 0)),
                            "pair_address": pair.get("pairAddress"), # PENTING UNTUK CHART
                            "pair_info": pair
                        }
        except Exception as e:
            logger.warning(f"DexScreener fetch failed for {token_address}: {e}")
        return None

    async def get_token_metadata(self, token_address: str) -> Dict:
        """
        Menggabungkan Metadata Statis (Nama/Logo) dengan Data Dinamis (Harga).
        """
        # 1. Siapkan Metadata Dasar
        metadata = {
            "address": token_address,
            "name": "Unknown Token",
            "symbol": "UNK",
            "decimals": 9,
            "logoURI": None,
            "price_per_token": 0,
            "volume_24h": 0,
            "market_cap": 0
        }

        # Cek default list
        if token_address in self.default_tokens:
            metadata.update(self.default_tokens[token_address])

        # 2. Ambil Harga Real-time (DexScreener)
        market_data = await self._fetch_dexscreener_data(token_address)

        if market_data:
            metadata["price_per_token"] = market_data["price_usd"]
            metadata["volume_24h"] = market_data["volume_24h"]
            metadata["market_cap"] = market_data["market_cap"]
            
            # Isi nama/symbol jika masih UNK
            if metadata["symbol"] == "UNK":
                pair = market_data["pair_info"]
                base = pair.get("baseToken", {})
                metadata["name"] = base.get("name", "Unknown")
                metadata["symbol"] = base.get("symbol", "UNK")
                metadata["logoURI"] = pair.get("info", {}).get("imageUrl")
                
            return metadata

        # 3. Fallback ke RPC Helius (Metadata Only)
        if metadata["symbol"] == "UNK":
            try:
                async with httpx.AsyncClient(timeout=3.0) as http_client:
                    response = await http_client.post(
                        self.helius_rpc_url,
                        json={
                            "jsonrpc": "2.0", "id": "metadata", 
                            "method": "getAsset", "params": {"id": token_address}
                        }
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if "result" in data:
                            content = data["result"].get("content", {})
                            token_info = data["result"].get("token_info", {})
                            
                            metadata["name"] = content.get("metadata", {}).get("name", "Unknown")
                            metadata["symbol"] = content.get("metadata", {}).get("symbol", "UNK")
                            metadata["decimals"] = token_info.get("decimals", 9)
                            metadata["logoURI"] = content.get("links", {}).get("image")
            except Exception:
                pass

        return metadata

    async def get_token_balance(self, wallet: str, mint: str):
        """Mendapatkan saldo token dengan parsing JSON yang benar"""
        try:
            if not wallet or len(wallet) < 30: return {"balance": 0, "uiAmount": 0, "decimals": 0}
            
            pubkey = Pubkey.from_string(wallet)

            # KASUS A: Token Native (SOL)
            if mint == SOL_MINT: 
                bal = await self.client.get_balance(pubkey)
                val = bal.value or 0
                return {
                    "balance": val,
                    "uiAmount": val / 1e9,
                    "decimals": 9
                }
            
            # KASUS B: Token SPL
            mint_pubkey = Pubkey.from_string(mint)
            resp = await self.client.get_token_accounts_by_owner(
                pubkey, 
                TokenAccountOpts(mint=mint_pubkey, encoding="jsonParsed")
            )
            
            if resp.value:
                acc_data = resp.value[0].account.data
                parsed_data = acc_data.parsed if hasattr(acc_data, 'parsed') else acc_data
                
                if isinstance(parsed_data, dict):
                    amount_info = parsed_data['info']['tokenAmount']
                else:
                    amount_info = parsed_data.info['tokenAmount']

                return {
                    "balance": float(amount_info['amount']),
                    "uiAmount": float(amount_info['uiAmount']),
                    "decimals": int(amount_info['decimals'])
                }
            
            return {"balance": 0, "uiAmount": 0, "decimals": 0}

        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return {"balance": 0, "uiAmount": 0, "decimals": 0}

    async def get_wallet_portfolio(self, wallet_address: str) -> Dict:
        """
        Mendapatkan portfolio lengkap wallet termasuk semua token dan total balance USD.
        """
        try:
            if not wallet_address or len(wallet_address) < 30:
                return {"total_usd": 0, "tokens": [], "error": "Invalid wallet address"}
            
            pubkey = Pubkey.from_string(wallet_address)
            portfolio_tokens = []
            total_value_usd = 0
            
            # 1. Ambil SOL Balance
            try:
                sol_balance_resp = await self.client.get_balance(pubkey)
                sol_balance = (sol_balance_resp.value or 0) / 1e9
                
                if sol_balance > 0:
                    sol_metadata = await self.get_token_metadata(SOL_MINT)
                    sol_price = sol_metadata.get("price_per_token", 0)
                    sol_value = sol_balance * sol_price
                    
                    portfolio_tokens.append({
                        "address": SOL_MINT,
                        "symbol": "SOL",
                        "name": "Solana",
                        "balance": sol_balance,
                        "decimals": 9,
                        "price_usd": sol_price,
                        "value_usd": sol_value,
                        "logoURI": sol_metadata.get("logoURI"),
                        "volume_24h": sol_metadata.get("volume_24h", 0),
                        "market_cap": sol_metadata.get("market_cap", 0)
                    })
                    total_value_usd += sol_value
            except Exception as e:
                logger.error(f"Error fetching SOL balance: {e}")
            
            # 2. Ambil semua SPL Token Accounts
            try:
                # Get all token accounts owned by wallet
                token_accounts = await self.client.get_token_accounts_by_owner(
                    pubkey,
                    TokenAccountOpts(encoding="jsonParsed")
                )
                
                # Process each token account
                for account in token_accounts.value:
                    try:
                        acc_data = account.account.data
                        parsed_data = acc_data.parsed if hasattr(acc_data, 'parsed') else acc_data
                        
                        if isinstance(parsed_data, dict):
                            info = parsed_data['info']
                        else:
                            info = parsed_data.info
                        
                        mint = info['mint']
                        token_amount = info['tokenAmount']
                        balance = float(token_amount['uiAmount'] or 0)
                        
                        # Skip jika balance = 0
                        if balance <= 0:
                            continue
                        
                        # Ambil metadata + harga
                        metadata = await self.get_token_metadata(mint)
                        price = metadata.get("price_per_token", 0)
                        value = balance * price
                        
                        portfolio_tokens.append({
                            "address": mint,
                            "symbol": metadata.get("symbol", "UNK"),
                            "name": metadata.get("name", "Unknown"),
                            "balance": balance,
                            "decimals": int(token_amount['decimals']),
                            "price_usd": price,
                            "value_usd": value,
                            "logoURI": metadata.get("logoURI"),
                            "volume_24h": metadata.get("volume_24h", 0),
                            "market_cap": metadata.get("market_cap", 0)
                        })
                        
                        # Tambahkan ke total BAHKAN jika price = 0
                        # Karena user mau "sekecil apapun"
                        total_value_usd += value
                        
                    except Exception as e:
                        logger.error(f"Error processing token account: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error fetching token accounts: {e}")
            
            # 3. Sort by value (terbesar dulu)
            portfolio_tokens.sort(key=lambda x: x["value_usd"], reverse=True)
            
            return {
                "wallet": wallet_address,
                "total_usd": total_value_usd,
                "token_count": len(portfolio_tokens),
                "tokens": portfolio_tokens
            }
            
        except Exception as e:
            logger.error(f"Error in get_wallet_portfolio: {e}")
            return {
                "wallet": wallet_address,
                "total_usd": 0,
                "token_count": 0,
                "tokens": [],
                "error": str(e)
            }

    async def get_token_price_chart(self, token_address: str, interval: str) -> Optional[Dict]:
        """
        Ambil Chart REAL dari GeckoTerminal menggunakan Pair Address dari DexScreener.
        TIDAK ADA LAGI MOCK DATA.
        """
        # 1. Cari Pair Address dulu di DexScreener
        market_data = await self._fetch_dexscreener_data(token_address)
        
        if not market_data or not market_data.get("pair_address"):
            logger.warning(f"No pair found for chart: {token_address}")
            return {"data": [], "current_price": 0, "mock": False}

        current_price = market_data["price_usd"]
        pair_address = market_data["pair_address"]

        # 2. Fetch Candle Data dari GeckoTerminal (Gratis & Public)
        # Mapping interval: '1h' -> 'hour', '1d' -> 'day'
        gt_timeframe = "hour" if interval == "1h" else "day"
        limit = 24 if interval == "1h" else 30

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # API GeckoTerminal untuk Solana
                url = f"https://api.geckoterminal.com/api/v2/networks/solana/pools/{pair_address}/ohlcv/{gt_timeframe}"
                
                resp = await client.get(url, params={"limit": limit})
                
                if resp.status_code == 200:
                    data = resp.json()
                    # Format GeckoTerminal: [time, open, high, low, close, volume]
                    ohlcv_list = data.get("data", {}).get("attributes", {}).get("ohlcv_list", [])
                    
                    chart_data = []
                    for item in ohlcv_list:
                        # item = [timestamp, open, high, low, close, volume]
                        chart_data.append({
                            "timestamp": int(item[0]) * 1000, # Convert ke ms
                            "price": float(item[4]),          # Close price
                            "volume": float(item[5])
                        })
                    
                    # Sort biar urut dari lama ke baru (kadang API return terbalik)
                    chart_data.sort(key=lambda x: x["timestamp"])

                    return {
                        "data": chart_data,
                        "current_price": current_price,
                        "mock": False # Real Data!
                    }
                else:
                    logger.error(f"GeckoTerminal Error: {resp.status_code} - {resp.text}")

        except Exception as e:
            logger.error(f"Chart fetch error: {e}")

        # Jika gagal fetch chart, return kosong (jangan mock biar user tau errornya)
        return {
            "data": [],
            "current_price": current_price,
            "mock": False
        }

# Singleton Instance
_service = None
def get_token_service():
    global _service
    if _service is None:
        _service = TokenService()
    return _service