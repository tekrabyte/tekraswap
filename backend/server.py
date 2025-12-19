from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import httpx
import base58

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class SwapRequest(BaseModel):
    inputMint: str
    outputMint: str
    amount: int
    slippageBps: int = 100
    userPublicKey: str
    dex: str

class TokenInfo(BaseModel):
    address: str
    decimals: int = 9
    supply: Optional[float] = None
    price_usd: Optional[float] = None

class SwapRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    userPublicKey: str
    inputMint: str
    outputMint: str
    inputAmount: int
    expectedOutput: Optional[int] = None
    dex: str
    txHash: Optional[str] = None
    status: str = "pending"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Routes
@api_router.get("/")
async def root():
    return {"message": "Solana Token Swap API"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks

@api_router.post("/swap")
async def swap_tokens(request: SwapRequest):
    """Execute token swap via Jupiter or Raydium"""
    try:
        if request.dex == "jupiter":
            return await swap_jupiter(request)
        elif request.dex == "raydium":
            return await swap_raydium(request)
        else:
            raise HTTPException(status_code=400, detail="Invalid DEX selection")
    except Exception as e:
        logging.error(f"Swap error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def swap_jupiter(request: SwapRequest):
    """Jupiter Aggregator swap implementation"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get quote from Jupiter API v6
            quote_url = "https://quote-api.jup.ag/v6/quote"
            params = {
                "inputMint": request.inputMint,
                "outputMint": request.outputMint,
                "amount": request.amount,
                "slippageBps": request.slippageBps,
            }
            
            quote_response = await client.get(quote_url, params=params)
            quote_response.raise_for_status()
            quote_data = quote_response.json()

            if "error" in quote_data:
                raise Exception(f"Jupiter quote error: {quote_data['error']}")

            # Build swap transaction
            swap_url = "https://quote-api.jup.ag/v6/swap"
            swap_payload = {
                "quoteResponse": quote_data,
                "userPublicKey": request.userPublicKey,
                "wrapAndUnwrapSol": True,
            }

            swap_response = await client.post(swap_url, json=swap_payload)
            swap_response.raise_for_status()
            swap_data = swap_response.json()

            # Store swap record
            swap_record = SwapRecord(
                userPublicKey=request.userPublicKey,
                inputMint=request.inputMint,
                outputMint=request.outputMint,
                inputAmount=request.amount,
                expectedOutput=int(quote_data.get("outAmount", 0)),
                dex="jupiter",
                status="pending"
            )
            
            doc = swap_record.model_dump()
            doc['timestamp'] = doc['timestamp'].isoformat()
            await db.swaps.insert_one(doc)

            return {
                "transaction": swap_data.get("swapTransaction"),
                "expectedOutput": quote_data.get("outAmount"),
                "priceImpact": quote_data.get("priceImpactPct")
            }

    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Jupiter API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Jupiter swap error: {str(e)}")

async def swap_raydium(request: SwapRequest):
    """Raydium DEX swap implementation"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get quote from Raydium API v1
            raydium_api = "https://api-v3.raydium.io"
            quote_url = f"{raydium_api}/swap/quote"
            
            params = {
                "inputMint": request.inputMint,
                "outputMint": request.outputMint,
                "amount": str(request.amount),
                "slippage": request.slippageBps / 10000,
            }

            quote_response = await client.get(quote_url, params=params)
            quote_response.raise_for_status()
            quote_data = quote_response.json()

            if not quote_data.get("data"):
                raise Exception("Failed to get quote from Raydium")

            # Build transaction
            tx_url = f"{raydium_api}/swap/transaction"
            tx_payload = {
                "quote": quote_data["data"],
                "wallet": request.userPublicKey,
                "wrapSol": True,
                "txVersion": "V0",
            }

            tx_response = await client.post(tx_url, json=tx_payload)
            tx_response.raise_for_status()
            tx_data = tx_response.json()

            # Store swap record
            swap_record = SwapRecord(
                userPublicKey=request.userPublicKey,
                inputMint=request.inputMint,
                outputMint=request.outputMint,
                inputAmount=request.amount,
                expectedOutput=int(quote_data["data"].get("outAmount", 0)),
                dex="raydium",
                status="pending"
            )
            
            doc = swap_record.model_dump()
            doc['timestamp'] = doc['timestamp'].isoformat()
            await db.swaps.insert_one(doc)

            return {
                "transaction": tx_data.get("transaction"),
                "expectedOutput": quote_data["data"].get("outAmount"),
            }

    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Raydium API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Raydium swap error: {str(e)}")

@api_router.get("/quote")
async def get_quote(inputMint: str, outputMint: str, amount: int, slippageBps: int = 100):
    """Get swap quote from Jupiter"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            quote_url = "https://quote-api.jup.ag/v6/quote"
            params = {
                "inputMint": inputMint,
                "outputMint": outputMint,
                "amount": amount,
                "slippageBps": slippageBps,
            }
            
            response = await client.get(quote_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return {
                "inAmount": data.get("inAmount"),
                "outAmount": data.get("outAmount"),
                "priceImpactPct": data.get("priceImpactPct"),
                "routePlan": data.get("routePlan", []),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/token-info")
async def get_token_info(address: str):
    """Get token information"""
    try:
        # For demo, return basic info
        # In production, integrate with DexScreener or Jupiter API
        return {
            "address": address,
            "name": "Token",
            "symbol": "TOKEN",
            "decimals": 9,
            "price_usd": 0.0,
            "volume_24h": 0.0,
            "market_cap": 0.0,
            "price_change_24h": 0.0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/swap-history")
async def get_swap_history(wallet: str, limit: int = 10):
    """Retrieve swap history for a wallet"""
    try:
        swaps = await db.swaps.find(
            {"userPublicKey": wallet}
        ).sort("timestamp", -1).limit(limit).to_list(limit)

        for swap in swaps:
            swap["_id"] = str(swap["_id"])
            if isinstance(swap.get("timestamp"), str):
                pass
            elif hasattr(swap.get("timestamp"), "isoformat"):
                swap["timestamp"] = swap["timestamp"].isoformat()

        return {"swaps": swaps}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/price-chart")
async def get_price_chart(token: str, interval: str = "1h"):
    """Get price chart data for token"""
    try:
        # Mock data for demo
        # In production, integrate with DexScreener or Birdeye API
        import random
        from datetime import timedelta
        
        now = datetime.now(timezone.utc)
        data = []
        base_price = 0.01
        
        for i in range(24):
            timestamp = now - timedelta(hours=24-i)
            price = base_price * (1 + random.uniform(-0.1, 0.1))
            data.append({
                "timestamp": int(timestamp.timestamp() * 1000),
                "price": price,
                "volume": random.uniform(1000, 10000)
            })
        
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()