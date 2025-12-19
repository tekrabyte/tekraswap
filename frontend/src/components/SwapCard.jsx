import { useState, useEffect } from "react";
import { useWallet } from "@solana/wallet-adapter-react";
import { Connection, VersionedTransaction } from "@solana/web3.js";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowRightLeft, Loader2, Settings } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SOL_MINT = "So11111111111111111111111111111111111111112";
const TARGET_TOKEN = "4ymWDE5kwxZ5rxN3mWLvJEBHESbZSiqBuvWmSVcGqZdj";

export function SwapCard() {
  const { publicKey, sendTransaction, connected } = useWallet();
  const [inputAmount, setInputAmount] = useState("");
  const [outputAmount, setOutputAmount] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedDEX, setSelectedDEX] = useState("jupiter");
  const [slippage, setSlippage] = useState(100);
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    if (inputAmount && parseFloat(inputAmount) > 0) {
      fetchQuote();
    } else {
      setOutputAmount("");
    }
  }, [inputAmount, selectedDEX]);

  const fetchQuote = async () => {
    try {
      const amount = Math.floor(parseFloat(inputAmount) * 1e9);
      const response = await axios.get(`${API}/quote`, {
        params: {
          inputMint: SOL_MINT,
          outputMint: TARGET_TOKEN,
          amount,
          slippageBps: slippage,
        },
      });
      
      const outAmount = parseFloat(response.data.outAmount) / 1e9;
      setOutputAmount(outAmount.toFixed(4));
    } catch (error) {
      console.error("Quote error:", error);
    }
  };

  const handleSwap = async () => {
    if (!connected || !publicKey) {
      toast.error("Please connect your wallet");
      return;
    }

    if (!inputAmount || parseFloat(inputAmount) <= 0) {
      toast.error("Please enter an amount");
      return;
    }

    setLoading(true);

    try {
      const amount = Math.floor(parseFloat(inputAmount) * 1e9);
      
      const response = await axios.post(`${API}/swap`, {
        inputMint: SOL_MINT,
        outputMint: TARGET_TOKEN,
        amount,
        slippageBps: slippage,
        userPublicKey: publicKey.toString(),
        dex: selectedDEX,
      });

      const swapTransactionBuf = Buffer.from(response.data.transaction, "base64");
      const transaction = VersionedTransaction.deserialize(swapTransactionBuf);

      const connection = new Connection("https://api.mainnet-beta.solana.com");
      const signature = await sendTransaction(transaction, connection, {
        skipPreflight: false,
      });

      toast.success(`Swap successful! TX: ${signature.slice(0, 8)}...`);
      setInputAmount("");
      setOutputAmount("");
    } catch (error) {
      console.error("Swap error:", error);
      toast.error(error.response?.data?.detail || "Swap failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card 
      data-testid="swap-card"
      className="w-full max-w-md backdrop-blur-xl bg-black/40 border border-white/10 shadow-2xl rounded-3xl"
    >
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle className="text-2xl font-heading text-white">Swap Tokens</CardTitle>
          <Button
            data-testid="settings-button"
            variant="ghost"
            size="icon"
            onClick={() => setShowSettings(!showSettings)}
            className="text-white/60 hover:text-white"
          >
            <Settings className="h-5 w-5" />
          </Button>
        </div>
        
        {showSettings && (
          <div className="mt-4 p-4 bg-white/5 rounded-xl">
            <label className="text-sm text-white/60 font-mono">Slippage Tolerance (%)</label>
            <Input
              type="number"
              value={slippage / 100}
              onChange={(e) => setSlippage(parseFloat(e.target.value) * 100)}
              className="mt-2 bg-black/20 border-white/10 text-white"
            />
          </div>
        )}
      </CardHeader>
      
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Button
            data-testid="jupiter-dex-button"
            variant={selectedDEX === "jupiter" ? "default" : "outline"}
            onClick={() => setSelectedDEX("jupiter")}
            className={`flex-1 rounded-full ${selectedDEX === "jupiter" ? "bg-[#1D6FFF] hover:bg-[#1D6FFF]/90" : "bg-white/5 hover:bg-white/10 text-white border-white/10"}`}
          >
            Jupiter
          </Button>
          <Button
            data-testid="raydium-dex-button"
            variant={selectedDEX === "raydium" ? "default" : "outline"}
            onClick={() => setSelectedDEX("raydium")}
            className={`flex-1 rounded-full ${selectedDEX === "raydium" ? "bg-[#1D6FFF] hover:bg-[#1D6FFF]/90" : "bg-white/5 hover:bg-white/10 text-white border-white/10"}`}
          >
            Raydium
          </Button>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-white/80 font-body">You Pay (SOL)</label>
          <Input
            data-testid="input-amount"
            type="number"
            placeholder="0.0"
            value={inputAmount}
            onChange={(e) => setInputAmount(e.target.value)}
            disabled={loading}
            className="bg-black/20 border-white/10 focus:border-[#1D6FFF] focus:ring-1 focus:ring-[#1D6FFF] rounded-xl h-14 text-lg px-4 text-white font-mono placeholder:text-white/20"
          />
        </div>

        <div className="flex justify-center">
          <div className="p-2 bg-white/5 rounded-full">
            <ArrowRightLeft className="h-5 w-5 text-[#1D6FFF]" />
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-white/80 font-body">You Receive</label>
          <Input
            data-testid="output-amount"
            type="text"
            placeholder="0.0"
            value={outputAmount}
            disabled
            className="bg-black/20 border-white/10 rounded-xl h-14 text-lg px-4 text-white font-mono placeholder:text-white/20"
          />
        </div>

        <Button
          data-testid="swap-button"
          onClick={handleSwap}
          disabled={loading || !connected || !inputAmount}
          className="w-full bg-[#1D6FFF] hover:bg-[#1D6FFF]/90 text-white rounded-full px-8 py-6 text-lg font-medium transition-all hover:scale-105 active:scale-95 shadow-[0_0_20px_rgba(29,111,255,0.3)] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Swapping...
            </>
          ) : !connected ? (
            "Connect Wallet"
          ) : (
            "Swap"
          )}
        </Button>

        {!connected && (
          <div className="text-sm text-yellow-500/80 text-center font-body" data-testid="connect-wallet-message">
            Please connect your wallet to proceed
          </div>
        )}
      </CardContent>
    </Card>
  );
}