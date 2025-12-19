import { useEffect, useState } from "react";
import { useWallet } from "@solana/wallet-adapter-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { History, ExternalLink } from "lucide-react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export function TransactionHistory() {
  const { publicKey } = useWallet();
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (publicKey) {
      fetchHistory();
    }
  }, [publicKey]);

  const fetchHistory = async () => {
    if (!publicKey) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`${API}/swap-history`, {
        params: { wallet: publicKey.toString(), limit: 10 },
      });
      setTransactions(response.data.swaps || []);
    } catch (error) {
      console.error("History error:", error);
    } finally {
      setLoading(false);
    }
  };

  if (!publicKey) {
    return (
      <Card className="backdrop-blur-xl bg-black/40 border border-white/10 shadow-2xl rounded-3xl">
        <CardContent className="pt-6 text-center text-white/60">
          Connect wallet to view transaction history
        </CardContent>
      </Card>
    );
  }

  return (
    <Card 
      data-testid="transaction-history"
      className="backdrop-blur-xl bg-black/40 border border-white/10 shadow-2xl rounded-3xl"
    >
      <CardHeader>
        <div className="flex items-center gap-2">
          <History className="h-5 w-5 text-[#1D6FFF]" />
          <CardTitle className="text-xl font-heading text-white">Transaction History</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-white/60 text-center py-8">Loading...</div>
        ) : transactions.length === 0 ? (
          <div className="text-white/60 text-center py-8">No transactions yet</div>
        ) : (
          <div className="space-y-3">
            {transactions.map((tx, idx) => (
              <div
                key={tx.id || idx}
                data-testid="transaction-item"
                className="p-4 bg-white/5 rounded-xl border border-white/5 hover:border-white/10 transition-all"
              >
                <div className="flex justify-between items-start">
                  <div className="space-y-1">
                    <div className="text-sm font-medium text-white font-body">
                      Swap via {tx.dex === "jupiter" ? "Jupiter" : "Raydium"}
                    </div>
                    <div className="text-xs text-white/60 font-mono">
                      Amount: {(tx.inputAmount / 1e9).toFixed(4)} SOL
                    </div>
                    <div className="text-xs text-white/40 font-mono">
                      {new Date(tx.timestamp).toLocaleString()}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span 
                      className={`text-xs px-2 py-1 rounded-full font-mono ${
                        tx.status === "confirmed" 
                          ? "bg-green-500/20 text-green-400" 
                          : "bg-yellow-500/20 text-yellow-400"
                      }`}
                    >
                      {tx.status}
                    </span>
                    {tx.txHash && (
                      <a
                        href={`https://solscan.io/tx/${tx.txHash}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[#1D6FFF] hover:text-[#1D6FFF]/80"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}