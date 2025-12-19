import React from 'react'
import { useWallet } from '@solana/wallet-adapter-react'
import { WalletMultiButton } from '@solana/wallet-adapter-react-ui'

const WalletConnect: React.FC = () => {
  return (
    <div className="flex items-center gap-4">
      <WalletMultiButton className="!bg-gradient-to-r !from-purple-600 !to-blue-600 hover:!from-purple-700 hover:!to-blue-700" />
    </div>
  )
}

export default WalletConnect
