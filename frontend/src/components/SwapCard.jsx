import { useState, useEffect } from "react";
import { useWallet } from "@solana/wallet-adapter-react";
import { Connection, VersionedTransaction } from "@solana/web3.js";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowRightLeft, Loader2, Settings, ChevronDown } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";
import { TokenSelectDialog } from "@/components/TokenSelectDialog";
import { useCurrency } from "@/contexts/CurrencyContext";
import { formatPrice, formatPriceWithCurrency, formatIDR } from "@/utils/formatNumber";

// Setup API URL
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";
const API = `${BACKEND_URL}/api`;

const DEFAULT_INPUT_TOKEN = {
  address: "So11111111111111111111111111111111111111112",
  symbol: "SOL",
  name: "Wrapped SOL",
  decimals: 9,
  logoURI: "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/So11111111111111111111111111111111111111112/logo.png"
};

const DEFAULT_OUTPUT_TOKEN = {
  address: "FShCGqGUWRZkqovteJBGegUJAcjRzHZiBmHYGgSqpump", // Ganti default ke USDC dulu biar pasti ada harga
  symbol: "TEKRA",
  name: "TekraByte (MemeCoin)",
  decimals: 9,
  logoURI: "https://tekrabyte.com/crypto/meme_tekrabyte/logo.png"
};

export function SwapCard() {
  const { publicKey, sendTransaction, connected } = useWallet();
  
  // State Token
  const [inputToken, setInputToken] = useState(DEFAULT_INPUT_TOKEN);
  const [outputToken, setOutputToken] = useState(DEFAULT_OUTPUT_TOKEN);
  
  // State Amount
  const [inputAmount, setInputAmount] = useState("");
  const [outputAmount, setOutputAmount] = useState("");
  
  // State Harga & Balance
  const [inputBalance, setInputBalance] = useState(null);
  const [outputBalance, setOutputBalance] = useState(null);
  const [inputPrice, setInputPrice] = useState(0); // Harga Pasar Input
  const [outputPrice, setOutputPrice] = useState(0); // Harga Pasar Output

  // UI States
  const [loading, setLoading] = useState(false);
  const [selectedDEX, setSelectedDEX] = useState("jupiter");
  const [slippage, setSlippage] = useState(100);
  const [showSettings, setShowSettings] = useState(false);
  const [showInputTokenDialog, setShowInputTokenDialog] = useState(false);
  const [showOutputTokenDialog, setShowOutputTokenDialog] = useState(false);

  // 1. Fetch Balance & Price saat Wallet connect atau Token berubah
  useEffect(() => {
    fetchTokenData(inputToken, "input");
    fetchTokenData(outputToken, "output");
  }, [connected, publicKey, inputToken, outputToken]);

  // 2. Fetch Quote (Swap Rate) saat amount berubah
  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (inputAmount && parseFloat(inputAmount) > 0) {
        fetchQuote();
      } else {
        setOutputAmount("");
      }
    }, 500); // Debounce biar gak spam API

    return () => clearTimeout(delayDebounceFn);
  }, [inputAmount, inputToken, outputToken, selectedDEX]);

  // --- FUNGSI FETCH DATA LENGKAP (Balance + Harga) ---
  const fetchTokenData = async (token, type) => {
    try {
      // A. Ambil Metadata (Harga Pasar)
      console.log(`Fetching Metadata for ${token.symbol}...`);
      const metaRes = await axios.get(`${API}/token-metadata/${token.address}`);
      const price = metaRes.data.price_per_token || 0;
      
      if (type === "input") setInputPrice(price);
      else setOutputPrice(price);

      // B. Ambil Balance (Hanya jika wallet connect)
      if (publicKey) {
        console.log(`Fetching Balance for ${token.symbol}...`);
        const balRes = await axios.get(`${API}/token-balance`, {
          params: {
            wallet: publicKey.toString(),
            token_mint: token.address
          }
        });
        
        console.log(`Balance ${token.symbol}:`, balRes.data);
        if (type === "input") setInputBalance(balRes.data);
        else setOutputBalance(balRes.data);
      }
    } catch (error) {
      console.error(`Error fetching data for ${token.symbol}:`, error);
    }
  };

  const fetchQuote = async () => {
    try {
      const decimals = inputToken.decimals || 9;
      // Fix: Gunakan Math.round untuk menghindari floating point error
      const amount = Math.floor(parseFloat(inputAmount) * Math.pow(10, decimals));
      
      const response = await axios.get(`${API}/quote`, {
        params: {
            // Pastikan parameter sesuai dengan backend FastAPI
            inputMint: inputToken.address,
            outputMint: outputToken.address,
            amount: amount, // Backend minta integer (lamports/satoshis)
            slippageBps: slippage,
        },
      });
      
      const outDecimals = outputToken.decimals || 9;
      const outAmountRaw = response.data.outAmount || response.data.expectedOutput; // Handle beda nama field
      const outAmount = parseFloat(outAmountRaw) / Math.pow(10, outDecimals);
      
      setOutputAmount(outAmount.toFixed(6));
    } catch (error) {
      console.error("Quote error:", error);
      // Jangan set N/A, kosongkan saja biar UI bersih
      setOutputAmount(""); 
    }
  };

  const handleSwap = async () => {
    if (!connected || !publicKey) {
      toast.error("Please connect your wallet");
      return;
    }

    setLoading(true);
    try {
      const decimals = inputToken.decimals || 9;
      const amount = Math.floor(parseFloat(inputAmount) * Math.pow(10, decimals));
      
      const response = await axios.post(`${API}/swap`, {
        inputMint: inputToken.address,
        outputMint: outputToken.address,
        amount,
        slippageBps: slippage,
        userPublicKey: publicKey.toString(),
        dex: selectedDEX,
      });

      const swapTransactionBuf = Buffer.from(response.data.transaction, "base64");
      const transaction = VersionedTransaction.deserialize(swapTransactionBuf);

      const connection = new Connection(process.env.REACT_APP_HELIUS_RPC || "https://api.mainnet-beta.solana.com");
      const signature = await sendTransaction(transaction, connection, {
        skipPreflight: false,
      });

      toast.success(`Swap successful!`);
      setInputAmount("");
      setOutputAmount("");
      
      // Refresh balances
      setTimeout(() => {
        fetchTokenData(inputToken, "input");
        fetchTokenData(outputToken, "output");
      }, 2000);
    } catch (error) {
      console.error("Swap error:", error);
      toast.error("Swap failed. Check console for details.");
    } finally {
      setLoading(false);
    }
  };

  const handleSwitchTokens = () => {
    const tempToken = inputToken;
    const tempAmount = inputAmount; // Simpan nilai input lama
    
    setInputToken(outputToken);
    setOutputToken(tempToken);
    
    // Switch Harga & Balance UI juga
    const tempPrice = inputPrice;
    setInputPrice(outputPrice);
    setOutputPrice(tempPrice);

    // Reset amount karena quote akan berubah
    setInputAmount(""); 
    setOutputAmount("");
  };

  // Komponen Tombol Token yang sudah diperbaiki Tampilannya
  const TokenButton = ({ token, balance, price, onClick, label }) => (
    <button
      onClick={onClick}
      className="w-full p-3 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-all flex items-center justify-between group"
    >
      <div className="flex items-center gap-3">
        {/* LOGO */}
        {token.logoURI ? (
          <img
            src={token.logoURI}
            alt={token.symbol}
            className="w-8 h-8 rounded-full"
            onError={(e) => { e.target.style.display = "none"; }}
          />
        ) : (
          <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold text-xs">
            {token.symbol?.substring(0, 2)}
          </div>
        )}
        
        {/* NAMA & SYMBOL */}
        <div className="text-left">
          <div className="text-sm font-medium text-white/80">{label}</div>
          <div className="text-lg font-bold text-white flex items-center gap-2">
            {token.symbol}
            <ChevronDown className="h-4 w-4 text-white/60" />
          </div>
        </div>
      </div>

      {/* BALANCE & HARGA */}
      <div className="text-right">
        {connected && balance ? (
          <>
            <div className="text-sm font-medium text-white">
              {balance.uiAmount?.toFixed(4) || "0"}
            </div>
            <div className="text-xs text-white/50">
              {/* Tampilkan Harga per Token */}
              ≈ ${price ? price.toFixed(4) : "0.00"}
            </div>
          </>
        ) : (
          <div className="text-xs text-white/40">--</div>
        )}
      </div>
    </button>
  );

  return (
    <>
      <Card className="w-full max-w-md backdrop-blur-xl bg-black/40 border border-white/10 shadow-2xl rounded-3xl">
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="text-2xl font-heading text-white">Swap</CardTitle>
            <Button variant="ghost" size="icon" onClick={() => setShowSettings(!showSettings)}>
              <Settings className="h-5 w-5 text-white/60" />
            </Button>
          </div>
          {/* Settings Area */}
          {showSettings && (
             <div className="mt-2 p-3 bg-white/5 rounded-lg">
                <label className="text-xs text-white/60">Slippage (%)</label>
                <Input 
                   type="number" 
                   value={slippage/100} 
                   onChange={(e) => setSlippage(Number(e.target.value)*100)} 
                   className="mt-1 bg-black/40 border-white/10 text-white h-8"
                />
             </div>
          )}
        </CardHeader>
        
        <CardContent className="space-y-4">
          
          {/* INPUT AREA */}
          <div className="bg-black/20 p-4 rounded-2xl border border-white/5 space-y-3">
            <TokenButton
              token={inputToken}
              balance={inputBalance}
              price={inputPrice}
              onClick={() => setShowInputTokenDialog(true)}
              label="From"
            />
            <div className="flex justify-between items-center bg-black/20 rounded-xl px-3">
                <Input
                type="number"
                placeholder="0.0"
                value={inputAmount}
                onChange={(e) => setInputAmount(e.target.value)}
                className="bg-transparent border-none text-2xl text-white font-mono h-14 p-0 focus-visible:ring-0 placeholder:text-white/20"
                />
                {/* Total USD Value */}
                <div className="text-xs text-white/40">
                    ≈ ${(inputAmount * inputPrice).toFixed(2)}
                </div>
            </div>
          </div>

          {/* SWITCH ARROW */}
          <div className="flex justify-center -my-3 relative z-10">
            <button onClick={handleSwitchTokens} className="bg-[#1D6FFF] p-2 rounded-full border-4 border-black shadow-lg hover:scale-110 transition">
              <ArrowRightLeft className="h-4 w-4 text-white" />
            </button>
          </div>

          {/* OUTPUT AREA */}
          <div className="bg-black/20 p-4 rounded-2xl border border-white/5 space-y-3">
            <TokenButton
              token={outputToken}
              balance={outputBalance}
              price={outputPrice}
              onClick={() => setShowOutputTokenDialog(true)}
              label="To (Est.)"
            />
            <div className="flex justify-between items-center bg-black/20 rounded-xl px-3">
                <Input
                type="number"
                placeholder="0.0"
                value={outputAmount}
                disabled
                className="bg-transparent border-none text-2xl text-white font-mono h-14 p-0 focus-visible:ring-0 disabled:opacity-80"
                />
                <div className="text-xs text-white/40">
                    ≈ ${(outputAmount * outputPrice).toFixed(2)}
                </div>
            </div>
          </div>

          {/* SWAP BUTTON */}
          <Button
            onClick={handleSwap}
            disabled={loading || !connected || !inputAmount}
            className="w-full bg-[#1D6FFF] hover:bg-[#1D6FFF]/80 text-white h-14 rounded-xl text-lg font-bold shadow-lg shadow-blue-900/20"
          >
            {loading ? <Loader2 className="animate-spin mr-2" /> : !connected ? "Connect Wallet" : "Swap Now"}
          </Button>

        </CardContent>
      </Card>

      {/* DIALOGS - Pastikan paste address dilakukan DI SINI */}
      <TokenSelectDialog
        open={showInputTokenDialog}
        onOpenChange={setShowInputTokenDialog}
        onSelectToken={setInputToken}
        selectedToken={inputToken}
      />
      <TokenSelectDialog
        open={showOutputTokenDialog}
        onOpenChange={setShowOutputTokenDialog}
        onSelectToken={setOutputToken}
        selectedToken={outputToken}
      />
    </>
  );
}