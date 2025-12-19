import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { WalletButton } from "@/components/WalletButton";
import { SwapCard } from "@/components/SwapCard";
import { PriceChart } from "@/components/PriceChart";
import { TokenStats } from "@/components/TokenStats";
import { PortfolioBalance } from "@/components/PortfolioBalance";
import { Zap, Home } from "lucide-react";
import { motion } from "framer-motion";

export default function SwapPage() {
  const navigate = useNavigate();

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
              data-testid="dashboard-button"
              variant="ghost"
              onClick={() => navigate("/dashboard")}
              className="text-white/80 hover:text-white hover:bg-white/5"
            >
              Dashboard
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
            <h1 className="text-4xl font-bold text-white font-heading mb-2">Swap Tokens</h1>
            <p className="text-white/60 font-body">Trade tokens with the best rates from top DEXs</p>
          </motion.div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Swap Card - Main Focus */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="lg:col-span-1 flex justify-center lg:justify-start"
            >
              <SwapCard />
            </motion.div>

            {/* Charts & Stats */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="lg:col-span-2 space-y-6"
            >
              <TokenStats />
              <PriceChart />
            </motion.div>
          </div>
        </div>
      </main>
    </div>
  );
}