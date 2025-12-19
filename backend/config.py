import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "jupiter_swap")
    SOLANA_RPC_URL: str = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    JUPITER_API_URL: str = os.getenv("JUPITER_API_URL", "https://quote-api.jup.ag/v6")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    PLATFORM_FEE_BPS: int = int(os.getenv("PLATFORM_FEE_BPS", "50"))  # 0.5%
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ]
    
    # Fee wallet mappings for specific tokens
    FEE_WALLETS = {
        "4ymWDE5kwxZ5rxN3mWLvJEBHESbZSiqBuvWmSVcGqZdj": "EcC2sMMECMwJRG8ZDjpyRpjR4YMFGY5GmCU7qNBqDLFp",
        "FShCGqGUWRZkqovteJBGegUJAcjRzHZiBmHYGgSqpump": "AfwGDmpKgNSKu1KHqnsCT8v5D8vRfg8Ne3CwD44BgfY8"
    }

settings = Settings()
