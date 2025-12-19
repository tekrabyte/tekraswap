import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Coins, TrendingUp, Activity, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import axios from "axios";
import { formatPrice, formatLargeNumber } from "@/utils/formatNumber";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TARGET_TOKEN = "4ymWDE5kwxZ5rxN3mWLvJEBHESbZSiqBuvWmSVcGqZdj";

export function TokenStats() {
  // 1. State awal dengan nilai default angka 0 (bukan null/undefined)
  const [stats, setStats] = useState({
    price_usd: 0,
    volume_24h: 0,
    market_cap: 0,
  });
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    fetchTokenStats();
    
    // Auto-refresh setiap 30 detik
    const interval = setInterval(() => {
      fetchTokenStats(true); // silent refresh
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchTokenStats = async (silent = false) => {
    if (!silent) setLoading(true);
    
    try {
      // Cek apakah URL backend sudah benar
      console.log("Fetching stats from:", `${API}/token-info?address=${TARGET_TOKEN}`);
      
      const response = await axios.get(`${API}/token-info`, {
        params: { address: TARGET_TOKEN },
      });

      const data = response.data || {};
      console.log("Data received:", data);

      // 2. MAPPING DATA (KUNCI PERBAIKAN)
      // Kita ambil data dari berbagai kemungkinan nama key yang dikirim backend
      // Jika kosong, kita paksa jadi angka 0
      setStats({
        price_usd: Number(data.price_usd || data.price_per_token || 0),
        volume_24h: Number(data.volume_24h || data.volume || 0),
        market_cap: Number(data.market_cap || data.fdv || 0),
      });
      
      setLastUpdate(new Date());

    } catch (error) {
      console.error("Token stats error:", error);
      // Jika error, biarkan state tetap 0, jangan buat crash
    } finally {
      if (!silent) setLoading(false);
    }
  };

  const statItems = [
    {
      label: "Price",
      // FIXED: Gunakan formatPrice utility untuk menghindari scientific notation
      value: formatPrice(stats.price_usd),
      icon: Coins,
      testId: "price-stat",
    },
    {
      label: "24h Volume",
      // FIXED: Gunakan formatLargeNumber untuk format K/M/B
      value: formatLargeNumber(stats.volume_24h, { showDollarSign: true, decimals: 2 }),
      icon: Activity,
      testId: "volume-stat",
    },
    {
      label: "Market Cap",
      // FIXED: Gunakan formatLargeNumber untuk format K/M/B
      value: formatLargeNumber(stats.market_cap, { showDollarSign: true, decimals: 2 }),
      icon: TrendingUp,
      testId: "market-cap-stat",
    },
  ];

  return (
    <div data-testid="token-stats" className="space-y-3">
      {/* Header with refresh button */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-white">TEKRA Token Stats</h3>
        <div className="flex items-center gap-2">
          {lastUpdate && (
            <span className="text-xs text-white/40">
              {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => fetchTokenStats()}
            disabled={loading}
            className="h-8 w-8 text-white/60 hover:text-white"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {statItems.map((stat) => (
          <Card
            key={stat.label}
            data-testid={stat.testId}
            className="backdrop-blur-xl bg-black/40 border border-white/10 shadow-2xl rounded-3xl hover:border-white/20 transition-all"
          >
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-white/60 uppercase tracking-wide font-mono">
                  {stat.label}
                </span>
                <stat.icon className="h-5 w-5 text-[#1D6FFF]" />
              </div>
              <div className="text-2xl font-bold text-white font-mono tracking-tight">
                {stat.value}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}