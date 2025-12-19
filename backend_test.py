#!/usr/bin/env python3
"""
Backend API Testing Suite
Tests Jupiter API integration after hostname fix
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://address-search-fix-1.preview.emergentagent.com/api"

# Test token addresses
SOL_TOKEN = "So11111111111111111111111111111111111111112"  # SOL
USDC_TOKEN = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC
USER_TOKEN_1 = "4ymWDE5kwxZ5rxN3mWLvJEBHESbZSiqBuvWmSVcGqZdj"  # User's TEKRA token 1
USER_TOKEN_2 = "FShCGqGUWRZkqovteJBGegUJAcjRzHZiBmHYGgSqpump"  # User's TEKRA token 2

# Test wallet address (example)
TEST_WALLET = "EcC2sMMECMwJRG8ZDjpyRpjR4YMFGY5GmCU7qNBqDLFp"

class TestResults:
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
    
    def add_result(self, test_name, passed, details="", error=""):
        self.tests.append({
            "test": test_name,
            "passed": passed,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        print(f"\n{'='*60}")
        print(f"JUPITER API TEST RESULTS")
        print(f"{'='*60}")
        print(f"Total Tests: {len(self.tests)}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/len(self.tests)*100):.1f}%" if self.tests else "0%")
        print(f"{'='*60}")
        
        for test in self.tests:
            status = "✅ PASS" if test["passed"] else "❌ FAIL"
            print(f"{status} {test['test']}")
            if test["details"]:
                print(f"    Details: {test['details']}")
            if test["error"]:
                print(f"    Error: {test['error']}")
            print()

async def test_jupiter_quote_endpoint():
    """Test GET /api/quote endpoint with Jupiter API"""
    results = TestResults()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: SOL to USDC quote
        try:
            print("Testing SOL to USDC quote...")
            response = await client.get(
                f"{BACKEND_URL}/quote",
                params={
                    "inputMint": SOL_TOKEN,
                    "outputMint": USDC_TOKEN,
                    "amount": 1000000000,  # 1 SOL (9 decimals)
                    "slippageBps": 100
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["inAmount", "outAmount", "priceImpactPct"]
                
                if all(field in data for field in required_fields):
                    results.add_result(
                        "SOL to USDC Quote",
                        True,
                        f"inAmount: {data['inAmount']}, outAmount: {data['outAmount']}, priceImpact: {data['priceImpactPct']}%"
                    )
                else:
                    missing = [f for f in required_fields if f not in data]
                    results.add_result(
                        "SOL to USDC Quote",
                        False,
                        error=f"Missing required fields: {missing}"
                    )
            else:
                results.add_result(
                    "SOL to USDC Quote",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            results.add_result(
                "SOL to USDC Quote",
                False,
                error=f"Request failed: {str(e)}"
            )
        
        # Test 2: User Token 1 to SOL quote
        try:
            print("Testing User Token 1 to SOL quote...")
            response = await client.get(
                f"{BACKEND_URL}/quote",
                params={
                    "inputMint": USER_TOKEN_1,
                    "outputMint": SOL_TOKEN,
                    "amount": 1000000000,  # 1 token (assuming 9 decimals)
                    "slippageBps": 100
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["inAmount", "outAmount", "priceImpactPct"]
                
                if all(field in data for field in required_fields):
                    results.add_result(
                        "User Token 1 to SOL Quote",
                        True,
                        f"inAmount: {data['inAmount']}, outAmount: {data['outAmount']}, priceImpact: {data['priceImpactPct']}%"
                    )
                else:
                    missing = [f for f in required_fields if f not in data]
                    results.add_result(
                        "User Token 1 to SOL Quote",
                        False,
                        error=f"Missing required fields: {missing}"
                    )
            else:
                results.add_result(
                    "User Token 1 to SOL Quote",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            results.add_result(
                "User Token 1 to SOL Quote",
                False,
                error=f"Request failed: {str(e)}"
            )
        
        # Test 3: User Token 2 to USDC quote
        try:
            print("Testing User Token 2 to USDC quote...")
            response = await client.get(
                f"{BACKEND_URL}/quote",
                params={
                    "inputMint": USER_TOKEN_2,
                    "outputMint": USDC_TOKEN,
                    "amount": 1000000000,  # 1 token (assuming 9 decimals)
                    "slippageBps": 100
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["inAmount", "outAmount", "priceImpactPct"]
                
                if all(field in data for field in required_fields):
                    results.add_result(
                        "User Token 2 to USDC Quote",
                        True,
                        f"inAmount: {data['inAmount']}, outAmount: {data['outAmount']}, priceImpact: {data['priceImpactPct']}%"
                    )
                else:
                    missing = [f for f in required_fields if f not in data]
                    results.add_result(
                        "User Token 2 to USDC Quote",
                        False,
                        error=f"Missing required fields: {missing}"
                    )
            else:
                results.add_result(
                    "User Token 2 to USDC Quote",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            results.add_result(
                "User Token 2 to USDC Quote",
                False,
                error=f"Request failed: {str(e)}"
            )
        
        # Test 4: Invalid token address error handling
        try:
            print("Testing invalid token address error handling...")
            response = await client.get(
                f"{BACKEND_URL}/quote",
                params={
                    "inputMint": "InvalidTokenAddress123",
                    "outputMint": USDC_TOKEN,
                    "amount": 1000000000,
                    "slippageBps": 100
                }
            )
            
            if response.status_code >= 400:
                results.add_result(
                    "Invalid Token Error Handling",
                    True,
                    f"Correctly returned error status {response.status_code}"
                )
            else:
                results.add_result(
                    "Invalid Token Error Handling",
                    False,
                    error=f"Should have returned error but got {response.status_code}"
                )
                
        except Exception as e:
            results.add_result(
                "Invalid Token Error Handling",
                False,
                error=f"Request failed: {str(e)}"
            )
    
    return results

async def test_jupiter_swap_endpoint():
    """Test POST /api/swap endpoint with Jupiter API"""
    results = TestResults()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: SOL to USDC swap preparation (without execution)
        try:
            print("Testing SOL to USDC swap preparation...")
            swap_data = {
                "inputMint": SOL_TOKEN,
                "outputMint": USDC_TOKEN,
                "amount": 100000000,  # 0.1 SOL
                "slippageBps": 100,
                "userPublicKey": TEST_WALLET,
                "dex": "jupiter"
            }
            
            response = await client.post(
                f"{BACKEND_URL}/swap",
                json=swap_data
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["transaction", "expectedOutput"]
                
                if all(field in data for field in required_fields):
                    results.add_result(
                        "SOL to USDC Swap Preparation",
                        True,
                        f"Transaction prepared, expectedOutput: {data['expectedOutput']}"
                    )
                else:
                    missing = [f for f in required_fields if f not in data]
                    results.add_result(
                        "SOL to USDC Swap Preparation",
                        False,
                        error=f"Missing required fields: {missing}"
                    )
            else:
                results.add_result(
                    "SOL to USDC Swap Preparation",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            results.add_result(
                "SOL to USDC Swap Preparation",
                False,
                error=f"Request failed: {str(e)}"
            )
        
        # Test 2: User Token to SOL swap preparation
        try:
            print("Testing User Token to SOL swap preparation...")
            swap_data = {
                "inputMint": USER_TOKEN_1,
                "outputMint": SOL_TOKEN,
                "amount": 1000000000,  # 1 token
                "slippageBps": 100,
                "userPublicKey": TEST_WALLET,
                "dex": "jupiter"
            }
            
            response = await client.post(
                f"{BACKEND_URL}/swap",
                json=swap_data
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["transaction", "expectedOutput"]
                
                if all(field in data for field in required_fields):
                    results.add_result(
                        "User Token to SOL Swap Preparation",
                        True,
                        f"Transaction prepared, expectedOutput: {data['expectedOutput']}"
                    )
                else:
                    missing = [f for f in required_fields if f not in data]
                    results.add_result(
                        "User Token to SOL Swap Preparation",
                        False,
                        error=f"Missing required fields: {missing}"
                    )
            else:
                results.add_result(
                    "User Token to SOL Swap Preparation",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            results.add_result(
                "User Token to SOL Swap Preparation",
                False,
                error=f"Request failed: {str(e)}"
            )
        
        # Test 3: Invalid DEX error handling
        try:
            print("Testing invalid DEX error handling...")
            swap_data = {
                "inputMint": SOL_TOKEN,
                "outputMint": USDC_TOKEN,
                "amount": 100000000,
                "slippageBps": 100,
                "userPublicKey": TEST_WALLET,
                "dex": "invalid_dex"
            }
            
            response = await client.post(
                f"{BACKEND_URL}/swap",
                json=swap_data
            )
            
            if response.status_code >= 400:
                results.add_result(
                    "Invalid DEX Error Handling",
                    True,
                    f"Correctly returned error status {response.status_code}"
                )
            else:
                results.add_result(
                    "Invalid DEX Error Handling",
                    False,
                    error=f"Should have returned error but got {response.status_code}"
                )
                
        except Exception as e:
            results.add_result(
                "Invalid DEX Error Handling",
                False,
                error=f"Request failed: {str(e)}"
            )
        
        # Test 4: Invalid token validation
        try:
            print("Testing invalid token validation in swap...")
            swap_data = {
                "inputMint": "InvalidTokenAddress123",
                "outputMint": USDC_TOKEN,
                "amount": 100000000,
                "slippageBps": 100,
                "userPublicKey": TEST_WALLET,
                "dex": "jupiter"
            }
            
            response = await client.post(
                f"{BACKEND_URL}/swap",
                json=swap_data
            )
            
            if response.status_code >= 400:
                results.add_result(
                    "Invalid Token Validation in Swap",
                    True,
                    f"Correctly returned error status {response.status_code}"
                )
            else:
                results.add_result(
                    "Invalid Token Validation in Swap",
                    False,
                    error=f"Should have returned error but got {response.status_code}"
                )
                
        except Exception as e:
            results.add_result(
                "Invalid Token Validation in Swap",
                False,
                error=f"Request failed: {str(e)}"
            )
    
    return results

async def test_backend_health():
    """Test basic backend health and connectivity"""
    results = TestResults()
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        
        # Test 1: Basic API health
        try:
            print("Testing backend API health...")
            response = await client.get(f"{BACKEND_URL}/")
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    results.add_result(
                        "Backend API Health",
                        True,
                        f"API responding: {data['message']}"
                    )
                else:
                    results.add_result(
                        "Backend API Health",
                        False,
                        error="Response missing message field"
                    )
            else:
                results.add_result(
                    "Backend API Health",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            results.add_result(
                "Backend API Health",
                False,
                error=f"Request failed: {str(e)}"
            )
        
        # Test 2: Token list endpoint
        try:
            print("Testing token list endpoint...")
            response = await client.get(f"{BACKEND_URL}/token-list")
            
            if response.status_code == 200:
                data = response.json()
                if "tokens" in data and isinstance(data["tokens"], list):
                    token_count = len(data["tokens"])
                    results.add_result(
                        "Token List Endpoint",
                        True,
                        f"Retrieved {token_count} tokens"
                    )
                else:
                    results.add_result(
                        "Token List Endpoint",
                        False,
                        error="Response missing tokens array"
                    )
            else:
                results.add_result(
                    "Token List Endpoint",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            results.add_result(
                "Token List Endpoint",
                False,
                error=f"Request failed: {str(e)}"
            )
    
    return results

async def main():
    """Run all Jupiter API tests"""
    print("Starting Jupiter API Integration Tests...")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Timestamp: {datetime.now().isoformat()}")
    print("="*60)
    
    # Run all test suites
    health_results = await test_backend_health()
    quote_results = await test_jupiter_quote_endpoint()
    swap_results = await test_jupiter_swap_endpoint()
    
    # Combine all results
    all_results = TestResults()
    all_results.tests.extend(health_results.tests)
    all_results.tests.extend(quote_results.tests)
    all_results.tests.extend(swap_results.tests)
    all_results.passed = health_results.passed + quote_results.passed + swap_results.passed
    all_results.failed = health_results.failed + quote_results.failed + swap_results.failed
    
    # Print comprehensive summary
    all_results.print_summary()
    
    # Return exit code based on results
    return 0 if all_results.failed == 0 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)