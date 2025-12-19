import { useState, useEffect } from "react";
import { useWallet } from "@solana/wallet-adapter-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Wallet, TrendingUp, Coins, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import axios from "axios";
import { motion } from "framer-motion";
import { formatPrice, formatLargeNumber, formatUSD } from "@/utils/formatNumber";
import { formatCurrency, formatLargeCurrency, formatTokenBalance } from "@/utils/formatCurrency";
import { useCurrency } from "@/contexts/CurrencyContext";
import { CurrencyToggle } from "@/components/CurrencyToggle";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export function PortfolioBalance({ compact = false, autoRefresh = true }) {
  const { publicKey, connected } = useWallet();
  const { currency, exchangeRate } = useCurrency();
  const [portfolio, setPortfolio] = useState({
    total_usd: 0,
    token_count: 0,
    tokens: []
  });
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    if (connected && publicKey) {
      fetchPortfolio();
      
      // Auto-refresh setiap 30 detik jika autoRefresh = true
      if (autoRefresh) {
        const interval = setInterval(() => {
          fetchPortfolio(true); // silent refresh
        }, 30000);
        
        return () => clearInterval(interval);
      }
    }
  }, [connected, publicKey, autoRefresh]);

  const fetchPortfolio = async (silent = false) => {
    if (!publicKey) return;
    
    if (!silent) setLoading(true);
    
    try {
      const response = await axios.get(`${API}/wallet-portfolio`, {
        params: { wallet: publicKey.toString() }
      });
      
      setPortfolio(response.data);
      setLastUpdate(new Date());
    } catch (error) {
      console.error("Error fetching portfolio:", error);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  if (!connected) {
    return (
      <Card className="backdrop-blur-xl bg-black/40 border border-white/10 shadow-2xl rounded-3xl">
        <CardContent className="p-6 text-center">
          <Wallet className="h-12 w-12 text-white/40 mx-auto mb-3" />
          <p className="text-white/60">Connect wallet untuk melihat portfolio</p>
        </CardContent>
      </Card>
    );
  }

  // Compact version untuk Swap page
  if (compact) {
    return (
      <Card className="backdrop-blur-xl bg-black/40 border border-white/10 shadow-xl rounded-2xl">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full">
                <Wallet className="h-5 w-5 text-white" />
              </div>
              <div>
                <div className="text-xs text-white/50 flex items-center gap-2">
                  <span>Total Balance</span>
                  <CurrencyToggle compact={true} />
                </div>
                <div className="text-xl font-bold text-white font-mono">
                  {formatCurrency(portfolio.total_usd, currency, exchangeRate, { useShortFormat: true })}
                </div>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => fetchPortfolio()}
              disabled={loading}
              className="text-white/60 hover:text-white"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
          <div className="text-xs text-white/40 mt-2">
            {portfolio.token_count} token{portfolio.token_count !== 1 ? 's' : ''}
            {lastUpdate && ` • Updated ${lastUpdate.toLocaleTimeString()}`}
          </div>
        </CardContent>
      </Card>
    );
  }

  // Full version untuk Dashboard
  return (
    <div className="space-y-4">
      {/* Total Balance Card */}
      <Card className="backdrop-blur-xl bg-gradient-to-br from-blue-900/40 to-purple-900/40 border border-white/10 shadow-2xl rounded-3xl">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-xl font-heading text-white flex items-center gap-2">
              <Wallet className="h-6 w-6" />
              Portfolio Balance
            </CardTitle>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => fetchPortfolio()}
              disabled={loading}
              className="text-white/60 hover:text-white"
            >
              <RefreshCw className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <div className="text-sm text-white/60 uppercase tracking-wider mb-1">Total Value</div>
              <div className="text-5xl font-bold text-white font-mono tracking-tight">
                {formatUSD(portfolio.total_usd)}
              </div>
            </div>
            
            <div className="flex gap-6 text-sm">
              <div>
                <div className="text-white/50">Total Tokens</div>
                <div className="text-white font-bold text-lg">{portfolio.token_count}</div>
              </div>
              {lastUpdate && (
                <div>
                  <div className="text-white/50">Last Update</div>
                  <div className="text-white font-medium">{lastUpdate.toLocaleTimeString()}</div>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Token List */}
      {portfolio.tokens.length > 0 && (
        <Card className="backdrop-blur-xl bg-black/40 border border-white/10 shadow-2xl rounded-3xl">
          <CardHeader>
            <CardTitle className="text-lg font-heading text-white flex items-center gap-2">
              <Coins className="h-5 w-5" />
              Your Tokens
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-96 overflow-y-auto custom-scrollbar">
              {portfolio.tokens.map((token, index) => (
                <motion.div
                  key={token.address}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="p-4 bg-white/5 border border-white/5 rounded-xl hover:bg-white/10 transition-all"
                >
                  <div className="flex items-center justify-between">
                    {/* Token Info */}
                    <div className="flex items-center gap-3 flex-1">
                      {token.logoURI ? (
                        <img
                          src={token.logoURI}
                          alt={token.symbol}
                          className="w-10 h-10 rounded-full"
                          onError={(e) => { e.target.style.display = "none"; }}
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold">
                          {token.symbol?.substring(0, 2)}
                        </div>
                      )}
                      <div>
                        <div className="font-bold text-white">{token.symbol}</div>
                        <div className="text-xs text-white/50">{token.name}</div>
                      </div>
                    </div>

                    {/* Balance & Value */}
                    <div className="text-right">
                      <div className="font-bold text-white">
                        {formatTokenBalance(token.balance, token.decimals)} {token.symbol}
                      </div>
                      <div className="text-sm text-white/60">
                        {formatUSD(token.value_usd)}
                      </div>
                      <div className="text-xs text-white/40">
                        @ {formatPrice(token.price_usd)}
                      </div>
                    </div>
                  </div>

                  {/* Market Data (jika ada) */}
                  {(token.volume_24h > 0 || token.market_cap > 0) && (
                    <div className="mt-3 pt-3 border-t border-white/5 grid grid-cols-2 gap-4 text-xs">
                      {token.volume_24h > 0 && (
                        <div>
                          <div className="text-white/40">24h Volume</div>
                          <div className="text-white/80 font-medium">
                            {formatLargeNumber(token.volume_24h, { showDollarSign: true, decimals: 2 })}
                          </div>
                        </div>
                      )}
                      {token.market_cap > 0 && (
                        <div>
                          <div className="text-white/40">Market Cap</div>
                          <div className="text-white/80 font-medium">
                            {formatLargeNumber(token.market_cap, { showDollarSign: true, decimals: 2 })}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
