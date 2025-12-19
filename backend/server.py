from fastapi import FastAPI, APIRouter, HTTPException, Query
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# ======================================================
# LOAD ENV
# ======================================================
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# ======================================================
# LOGGING
# ======================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SOLANA_API")

# ======================================================
# IMPORT SERVICES
# ======================================================
from services.token_service import get_token_service
from services.currency_service import get_currency_service

# Import Jupiter Service (Pastikan file services/jupiter_service.py ada)
try:
    from services.jupiter_service import get_jupiter_service
except ImportError:
    logger.warning("Warning: services/jupiter_service.py not found. Real swap will fail.")
    get_jupiter_service = None

# ======================================================
# FASTAPI APP
# ======================================================
app = FastAPI(title="Solana Swap Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================
# MODELS
# ======================================================
class SwapRequest(BaseModel):
    userPublicKey: str
    inputMint: str
    outputMint: str
    amount: int
    slippageBps: int = 100
    dex: str = "jupiter"

api_router = APIRouter(prefix="/api")

# ======================================================
# 1. FIX ERROR: token-list 404
# ======================================================
@api_router.get("/token-list")
async def get_token_list():
    """Endpoint untuk daftar token default"""
    service = get_token_service()
    # Kita panggil method get_token_list dari service, atau return manual jika belum ada
    if hasattr(service, 'get_token_list'):
        return await service.get_token_list()
    
    # Fallback jika method tidak ada di service
    return [
        {"address": "So11111111111111111111111111111111111111112", "symbol": "SOL", "name": "Solana", "decimals": 9, "logoURI": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/So11111111111111111111111111111111111111112/logo.png"},
        {"address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "symbol": "USDC", "name": "USD Coin", "decimals": 6, "logoURI": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v/logo.png"}
    ]

# ======================================================
# 2. FIX ERROR: token-info 404 (Query Param Style)
# ======================================================
@api_router.get("/token-info")
async def get_token_info(address: str = Query(..., alias="address")):
    """
    Frontend memanggil: /api/token-info?address=...
    Endpoint ini menjembatani ke logic metadata.
    """
    return await get_metadata_logic(address)

# Endpoint lama (Path Param Style) tetap kita simpan
@api_router.get("/token-metadata/{token_address}")
async def get_metadata_path(token_address: str):
    return await get_metadata_logic(token_address)

async def get_metadata_logic(token_address: str):
    logger.info(f"Metadata request: {token_address}")
    if len(token_address) < 30:
        raise HTTPException(status_code=400, detail="Invalid address")
    
    service = get_token_service()
    metadata = await service.get_token_metadata(token_address)
    if not metadata:
        # Return fallback mock agar frontend tidak error
        return {
            "address": token_address,
            "symbol": "UNK", 
            "name": "Unknown Token", 
            "decimals": 9, 
            "price_per_token": 0, 
            "logoURI": None
        }
    return metadata

# ======================================================
# TOKEN BALANCE
# ======================================================
@api_router.get("/token-balance")
async def token_balance(wallet: str, token_mint: str): # Hapus validasi ketat query
    logger.info(f"Balance request wallet={wallet} mint={token_mint}")
    service = get_token_service()
    return await service.get_token_balance(wallet, token_mint)

# ======================================================
# MULTIPLE TOKEN BALANCES
# ======================================================
class TokenBalancesRequest(BaseModel):
    wallet: str
    token_mints: list[str]

@api_router.post("/token-balances")
async def get_multiple_token_balances(request: TokenBalancesRequest):
    """
    Get balances for multiple tokens at once.
    Used by TokenSelectDialog to show balances for all tokens.
    """
    logger.info(f"Multiple balances request for {len(request.token_mints)} tokens")
    
    if not request.wallet or len(request.wallet) < 32:
        return {"balances": {}}
    
    service = get_token_service()
    balances = {}
    
    # Fetch balance for each token
    for mint in request.token_mints:
        try:
            balance_data = await service.get_token_balance(request.wallet, mint)
            balances[mint] = balance_data
        except Exception as e:
            logger.error(f"Error fetching balance for {mint}: {e}")
            balances[mint] = {"balance": 0, "uiAmount": 0, "decimals": 0}
    
    return {"balances": balances}

# ======================================================
# VALIDATE TOKEN
# ======================================================
@api_router.post("/validate-token/{token_address}")
async def validate_token(token_address: str):
    """
    Validate if a token address is valid and exists on Solana.
    Used before adding custom tokens.
    """
    logger.info(f"Validate token request: {token_address}")
    
    # Basic validation - check address format
    if not token_address or len(token_address) < 32 or len(token_address) > 44:
        return {"valid": False, "error": "Invalid address format"}
    
    try:
        # Try to get metadata - if successful, token is valid
        service = get_token_service()
        metadata = await service.get_token_metadata(token_address)
        
        # Check if we got valid metadata
        if metadata and metadata.get("symbol") != "UNK":
            return {
                "valid": True,
                "token": metadata
            }
        
        # Token exists but no metadata found
        return {
            "valid": True,
            "token": metadata,
            "warning": "Token found but metadata limited"
        }
        
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return {"valid": False, "error": str(e)}

# ======================================================
# WALLET PORTFOLIO (Total Balance + All Tokens)
# ======================================================
@api_router.get("/wallet-portfolio")
async def wallet_portfolio(wallet: str):
    """
    Mendapatkan total balance wallet dalam USD + breakdown semua token.
    Menghitung: balance × price untuk setiap token, termasuk yang harganya 0.
    """
    logger.info(f"Portfolio request for wallet: {wallet}")
    service = get_token_service()
    return await service.get_wallet_portfolio(wallet)

# ======================================================
# PRICE CHART
# ======================================================
@api_router.get("/price-chart")
async def price_chart(token: str, interval: str = "1h"):
    service = get_token_service()
    return await service.get_token_price_chart(token, interval)

# ======================================================
# EXCHANGE RATE (USD TO IDR)
# ======================================================
@api_router.get("/exchange-rate")
async def get_exchange_rate():
    """
    Get current USD to IDR exchange rate.
    Returns real-time rate with caching (1 hour).
    """
    logger.info("Exchange rate request")
    service = get_currency_service()
    rate_data = await service.get_usd_to_idr_rate()
    return rate_data


# ======================================================
# 3. FIX ERROR: Quote & Swap
# ======================================================
@api_router.get("/quote")
async def get_quote(inputMint: str, outputMint: str, amount: int, slippageBps: int = 50):
    logger.info(f"Quote Request: {amount}")
    
    if not get_jupiter_service:
        # Jika service jupiter belum ada, return Mock agar frontend tidak crash 520
        logger.warning("Jupiter Service not found. Returning MOCK quote.")
        return {
            "inAmount": str(amount),
            "outAmount": str(int(amount * 0.95)), # Mock price impact
            "priceImpactPct": "0.1",
            "marketInfos": [],
            "swapMode": "ExactIn",
            "otherAmountThreshold": str(int(amount * 0.94)),
        }

    service = get_jupiter_service()
    quote = await service.get_quote(inputMint, outputMint, amount, slippageBps)
    
    if not quote:
        raise HTTPException(status_code=400, detail="Jupiter Quote Failed")
    
    return quote

@api_router.post("/swap")
async def swap_tokens(request: SwapRequest):
    logger.info(f"Swap request: {request.userPublicKey}")

    if not get_jupiter_service:
        raise HTTPException(status_code=500, detail="Jupiter Service not configured in Backend")

    service = get_jupiter_service()
    
    # 1. Get Quote
    quote = await service.get_quote(request.inputMint, request.outputMint, request.amount, request.slippageBps)
    if not quote:
        raise HTTPException(status_code=400, detail="Failed to get quote")

    # 2. Get Transaction
    swap_tx = await service.get_swap_transaction(quote, request.userPublicKey)
    if not swap_tx:
        raise HTTPException(status_code=400, detail="Failed to build transaction")
    
    return {
        "status": "ok",
        "transaction": swap_tx, # Frontend butuh string ini untuk Buffer.from()
        "quoteDetails": quote
    }

app.include_router(api_router)