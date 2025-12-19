from fastapi import APIRouter, HTTPException, Depends
from services.token_service import token_service
from database import get_database
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_db():
    return await get_database()

@router.get("/metadata/{mint_address}")
async def get_token_metadata(
    mint_address: str,
    use_cache: bool = True,
    db = Depends(get_db)
):
    """
    Get token metadata by mint address.
    Fetches from cache first, then from Jupiter token list or blockchain.
    """
    try:
        metadata = await token_service.get_token_metadata(
            mint_address=mint_address,
            use_cache=use_cache
        )
        
        if not metadata:
            raise HTTPException(
                status_code=404,
                detail=f"Token metadata not found for {mint_address}"
            )
        
        return metadata
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching token metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_tokens(
    query: str,
    limit: int = 20,
    db = Depends(get_db)
):
    """
    Search tokens by symbol or name.
    Returns matching tokens from the cached database.
    """
    try:
        if not query or len(query) < 1:
            raise HTTPException(
                status_code=400,
                detail="Query parameter must be at least 1 character"
            )
        
        results = await token_service.search_tokens(
            query=query,
            limit=limit
        )
        
        return {
            "tokens": results,
            "total": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching tokens: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/popular")
async def get_popular_tokens(db = Depends(get_db)):
    """
    Get list of popular tokens for quick selection.
    """
    try:
        # Common Solana tokens
        popular_mints = [
            "So11111111111111111111111111111111111111112",  # SOL
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
            "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",  # USDT
            "4ymWDE5kwxZ5rxN3mWLvJEBHESbZSiqBuvWmSVcGqZdj",  # User's token 1
            "FShCGqGUWRZkqovteJBGegUJAcjRzHZiBmHYGgSqpump",  # User's token 2
        ]
        
        tokens = []
        for mint in popular_mints:
            metadata = await token_service.get_token_metadata(mint, use_cache=True)
            if metadata:
                tokens.append(metadata)
        
        return {
            "tokens": tokens,
            "total": len(tokens)
        }
        
    except Exception as e:
        logger.error(f"Error fetching popular tokens: {e}")
        raise HTTPException(status_code=500, detail=str(e))
