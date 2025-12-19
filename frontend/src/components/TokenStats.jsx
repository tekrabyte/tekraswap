import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Coins, TrendingUp, Activity } from "lucide-react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TARGET_TOKEN = "4ymWDE5kwxZ5rxN3mWLvJEBHESbZSiqBuvWmSVcGqZdj";

export function TokenStats() {
  const [stats, setStats] = useState({
    price_usd: 0.0,
    volume_24h: 0.0,
    market_cap: 0.0,
  });

  useEffect(() => {
    fetchTokenStats();
  }, []);

  const fetchTokenStats = async () => {
    try {
      const response = await axios.get(`${API}/token-info`, {
        params: { address: TARGET_TOKEN },
      });
      setStats(response.data);
    } catch (error) {
      console.error("Token stats error:", error);
    }
  };

  const statItems = [
    {
      label: "Price",
      value: `$${stats.price_usd.toFixed(6)}`,
      icon: Coins,
      testId: "price-stat",
    },
    {
      label: "24h Volume",
      value: `$${(stats.volume_24h / 1000).toFixed(1)}K`,
      icon: Activity,
      testId: "volume-stat",
    },
    {
      label: "Market Cap",
      value: `$${(stats.market_cap / 1000000).toFixed(1)}M`,
      icon: TrendingUp,
      testId: "market-cap-stat",
    },
  ];

  return (
    <div data-testid="token-stats" className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
  );
}