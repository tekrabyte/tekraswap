"""Currency Service for exchange rate operations.

Provides real-time USD to IDR exchange rates with caching.
Uses free exchangerate-api.com API with fallback to hardcoded rate.
"""

import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class CurrencyService:
    """Service for currency exchange rate operations.
    
    Features:
    - Real-time USD to IDR exchange rate
    - 1-hour caching to reduce API calls
    - Fallback to hardcoded rate if API fails
    - Multiple API providers support
    """
    
    def __init__(self):
        self.cache: Dict[str, any] = {}
        self.cache_duration = timedelta(hours=1)
        # Fallback rate jika API gagal (update manual setiap bulan)
        self.fallback_rate = 15800.0  # 1 USD = 15,800 IDR (approximate)
        
    async def get_usd_to_idr_rate(self) -> Dict:
        """Get USD to IDR exchange rate.
        
        Returns:
            Dict with:
            - rate: float (IDR per 1 USD)
            - last_update: timestamp
            - source: API source name or 'fallback'
        """
        # Check cache first
        if self._is_cache_valid():
            logger.info(f"Using cached exchange rate: {self.cache['rate']} IDR")
            return self.cache
        
        # Try to fetch from API
        rate_data = await self._fetch_from_api()
        
        if rate_data:
            self.cache = rate_data
            return rate_data
        
        # Fallback
        logger.warning("Using fallback exchange rate")
        fallback_data = {
            "rate": self.fallback_rate,
            "last_update": datetime.now().isoformat(),
            "source": "fallback",
            "currency_pair": "USD/IDR"
        }
        self.cache = fallback_data
        return fallback_data
    
    def _is_cache_valid(self) -> bool:
        """Check if cached rate is still valid."""
        if not self.cache or 'last_update' not in self.cache:
            return False
        
        try:
            last_update = datetime.fromisoformat(self.cache['last_update'])
            return datetime.now() - last_update < self.cache_duration
        except Exception:
            return False
    
    async def _fetch_from_api(self) -> Optional[Dict]:
        """Fetch exchange rate from API.
        
        Tries multiple providers in order:
        1. exchangerate-api.com (free, no key)
        2. frankfurter.app (free, no key)
        """
        # Provider 1: exchangerate-api.com
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                url = "https://api.exchangerate-api.com/v4/latest/USD"
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    idr_rate = data.get("rates", {}).get("IDR")
                    
                    if idr_rate:
                        logger.info(f"Fetched exchange rate from exchangerate-api: {idr_rate} IDR")
                        return {
                            "rate": float(idr_rate),
                            "last_update": datetime.now().isoformat(),
                            "source": "exchangerate-api.com",
                            "currency_pair": "USD/IDR"
                        }
        except Exception as e:
            logger.warning(f"exchangerate-api.com failed: {e}")
        
        # Provider 2: frankfurter.app
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                url = "https://api.frankfurter.app/latest?from=USD&to=IDR"
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    idr_rate = data.get("rates", {}).get("IDR")
                    
                    if idr_rate:
                        logger.info(f"Fetched exchange rate from frankfurter: {idr_rate} IDR")
                        return {
                            "rate": float(idr_rate),
                            "last_update": datetime.now().isoformat(),
                            "source": "frankfurter.app",
                            "currency_pair": "USD/IDR"
                        }
        except Exception as e:
            logger.warning(f"frankfurter.app failed: {e}")
        
        return None
    
    def convert_usd_to_idr(self, usd_amount: float, rate: float) -> float:
        """Convert USD amount to IDR.
        
        Args:
            usd_amount: Amount in USD
            rate: Exchange rate (IDR per USD)
            
        Returns:
            Amount in IDR
        """
        if usd_amount is None or rate is None:
            return 0.0
        return float(usd_amount) * float(rate)

# Singleton instance
_currency_service = None

def get_currency_service() -> CurrencyService:
    """Get singleton instance of CurrencyService."""
    global _currency_service
    if _currency_service is None:
        _currency_service = CurrencyService()
    return _currency_service
