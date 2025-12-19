# Jupiter Swap Widget - Solana Token Swap Platform

## Overview
Full-stack Solana token swap application menggunakan Jupiter Aggregator dengan sistem fee 0.5% per transaksi.

## Features
- ✅ Swap token Solana dengan best rates dari Jupiter
- ✅ Support wallet: Phantom & Solflare
- ✅ Baca metadata token via address paste
- ✅ Platform fee 0.5% masuk ke wallet Anda
- ✅ Mainnet ready
- ✅ Real-time quotes dengan debouncing
- ✅ Transaction history tracking

## Tech Stack
- **Frontend**: React + Vite + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python
- **Database**: MongoDB
- **Blockchain**: Solana Mainnet
- **Swap Provider**: Jupiter Aggregator v6

## Fee Wallet Configuration
Berikut adalah konfigurasi fee wallet untuk token Anda:

### Token 1
- **Token Address**: `4ymWDE5kwxZ5rxN3mWLvJEBHESbZSiqBuvWmSVcGqZdj`
- **Fee Wallet**: `EcC2sMMECMwJRG8ZDjpyRpjR4YMFGY5GmCU7qNBqDLFp`

### Token 2
- **Token Address**: `FShCGqGUWRZkqovteJBGegUJAcjRzHZiBmHYGgSqpump`
- **Fee Wallet**: `AfwGDmpKgNSKu1KHqnsCT8v5D8vRfg8Ne3CwD44BgfY8`

Setiap kali ada swap ke token-token ini, fee 0.5% akan otomatis masuk ke wallet yang dikonfigurasi.

## Setup Instructions

### 1. Install Dependencies

#### Backend
```bash
cd backend
pip install -r requirements.txt
```

#### Frontend
```bash
cd frontend
yarn install
```

### 2. Start MongoDB
```bash
sudo systemctl start mongodb
# atau jika menggunakan Docker:
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 3. Configure Environment

#### Backend (.env)
```
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=jupiter_swap
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
JUPITER_API_URL=https://quote-api.jup.ag/v6
ENVIRONMENT=production
PLATFORM_FEE_BPS=50
```

#### Frontend (.env)
```
VITE_BACKEND_URL=http://localhost:8001
VITE_SOLANA_NETWORK=mainnet-beta
VITE_SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
```

### 4. Start Services

#### Backend
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

#### Frontend
```bash
cd frontend
yarn dev
```

## Usage

1. **Connect Wallet**: Klik tombol "Connect Wallet" dan pilih Phantom atau Solflare

2. **Enter Token Addresses**:
   - Paste address token yang ingin di-swap di field "From"
   - Paste address token tujuan di field "To"
   - Atau pilih dari popular tokens

3. **Enter Amount**: Masukkan jumlah token yang ingin di-swap

4. **Review Quote**: 
   - Rate akan otomatis ditampilkan
   - Platform fee 0.5% sudah termasuk
   - Check price impact dan minimum received

5. **Execute Swap**: 
   - Klik tombol "Swap"
   - Approve transaction di wallet Anda
   - Tunggu konfirmasi

## API Endpoints

### Swap
- `POST /api/swap/quote` - Get swap quote
- `POST /api/swap/execute` - Execute swap transaction
- `POST /api/swap/confirm/{transaction_id}` - Confirm transaction
- `GET /api/swap/history/{user_public_key}` - Get swap history

### Tokens
- `GET /api/tokens/metadata/{mint_address}` - Get token metadata
- `GET /api/tokens/search?query=` - Search tokens
- `GET /api/tokens/popular` - Get popular tokens

## Architecture

### Frontend Flow
1. User connects wallet (Phantom/Solflare)
2. User inputs token addresses and amount
3. Frontend fetches token metadata from backend
4. Frontend requests quote from backend (with debouncing)
5. User reviews and confirms swap
6. Frontend sends swap execution request to backend
7. Backend returns serialized transaction
8. Frontend sends transaction to wallet for signing
9. Signed transaction submitted to Solana blockchain
10. Frontend confirms transaction with backend

### Backend Flow
1. Receives quote request from frontend
2. Calls Jupiter API v6 for best swap route
3. Calculates 0.5% platform fee
4. Returns quote with fee information
5. On swap execution:
   - Creates swap transaction via Jupiter
   - Records transaction in MongoDB
   - Returns serialized transaction
6. Tracks transaction status
7. Records fee collection for accounting

### Fee Collection
- Fee dikumpulkan otomatis oleh Jupiter saat swap
- Fee langsung masuk ke wallet yang dikonfigurasi
- Semua fee tercatat di database untuk tracking

## Database Schema

### Collections

#### swaps
```javascript
{
  id: String,
  userPublicKey: String,
  inputMint: String,
  outputMint: String,
  inputAmount: Number,
  outputAmount: Number,
  platformFee: Number,
  feeAccount: String,
  status: String, // pending, confirmed, failed
  transactionSignature: String,
  createdAt: Date,
  updatedAt: Date
}
```

#### tokens
```javascript
{
  mint: String,
  symbol: String,
  name: String,
  decimals: Number,
  logoURI: String,
  tags: Array
}
```

#### fee_ledger
```javascript
{
  transactionId: String,
  feeAmount: Number,
  tokenMint: String,
  feeAccount: String,
  timestamp: Date
}
```

## Security Considerations

1. **Private Keys**: Never stored on backend or database
2. **Transaction Signing**: Always done on user's wallet
3. **RPC Rate Limiting**: Use private RPC for production
4. **CORS**: Configured for specific origins only
5. **Input Validation**: All inputs validated with Pydantic

## Performance Optimization

1. **Token Metadata Caching**: Frequently accessed tokens cached in MongoDB
2. **Quote Debouncing**: 800ms debounce to reduce API calls
3. **Connection Pooling**: MongoDB connection pool for efficient queries
4. **Async Operations**: All I/O operations are async

## Monitoring & Analytics

### Fee Statistics
Query fee collection statistics:
```python
from services.fee_service import fee_service
stats = await fee_service.get_fee_statistics()
```

### Swap History
View all swaps for specific user:
```bash
curl http://localhost:8001/api/swap/history/{user_public_key}
```

## Production Deployment

### Recommended Setup
1. **RPC Provider**: Gunakan Helius atau QuickNode untuk RPC yang reliable
2. **Database**: MongoDB Atlas untuk managed database
3. **Backend**: Deploy ke VPS atau cloud (AWS, DigitalOcean, etc)
4. **Frontend**: Deploy ke Vercel atau Netlify
5. **Monitoring**: Setup logging dan error tracking (Sentry)

### Environment Variables (Production)
```bash
# Backend
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/jupiter_swap
SOLANA_RPC_URL=https://your-rpc-provider.com
ALLOWED_ORIGINS=["https://yourdomain.com"]

# Frontend
VITE_BACKEND_URL=https://api.yourdomain.com
VITE_SOLANA_RPC_URL=https://your-rpc-provider.com
```

## Troubleshooting

### Transaction Failed
- Check slippage tolerance (increase if needed)
- Verify sufficient SOL for gas fees
- Check RPC connection

### Token Not Found
- Verify token address is correct (44 characters)
- Token might not be in Jupiter's token list
- Check if token exists on Solana blockchain

### Quote Not Loading
- Check backend is running
- Verify CORS configuration
- Check network connectivity

## Support

Jika ada masalah atau pertanyaan:
1. Check logs: Backend logs di terminal
2. Check browser console untuk frontend errors
3. Verify MongoDB is running
4. Check API endpoints di http://localhost:8001/docs

## License
MIT
