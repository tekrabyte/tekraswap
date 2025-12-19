from typing import Optional
from config import settings
from database import get_database
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FeeService:
    """Service for managing platform fees"""
    
    @staticmethod
    def get_fee_account(output_mint: str) -> Optional[str]:
        """Get fee wallet address for specific output token"""
        return settings.FEE_WALLETS.get(output_mint)
    
    @staticmethod
    def calculate_fee(amount: int, fee_bps: int = None) -> int:
        """Calculate fee amount in basis points"""
        if fee_bps is None:
            fee_bps = settings.PLATFORM_FEE_BPS
        return int(amount * fee_bps / 10000)
    
    @staticmethod
    async def record_fee(
        transaction_id: str,
        fee_amount: int,
        token_mint: str,
        fee_account: str
    ):
        """Record fee collection in database"""
        try:
            db = await get_database()
            await db.fee_ledger.insert_one({
                "transactionId": transaction_id,
                "feeAmount": fee_amount,
                "tokenMint": token_mint,
                "feeAccount": fee_account,
                "timestamp": datetime.utcnow()
            })
            logger.info(f"Fee recorded: {fee_amount} for tx {transaction_id}")
        except Exception as e:
            logger.error(f"Error recording fee: {e}")
    
    @staticmethod
    async def get_fee_statistics(fee_account: Optional[str] = None):
        """Get fee collection statistics"""
        try:
            db = await get_database()
            match_filter = {}
            if fee_account:
                match_filter["feeAccount"] = fee_account
            
            pipeline = [
                {"$match": match_filter},
                {
                    "$group": {
                        "_id": "$tokenMint",
                        "totalFees": {"$sum": "$feeAmount"},
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            results = await db.fee_ledger.aggregate(pipeline).to_list(length=None)
            return results
        except Exception as e:
            logger.error(f"Error getting fee statistics: {e}")
            return []

fee_service = FeeService()
