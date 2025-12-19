from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from models import QuoteRequest, SwapRequest, SwapTransaction
from services.jupiter_service import jupiter_service
from services.fee_service import fee_service
from database import get_database
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_db():
    return await get_database()

@router.post("/quote")
async def get_quote(request: QuoteRequest):
    """
    Get a swap quote from Jupiter Aggregator.
    Returns the best route with estimated output amount.
    """
    try:
        quote = await jupiter_service.get_quote(
            input_mint=request.inputMint,
            output_mint=request.outputMint,
            amount=request.amount,
            slippage_bps=request.slippageBps,
            only_direct_routes=request.onlyDirectRoutes,
            as_legacy_transaction=request.asLegacyTransaction
        )
        
        if not quote:
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch quote from Jupiter. Please check the token addresses and try again."
            )
        
        # Calculate platform fee
        output_amount = int(quote.get("outAmount", 0))
        fee_amount = fee_service.calculate_fee(output_amount)
        
        # Add fee information to response
        quote["platformFee"] = {
            "amount": fee_amount,
            "bps": 50,
            "percentage": 0.5
        }
        
        # Check if we have a fee account for this output token
        fee_account = fee_service.get_fee_account(request.outputMint)
        if fee_account:
            quote["feeAccount"] = fee_account
        
        return quote
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_quote: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute")
async def execute_swap(
    request: SwapRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """
    Execute a swap transaction.
    Returns the serialized transaction for the user to sign.
    """
    try:
        # Determine fee account based on output token
        output_mint = request.quoteResponse.get("outputMint")
        fee_account = request.feeAccount or fee_service.get_fee_account(output_mint)
        
        # Get swap transaction from Jupiter
        swap_result = await jupiter_service.get_swap_transaction(
            user_public_key=request.userPublicKey,
            quote_response=request.quoteResponse,
            wrap_and_unwrap_sol=request.wrapAndUnwrapSol,
            use_shared_accounts=request.useSharedAccounts,
            fee_account=fee_account,
            compute_unit_price_micro_lamports=request.computeUnitPriceMicroLamports,
            as_legacy_transaction=request.asLegacyTransaction
        )
        
        if not swap_result:
            raise HTTPException(
                status_code=500,
                detail="Failed to create swap transaction. Please try again."
            )
        
        # Calculate fee amounts
        input_amount = int(request.quoteResponse.get("inAmount", 0))
        output_amount = int(request.quoteResponse.get("outAmount", 0))
        fee_amount = fee_service.calculate_fee(output_amount)
        
        # Record transaction in database
        swap_record = SwapTransaction(
            userPublicKey=request.userPublicKey,
            inputMint=request.quoteResponse.get("inputMint"),
            outputMint=output_mint,
            inputAmount=input_amount,
            outputAmount=output_amount,
            platformFee=fee_amount,
            feeAccount=fee_account,
            status="pending"
        )
        
        result = await db.swaps.insert_one(swap_record.dict())
        transaction_id = str(result.inserted_id)
        
        # Record fee in background
        if fee_account:
            background_tasks.add_task(
                fee_service.record_fee,
                transaction_id,
                fee_amount,
                output_mint,
                fee_account
            )
        
        return {
            "swapTransaction": swap_result.get("swapTransaction"),
            "lastValidBlockHeight": swap_result.get("lastValidBlockHeight"),
            "prioritizationFeeLamports": swap_result.get("prioritizationFeeLamports"),
            "transactionId": transaction_id,
            "platformFee": {
                "amount": fee_amount,
                "bps": 50,
                "percentage": 0.5,
                "account": fee_account
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in execute_swap: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/confirm/{transaction_id}")
async def confirm_transaction(
    transaction_id: str,
    signature: str,
    db = Depends(get_db)
):
    """
    Update transaction status after user signs and submits.
    """
    try:
        result = await db.swaps.update_one(
            {"id": transaction_id},
            {
                "$set": {
                    "transactionSignature": signature,
                    "status": "confirmed"
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return {"success": True, "signature": signature}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{user_public_key}")
async def get_swap_history(
    user_public_key: str,
    limit: int = 20,
    db = Depends(get_db)
):
    """
    Get swap history for a user.
    """
    try:
        swaps = await db.swaps.find(
            {"userPublicKey": user_public_key}
        ).sort("createdAt", -1).limit(limit).to_list(length=limit)
        
        for swap in swaps:
            swap.pop('_id', None)
        
        return {"swaps": swaps, "total": len(swaps)}
        
    except Exception as e:
        logger.error(f"Error fetching swap history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
