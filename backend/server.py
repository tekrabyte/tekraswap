from fastapi import FastAPI, APIRouter, HTTPException
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import httpx
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Import Service
from services.token_service import get_token_service
from dotenv import load_dotenv

load_dotenv()

# --- SETUP LOGGING AGAR MUNCUL DI TERMINAL ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SOLANA_DEBUG")

app = FastAPI(title="Solana Swap Backend")

# --- CORS: IZINKAN SEMUA (PENTING BUAT LOCALHOST) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Izinkan semua origin (Frontend React/NextJS)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB Setup
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
try:
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[os.environ.get('DB_NAME', 'solana_bot')]
except:
    db = None

class SwapRequest(BaseModel):
    userPublicKey: str
    inputMint: str
    outputMint: str
    amount: int
    slippageBps: int = 100

api_router = APIRouter(prefix="/api")

# --- DEBUG ENDPOINTS ---

@api_router.get("/token-metadata/{token_address}")
async def get_metadata(token_address: str):
    print(f"\n[DEBUG] Request Metadata untuk: {token_address}") # <--- CEK TERMINAL
    try:
        service = get_token_service()
        # Validasi panjang address Solana (biasanya 32-44 karakter)
        if len(token_address) < 30:
            print(f"[ERROR] Alamat token kependekan/salah: {token_address}")
            return {"address": token_address, "symbol": "ERR", "price_per_token": 0}

        metadata = await service.get_token_metadata(token_address)
        print(f"[SUCCESS] Metadata didapat: {metadata.get('symbol')} - Harga: {metadata.get('price_per_token')}")
        return metadata
    except Exception as e:
        print(f"[ERROR] Metadata crash: {str(e)}")
        return {"address": token_address, "symbol": "ERR", "price_per_token": 0}

@api_router.get("/token-balance")
async def get_balance(wallet: str, token_mint: str):
    print(f"\n[DEBUG] Request Balance.") 
    print(f"   -> Wallet: {wallet}")
    print(f"   -> Token:  {token_mint}")
    
    try:
        service = get_token_service()
        balance = await service.get_token_balance(wallet, token_mint)
        print(f"[SUCCESS] Balance User: {balance['uiAmount']}")
        return balance
    except Exception as e:
        print(f"[ERROR] Balance crash: {str(e)}")
        return {"balance": 0, "uiAmount": 0}

@api_router.get("/price-chart")
async def get_chart(token: str, interval: str = "1h"):
    print(f"\n[DEBUG] Request Chart untuk: {token}")
    try:
        service = get_token_service()
        data = await service.get_token_price_chart(token, interval)
        print(f"[SUCCESS] Chart data points: {len(data.get('data', []))}")
        return data
    except Exception as e:
        print(f"[ERROR] Chart crash: {e}")
        return {"data": [], "current_price": 0}

@api_router.post("/swap")
async def swap_tokens(request: SwapRequest):
    print(f"\n[DEBUG] SWAP REQUEST MASUK: {request}")
    # ... logic swap tetap sama ...
    return {"status": "mock_ok"}

app.include_router(api_router)