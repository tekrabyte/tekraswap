import { useNavigate } from "react-router-dom";
import { useWallet } from "@solana/wallet-adapter-react";
import { Button } from "@/components/ui/button";
import { WalletButton } from "@/components/WalletButton";
import { TransactionHistory } from "@/components/TransactionHistory";
import { TokenStats } from "@/components/TokenStats";
import { Zap, Home, ArrowRightLeft } from "lucide-react";
import { motion } from "framer-motion";

export default function DashboardPage() {
  const navigate = useNavigate();
  const { publicKey } = useWallet();

  return (
    <div className="min-h-screen bg-[#020408]">
      {/* Header */}
      <header className="p-6 md:p-12 border-b border-white/5">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate("/")}>
              <Zap className="h-8 w-8 text-[#1D6FFF]" />
              <span className="text-2xl font-heading font-bold text-white">TekrabyteSwap</span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Button
              data-testid="home-button"
              variant="ghost"
              onClick={() => navigate("/")}
              className="text-white/80 hover:text-white hover:bg-white/5"
            >
              <Home className="h-4 w-4 mr-2" />
              Home
            </Button>
            <Button
              data-testid="swap-button"
              variant="ghost"
              onClick={() => navigate("/swap")}
              className="text-white/80 hover:text-white hover:bg-white/5"
            >
              <ArrowRightLeft className="h-4 w-4 mr-2" />
              Swap
            </Button>
            <WalletButton />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6 md:p-12">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mb-8"
          >
            <h1 className="text-4xl font-bold text-white font-heading mb-2">Dashboard</h1>
            {publicKey ? (
              <p className="text-white/60 font-mono text-sm">
                Wallet: {publicKey.toString().slice(0, 8)}...{publicKey.toString().slice(-8)}
              </p>
            ) : (
              <p className="text-white/60 font-body">Connect your wallet to view your dashboard</p>
            )}
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="space-y-8"
          >
            {/* Token Stats */}
            <div data-testid="dashboard-token-stats">
              <TokenStats />
            </div>

            {/* Transaction History */}
            <div data-testid="dashboard-transaction-history">
              <TransactionHistory />
            </div>

            {!publicKey && (
              <div className="text-center py-12">
                <p className="text-white/60 font-body mb-6">Connect your wallet to start trading</p>
                <Button
                  onClick={() => navigate("/swap")}
                  className="bg-[#1D6FFF] hover:bg-[#1D6FFF]/90 text-white rounded-full px-8 py-4 font-medium"
                >
                  Go to Swap
                </Button>
              </div>
            )}
          </motion.div>
        </div>
      </main>
    </div>
  );
}