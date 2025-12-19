import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { WalletButton } from "@/components/WalletButton";
import { Zap, ArrowRightLeft, LineChart, Shield } from "lucide-react";
import { motion } from "framer-motion";

export default function HomePage() {
  const navigate = useNavigate();

  const features = [
    {
      icon: ArrowRightLeft,
      title: "Instant Swaps",
      description: "Trade tokens instantly with best prices from Jupiter & Raydium",
    },
    {
      icon: LineChart,
      title: "Real-time Charts",
      description: "Monitor price movements with live market data",
    },
    {
      icon: Shield,
      title: "Secure Trading",
      description: "Non-custodial swaps with multi-wallet support",
    },
  ];

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 z-0">
        <div 
          className="absolute inset-0 bg-cover bg-center opacity-20"
          style={{
            backgroundImage: "url('https://images.unsplash.com/photo-1633538475696-a93e30810e09?crop=entropy&cs=srgb&fm=jpg&q=85')",
          }}
        />
        <div className="absolute inset-0 bg-gradient-radial from-[#1D6FFF]/10 via-[#020408]/50 to-[#020408]" />
      </div>

      {/* Header */}
      <header className="relative z-10 p-6 md:p-12">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Zap className="h-8 w-8 text-[#1D6FFF]" />
            <span className="text-2xl font-heading font-bold text-white">TekrabyteSwap</span>
          </div>
          <div className="flex items-center gap-4">
            <Button
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

      {/* Hero Section */}
      <main className="relative z-10 px-6 md:px-12 py-24">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center space-y-8 mb-20"
          >
            <h1 
              data-testid="hero-title"
              className="text-5xl md:text-7xl font-bold tracking-tighter leading-none font-heading text-white"
            >
              Trade Solana Tokens
              <br />
              <span className="text-[#1D6FFF]">Instantly</span>
            </h1>
            <p className="text-lg md:text-xl leading-relaxed text-white/60 font-body max-w-2xl mx-auto">
              The best DEX aggregator on Solana. Get optimal prices across Jupiter and Raydium with a single click.
            </p>
            <div className="flex gap-4 justify-center">
              <Button
                data-testid="get-started-button"
                onClick={() => navigate("/swap")}
                className="bg-[#1D6FFF] hover:bg-[#1D6FFF]/90 text-white rounded-full px-8 py-6 text-lg font-medium transition-all hover:scale-105 active:scale-95 shadow-[0_0_20px_rgba(29,111,255,0.3)]"
              >
                Start Swapping
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate("/dashboard")}
                className="bg-white/5 hover:bg-white/10 text-white border border-white/10 rounded-full px-6 py-6 backdrop-blur-md transition-all"
              >
                View Dashboard
              </Button>
            </div>
          </motion.div>

          {/* Features */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="grid grid-cols-1 md:grid-cols-3 gap-6"
            data-testid="features-section"
          >
            {features.map((feature, idx) => (
              <div
                key={idx}
                className="p-8 backdrop-blur-xl bg-black/40 border border-white/10 rounded-3xl hover:border-white/20 transition-all"
              >
                <div className="mb-4 p-3 bg-[#1D6FFF]/10 rounded-2xl w-fit">
                  <feature.icon className="h-8 w-8 text-[#1D6FFF]" />
                </div>
                <h3 className="text-xl font-semibold text-white font-heading mb-2">
                  {feature.title}
                </h3>
                <p className="text-white/60 font-body leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </motion.div>

          {/* CTA Section */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="mt-20 text-center"
          >
            <div className="p-12 backdrop-blur-xl bg-gradient-to-br from-[#1D6FFF]/20 to-[#1D6FFF]/5 border border-[#1D6FFF]/30 rounded-3xl max-w-3xl mx-auto">
              <h2 className="text-3xl md:text-4xl font-bold text-white font-heading mb-4">
                Ready to trade?
              </h2>
              <p className="text-white/60 font-body mb-6">
                Connect your wallet and start trading with the best rates on Solana
              </p>
              <Button
                data-testid="cta-swap-button"
                onClick={() => navigate("/swap")}
                className="bg-[#1D6FFF] hover:bg-[#1D6FFF]/90 text-white rounded-full px-8 py-6 text-lg font-medium transition-all hover:scale-105 active:scale-95 shadow-[0_0_20px_rgba(29,111,255,0.3)]"
              >
                Launch App
              </Button>
            </div>
          </motion.div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 p-6 md:p-12 mt-20 border-t border-white/5">
        <div className="max-w-7xl mx-auto text-center text-white/40 text-sm font-mono">
          © 2025 TekrabyteSwap. Built on Solana.
        </div>
      </footer>
    </div>
  );
}