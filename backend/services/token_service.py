import os
import httpx
import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List

# LIBRARY SOLANA PENTING
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solana.rpc.types import TokenAccountOpts  # <--- WAJIB ADA UNTUK BACA SALDO

logger = logging.getLogger(__name__)

class TokenService:
    def __init__(self):
        # Gunakan RPC URL dari env, atau fallback ke public node jika kosong
        self.helius_rpc_url = os.environ.get('HELIUS_RPC_URL')
        if not self.helius_rpc_url:
            self.helius_rpc_url = "https://api.mainnet-beta.solana.com" # Public Node
            logger.warning("HELIUS_RPC_URL tidak sett, menggunakan Public Node (Mungkin lambat)")

        self.client = AsyncClient(self.helius_rpc_url, commitment=Confirmed)
        
        # Daftar Token Default (Agar data muncul instan untuk token populer)
        self.default_tokens = [
            {
                "address": "So11111111111111111111111111111111111111112",
                "symbol": "SOL",
                "name": "Solana",
                "decimals": 9,
                "logoURI": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/So11111111111111111111111111111111111111112/logo.png",
                "price_per_token": 0
            },
            {
                "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "symbol": "USDC",
                "name": "USD Coin",
                "decimals": 6,
                "logoURI": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v/logo.png",
                "price_per_token": 1.0
            }
        ]

    async def get_token_list(self) -> List[Dict]:
        return self.default_tokens

    async def get_token_metadata(self, token_address: str) -> Dict:
        """Strategi: Cek Default -> Cek DexScreener (Cepat) -> Cek Helius (Lengkap) -> Fallback"""
        
        # 1. Cek Default List
        for token in self.default_tokens:
            if token["address"] == token_address:
                return token

        # 2. Cek DexScreener (Paling cepat & data market lengkap)
        try:
            async with httpx.AsyncClient(timeout=3.0) as http_client:
                response = await http_client.get(f"https://api.dexscreener.com/latest/dex/tokens/{token_address}")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("pairs"):
                        pair = data["pairs"][0]
                        base = pair.get("baseToken", {})
                        if base.get("address") == token_address:
                            return {
                                "address": token_address,
                                "name": base.get("name", "Unknown Token"),
                                "symbol": base.get("symbol", "UNK"),
                                "decimals": 9, 
                                "logoURI": pair.get("info", {}).get("imageUrl"),
                                "supply": 0,
                                "price_per_token": float(pair.get("priceUsd", 0)),
                                "market_cap": pair.get("fdv", 0)
                            }
        except Exception:
            pass # Lanjut ke Helius jika DexScreener gagal

        # 3. Cek Helius / RPC (Fallback)
        try:
            # Note: Method 'getAsset' hanya jalan di Helius/DAS API, bukan node biasa
            async with httpx.AsyncClient(timeout=3.0) as http_client:
                response = await http_client.post(
                    self.helius_rpc_url,
                    json={
                        "jsonrpc": "2.0", "id": "metadata", "method": "getAsset", 
                        "params": {"id": token_address}
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    if "result" in data:
                        res = data["result"]
                        content = res.get("content", {})
                        token_info = res.get("token_info", {})
                        return {
                            "address": token_address,
                            "name": content.get("metadata", {}).get("name", "Unknown"),
                            "symbol": content.get("metadata", {}).get("symbol", "UNK"),
                            "decimals": token_info.get("decimals", 9),
                            "logoURI": content.get("links", {}).get("image"),
                            "price_per_token": token_info.get("price_info", {}).get("price_per_token", 0)
                        }
        except Exception as e:
            logger.error(f"Metadata RPC error: {e}")

        # 4. Final Fallback (Agar UI tidak crash)
        return {
            "address": token_address,
            "name": f"Token {token_address[:4]}...",
            "symbol": "UNKNOWN",
            "decimals": 9,
            "logoURI": None,
            "price_per_token": 0
        }

    async def get_token_balance(self, wallet: str, mint: str):
        """Mendapatkan saldo token dengan parsing JSON yang benar"""
        try:
            if not wallet or len(wallet) < 30: return {"balance": 0, "uiAmount": 0, "decimals": 0}
            
            pubkey = Pubkey.from_string(wallet)

            # KASUS A: Token Native (SOL)
            if mint == "So11111111111111111111111111111111111111112": 
                bal = await self.client.get_balance(pubkey)
                val = bal.value or 0
                return {
                    "balance": val,
                    "uiAmount": val / 1e9,
                    "decimals": 9
                }
            
            # KASUS B: Token SPL (USDC, TEKRA, dll)
            mint_pubkey = Pubkey.from_string(mint)
            
            # --- FIX UTAMA: encoding="jsonParsed" ---
            resp = await self.client.get_token_accounts_by_owner(
                pubkey, 
                TokenAccountOpts(mint=mint_pubkey, encoding="jsonParsed")
            )
            
            if resp.value:
                # Ambil data akun pertama
                data = resp.value[0].account.data.parsed['info']['tokenAmount']
                return {
                    "balance": float(data['amount']),      # Raw
                    "uiAmount": float(data['uiAmount']),   # Readable (e.g. 10.5)
                    "decimals": int(data['decimals'])
                }
            
            return {"balance": 0, "uiAmount": 0, "decimals": 0}

        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return {"balance": 0, "uiAmount": 0, "decimals": 0}

    async def get_token_price_chart(self, token_address: str, interval: str) -> Optional[Dict]:
        """Ambil chart dari DexScreener, atau buat Mock Data jika kosong"""
        price = 0.1
        
        # 1. Coba ambil harga Real
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(f"https://api.dexscreener.com/latest/dex/tokens/{token_address}")
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("pairs"):
                        price = float(data["pairs"][0].get("priceUsd", 0))
        except:
            pass

        # 2. Buat Data Chart (Mock) agar Frontend tidak blank
        # Kita generate 24 titik data (1 hari) di sekitar harga asli
        now = datetime.now(timezone.utc)
        chart_data = []
        
        # Jika harga 0 (token baru/scam), set dummy price kecil
        base_price = price if price > 0 else 0.001 
        
        for i in range(24):
            ts = now - timedelta(hours=24-i)
            # Random movement +/- 3%
            random_var = random.uniform(0.97, 1.03)
            val = base_price * random_var
            
            chart_data.append({
                "timestamp": int(ts.timestamp() * 1000),
                "price": val,
                "volume": random.uniform(1000, 50000)
            })
        
        return {
            "data": chart_data,
            "current_price": base_price,
            "mock": True # Flag untuk frontend tau ini data estimasi
        }

# Singleton Instance
_service = None
def get_token_service():
    global _service
    if _service is None:
        _service = TokenService()
    return _service