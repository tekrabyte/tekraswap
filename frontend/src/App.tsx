import React from 'react'
import { SolanaProvider } from './components/providers/SolanaProvider'
import SwapInterface from './components/SwapInterface'
import WalletConnect from './components/WalletConnect'

function App() {
  return (
    <SolanaProvider>
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50">
        <nav className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                  Jupiter Swap Widget
                </h1>
              </div>
              <WalletConnect />
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex flex-col items-center justify-center">
            <div className="text-center mb-8">
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                Swap Solana Tokens
              </h2>
              <p className="text-lg text-gray-600">
                Trade any SPL token with the best rates on Solana
              </p>
              <p className="text-sm text-purple-600 mt-2">
                Platform Fee: 0.5% per swap
              </p>
            </div>
            
            <SwapInterface />
          </div>
        </main>

        <footer className="mt-16 py-8 border-t border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <p className="text-center text-gray-500 text-sm">
              Powered by Jupiter Aggregator • Solana Mainnet
            </p>
          </div>
        </footer>
      </div>
    </SolanaProvider>
  )
}

export default App
