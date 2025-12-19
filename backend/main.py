from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from database import connect_db, close_db, create_indexes
from routes import swap, tokens
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Jupiter Swap Platform API...")
    await connect_db()
    await create_indexes()
    logger.info("Application started successfully")
    yield
    # Shutdown
    logger.info("Shutting down...")
    await close_db()
    logger.info("Application shut down successfully")

# Create FastAPI app
app = FastAPI(
    title="Jupiter Swap Platform API",
    description="API for Solana token swaps using Jupiter Aggregator",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(swap.router, prefix="/api/swap", tags=["Swap"])
app.include_router(tokens.router, prefix="/api/tokens", tags=["Tokens"])

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    return {
        "message": "Jupiter Swap Platform API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
