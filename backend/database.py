from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config import settings
import logging

logger = logging.getLogger(__name__)

client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None

async def connect_db():
    global client, db
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.DATABASE_NAME]
        # Test connection
        await client.admin.command('ping')
        logger.info("Connected to MongoDB successfully")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_db():
    global client
    if client:
        client.close()
        logger.info("Disconnected from MongoDB")

async def get_database() -> AsyncIOMotorDatabase:
    return db

async def create_indexes():
    """Create database indexes for optimized queries"""
    if db:
        try:
            await db.swaps.create_index("userPublicKey")
            await db.swaps.create_index("transactionSignature")
            await db.swaps.create_index("createdAt")
            await db.tokens.create_index("mint", unique=True)
            await db.tokens.create_index("symbol")
            await db.fee_ledger.create_index("transactionId")
            await db.fee_ledger.create_index("timestamp")
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
