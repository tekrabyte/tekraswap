import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Area, AreaChart } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TARGET_TOKEN = "4ymWDE5kwxZ5rxN3mWLvJEBHESbZSiqBuvWmSVcGqZdj";

export function PriceChart() {
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchChartData();
  }, []);

  const fetchChartData = async () => {
    try {
      const response = await axios.get(`${API}/price-chart`, {
        params: { token: TARGET_TOKEN, interval: "1h" },
      });
      
      const formattedData = response.data.data.map(item => ({
        time: new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        price: item.price,
      }));
      
      setChartData(formattedData);
    } catch (error) {
      console.error("Chart data error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card 
      data-testid="price-chart"
      className="backdrop-blur-xl bg-black/40 border border-white/10 shadow-2xl rounded-3xl"
    >
      <CardHeader>
        <CardTitle className="text-xl font-heading text-white">Price Chart (24H)</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="h-[300px] flex items-center justify-center text-white/60">
            Loading chart...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#1D6FFF" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#1D6FFF" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis 
                dataKey="time" 
                stroke="#94A3B8" 
                style={{ fontSize: "12px", fontFamily: "JetBrains Mono" }}
              />
              <YAxis 
                stroke="#94A3B8" 
                style={{ fontSize: "12px", fontFamily: "JetBrains Mono" }}
                tickFormatter={(value) => `$${value.toFixed(4)}`}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: "rgba(11, 12, 18, 0.95)",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "12px",
                  color: "#fff",
                }}
                formatter={(value) => [`$${value.toFixed(6)}`, "Price"]}
              />
              <Area
                type="monotone"
                dataKey="price"
                stroke="#1D6FFF"
                strokeWidth={2}
                fill="url(#colorPrice)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}