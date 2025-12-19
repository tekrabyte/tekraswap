import React, { useState, useEffect, useCallback } from 'react'
import { useWallet, useConnection } from '@solana/wallet-adapter-react'
import { Transaction, VersionedTransaction } from '@solana/web3.js'
import bs58 from 'bs58'

interface Token {
  mint: string
  symbol: string
  name: string
  decimals: number
  logoURI?: string
}

interface QuoteResponse {
  inputMint: string
  inAmount: string
  outputMint: string
  outAmount: string
  otherAmountThreshold: string
  swapMode: string
  slippageBps: number
  platformFee?: {
    amount: number
    bps: number
    percentage: number
  }
  priceImpactPct: string
  routePlan: any[]
}

const SwapInterface: React.FC = () => {
  const { connected, publicKey, sendTransaction, signTransaction } = useWallet()
  const { connection } = useConnection()
  
  const [inputMint, setInputMint] = useState<string>('')
  const [outputMint, setOutputMint] = useState<string>('')
  const [inputToken, setInputToken] = useState<Token | null>(null)
  const [outputToken, setOutputToken] = useState<Token | null>(null)
  const [inputAmount, setInputAmount] = useState<string>('')
  const [quote, setQuote] = useState<QuoteResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [swapping, setSwapping] = useState(false)
  const [slippage, setSlippage] = useState(50) // 0.5%
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [popularTokens, setPopularTokens] = useState<Token[]>([])

  const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001'

  // Fetch popular tokens on mount
  useEffect(() => {
    fetchPopularTokens()
  }, [])

  const fetchPopularTokens = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/tokens/popular`)
      if (response.ok) {
        const data = await response.json()
        setPopularTokens(data.tokens || [])
      }
    } catch (err) {
      console.error('Failed to fetch popular tokens:', err)
    }
  }

  const fetchTokenMetadata = async (mint: string): Promise<Token | null> => {
    try {
      const response = await fetch(`${backendUrl}/api/tokens/metadata/${mint}`)
      if (response.ok) {
        const data = await response.json()
        return data
      }
      return null
    } catch (err) {
      console.error('Failed to fetch token metadata:', err)
      return null
    }
  }

  const handleInputMintChange = async (mint: string) => {
    setInputMint(mint)
    setError(null)
    if (mint.length >= 32) {
      const metadata = await fetchTokenMetadata(mint)
      if (metadata) {
        setInputToken(metadata)
      } else {
        setError('Token tidak ditemukan')
      }
    }
  }

  const handleOutputMintChange = async (mint: string) => {
    setOutputMint(mint)
    setError(null)
    if (mint.length >= 32) {
      const metadata = await fetchTokenMetadata(mint)
      if (metadata) {
        setOutputToken(metadata)
      } else {
        setError('Token tidak ditemukan')
      }
    }
  }

  const fetchQuote = useCallback(async () => {
    if (!inputToken || !outputToken || !inputAmount || parseFloat(inputAmount) <= 0) {
      setQuote(null)
      return
    }

    setLoading(true)
    setError(null)
    
    try {
      const amount = Math.floor(parseFloat(inputAmount) * Math.pow(10, inputToken.decimals))
      
      const response = await fetch(`${backendUrl}/api/swap/quote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          inputMint: inputToken.mint,
          outputMint: outputToken.mint,
          amount: amount,
          slippageBps: slippage,
          onlyDirectRoutes: false,
          asLegacyTransaction: false,
        }),
      })

      if (response.ok) {
        const quoteData = await response.json()
        setQuote(quoteData)
      } else {
        const errorData = await response.json()
        setError(errorData.detail || 'Failed to fetch quote')
      }
    } catch (err) {
      console.error('Failed to fetch quote:', err)
      setError('Gagal mendapatkan quote. Silakan coba lagi.')
    } finally {
      setLoading(false)
    }
  }, [inputToken, outputToken, inputAmount, slippage, backendUrl])

  // Debounce quote fetching
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      fetchQuote()
    }, 800)

    return () => clearTimeout(debounceTimer)
  }, [fetchQuote])

  const handleSwap = async () => {
    if (!connected || !publicKey || !quote) {
      setError('Silakan hubungkan wallet dan dapatkan quote terlebih dahulu')
      return
    }

    setSwapping(true)
    setError(null)
    setSuccess(null)

    try {
      // Get swap transaction from backend
      const response = await fetch(`${backendUrl}/api/swap/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userPublicKey: publicKey.toBase58(),
          quoteResponse: quote,
          wrapAndUnwrapSol: true,
          useSharedAccounts: true,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to create swap transaction')
      }

      const { swapTransaction, transactionId, platformFee } = await response.json()

      // Deserialize transaction
      const swapTransactionBuf = Buffer.from(swapTransaction, 'base64')
      const transaction = VersionedTransaction.deserialize(swapTransactionBuf)

      // Send transaction
      const signature = await sendTransaction(transaction, connection, {
        skipPreflight: false,
        maxRetries: 3,
      })

      console.log('Transaction sent:', signature)

      // Wait for confirmation
      const confirmation = await connection.confirmTransaction(signature, 'confirmed')

      if (confirmation.value.err) {
        throw new Error('Transaction failed')
      }

      // Update backend with signature
      await fetch(`${backendUrl}/api/swap/confirm/${transactionId}?signature=${signature}`, {
        method: 'POST',
      })

      setSuccess(`Swap berhasil! Signature: ${signature.substring(0, 8)}...`)
      
      // Reset form
      setInputAmount('')
      setQuote(null)

    } catch (err: any) {
      console.error('Swap failed:', err)
      setError(err.message || 'Swap gagal. Silakan coba lagi.')
    } finally {
      setSwapping(false)
    }
  }

  const selectToken = (token: Token, type: 'input' | 'output') => {
    if (type === 'input') {
      setInputMint(token.mint)
      setInputToken(token)
    } else {
      setOutputMint(token.mint)
      setOutputToken(token)
    }
  }

  const switchTokens = () => {
    const tempMint = inputMint
    const tempToken = inputToken
    setInputMint(outputMint)
    setInputToken(outputToken)
    setOutputMint(tempMint)
    setOutputToken(tempToken)
  }

  return (
    <div className="w-full max-w-lg">
      <div className="bg-white rounded-2xl shadow-xl p-6 space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <h3 className="text-xl font-bold text-gray-900">Swap</h3>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Slippage:</span>
            <select
              value={slippage}
              onChange={(e) => setSlippage(Number(e.target.value))}
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value={10}>0.1%</option>
              <option value={50}>0.5%</option>
              <option value={100}>1%</option>
              <option value={300}>3%</option>
            </select>
          </div>
        </div>

        {/* Input Token */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700">From</label>
          <div className="bg-gray-50 rounded-xl p-4 space-y-3">
            <input
              type="text"
              placeholder="Paste token address..."
              value={inputMint}
              onChange={(e) => handleInputMintChange(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            {inputToken && (
              <div className="flex items-center gap-2 text-sm">
                {inputToken.logoURI && (
                  <img src={inputToken.logoURI} alt={inputToken.symbol} className="w-6 h-6 rounded-full" />
                )}
                <span className="font-medium">{inputToken.symbol}</span>
                <span className="text-gray-500">- {inputToken.name}</span>
              </div>
            )}
            <input
              type="number"
              placeholder="0.00"
              value={inputAmount}
              onChange={(e) => setInputAmount(e.target.value)}
              className="w-full text-3xl font-semibold bg-transparent focus:outline-none"
            />
          </div>
        </div>

        {/* Switch Button */}
        <div className="flex justify-center">
          <button
            onClick={switchTokens}
            className="p-2 bg-gray-100 hover:bg-gray-200 rounded-full transition-colors"
          >
            <svg className="w-6 h-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
            </svg>
          </button>
        </div>

        {/* Output Token */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700">To</label>
          <div className="bg-gray-50 rounded-xl p-4 space-y-3">
            <input
              type="text"
              placeholder="Paste token address..."
              value={outputMint}
              onChange={(e) => handleOutputMintChange(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            {outputToken && (
              <div className="flex items-center gap-2 text-sm">
                {outputToken.logoURI && (
                  <img src={outputToken.logoURI} alt={outputToken.symbol} className="w-6 h-6 rounded-full" />
                )}
                <span className="font-medium">{outputToken.symbol}</span>
                <span className="text-gray-500">- {outputToken.name}</span>
              </div>
            )}
            {quote && outputToken && (
              <div className="text-3xl font-semibold">
                {(parseInt(quote.outAmount) / Math.pow(10, outputToken.decimals)).toFixed(6)}
              </div>
            )}
          </div>
        </div>

        {/* Quote Info */}
        {quote && (
          <div className="bg-purple-50 rounded-xl p-4 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Rate:</span>
              <span className="font-medium">
                1 {inputToken?.symbol} ≈ {(parseInt(quote.outAmount) / parseInt(quote.inAmount) * Math.pow(10, (inputToken?.decimals || 9) - (outputToken?.decimals || 9))).toFixed(6)} {outputToken?.symbol}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Price Impact:</span>
              <span className="font-medium">{parseFloat(quote.priceImpactPct).toFixed(2)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Platform Fee (0.5%):</span>
              <span className="font-medium text-purple-600">
                {quote.platformFee ? (quote.platformFee.amount / Math.pow(10, outputToken?.decimals || 9)).toFixed(6) : '0'} {outputToken?.symbol}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Minimum Received:</span>
              <span className="font-medium">
                {(parseInt(quote.otherAmountThreshold) / Math.pow(10, outputToken?.decimals || 9)).toFixed(6)} {outputToken?.symbol}
              </span>
            </div>
          </div>
        )}

        {/* Popular Tokens */}
        {popularTokens.length > 0 && (
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">Popular Tokens</label>
            <div className="flex flex-wrap gap-2">
              {popularTokens.map((token) => (
                <button
                  key={token.mint}
                  onClick={() => selectToken(token, inputToken ? 'output' : 'input')}
                  className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                >
                  {token.logoURI && (
                    <img src={token.logoURI} alt={token.symbol} className="w-4 h-4 rounded-full" />
                  )}
                  {token.symbol}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-600">
            {error}
          </div>
        )}

        {/* Success Message */}
        {success && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm text-green-600">
            {success}
          </div>
        )}

        {/* Swap Button */}
        <button
          onClick={handleSwap}
          disabled={!connected || loading || swapping || !quote}
          className="w-full py-4 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-400 disabled:to-gray-500 text-white font-semibold rounded-xl transition-all disabled:cursor-not-allowed"
        >
          {swapping ? (
            'Swapping...'
          ) : !connected ? (
            'Connect Wallet'
          ) : loading ? (
            'Loading Quote...'
          ) : !quote ? (
            'Enter Amount'
          ) : (
            'Swap'
          )}
        </button>
      </div>
    </div>
  )
}

export default SwapInterface
