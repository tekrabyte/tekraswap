from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class SwapMode(str, Enum):
    ExactIn = "ExactIn"
    ExactOut = "ExactOut"

class QuoteRequest(BaseModel):
    inputMint: str
    outputMint: str
    amount: int
    slippageBps: int = 50
    onlyDirectRoutes: bool = False
    asLegacyTransaction: bool = False
    
    @validator('inputMint', 'outputMint')
    def validate_mint(cls, v):
        if not v or len(v) < 32:
            raise ValueError('Invalid mint address format')
        return v
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v

class QuoteResponse(BaseModel):
    inputMint: str
    inAmount: str
    outputMint: str
    outAmount: str
    otherAmountThreshold: str
    swapMode: str
    slippageBps: int
    platformFee: Optional[Dict[str, Any]] = None
    priceImpactPct: str
    routePlan: List[Dict[str, Any]]
    contextSlot: Optional[int] = None
    timeTaken: Optional[float] = None

class SwapRequest(BaseModel):
    userPublicKey: str
    quoteResponse: Dict[str, Any]
    wrapAndUnwrapSol: bool = True
    computeUnitPriceMicroLamports: Optional[int] = None
    asLegacyTransaction: bool = False
    useSharedAccounts: bool = True
    feeAccount: Optional[str] = None
    
    @validator('userPublicKey')
    def validate_pubkey(cls, v):
        if not v or len(v) < 32:
            raise ValueError('Invalid public key format')
        return v

class TokenMetadata(BaseModel):
    mint: str
    symbol: str
    name: str
    decimals: int
    logoURI: Optional[str] = None
    tags: List[str] = []
    extensions: Optional[Dict[str, Any]] = None

class SwapTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    userPublicKey: str
    inputMint: str
    outputMint: str
    inputAmount: int
    outputAmount: int
    platformFee: int
    feeAccount: Optional[str] = None
    status: str = "pending"
    transactionSignature: Optional[str] = None
    errorMessage: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

class TokenSearchResponse(BaseModel):
    tokens: List[TokenMetadata]
    total: int
