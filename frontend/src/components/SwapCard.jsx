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

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DEFAULT_INPUT_TOKEN = {
  address: "So11111111111111111111111111111111111111112",
  symbol: "SOL",
  name: "Wrapped SOL",
  decimals: 9,
  logoURI: "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/So11111111111111111111111111111111111111112/logo.png"
};

const DEFAULT_OUTPUT_TOKEN = {
  address: "4ymWDE5kwxZ5rxN3mWLvJEBHESbZSiqBuvWmSVcGqZdj",
  symbol: "TOKEN1",
  name: "User Token 1",
  decimals: 9,
  logoURI: null
};

export function SwapCard() {
  const { publicKey, sendTransaction, connected } = useWallet();
  const [inputToken, setInputToken] = useState(DEFAULT_INPUT_TOKEN);
  const [outputToken, setOutputToken] = useState(DEFAULT_OUTPUT_TOKEN);
  const [inputAmount, setInputAmount] = useState("");
  const [outputAmount, setOutputAmount] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedDEX, setSelectedDEX] = useState("jupiter");
  const [slippage, setSlippage] = useState(100);
  const [showSettings, setShowSettings] = useState(false);
  const [showInputTokenDialog, setShowInputTokenDialog] = useState(false);
  const [showOutputTokenDialog, setShowOutputTokenDialog] = useState(false);
  const [inputBalance, setInputBalance] = useState(null);
  const [outputBalance, setOutputBalance] = useState(null);

  useEffect(() => {
    if (connected && publicKey) {
      fetchBalances();
    }
  }, [connected, publicKey, inputToken, outputToken]);

  useEffect(() => {
    if (inputAmount && parseFloat(inputAmount) > 0) {
      fetchQuote();
    } else {
      setOutputAmount("");
    }
  }, [inputAmount, inputToken, outputToken, selectedDEX]);

  const fetchBalances = async () => {
    if (!publicKey) return;
    
    try {
      const inputBalanceResponse = await axios.get(`${API}/token-balance`, {
        params: {
          wallet: publicKey.toString(),
          token_mint: inputToken.address
        }
      });
      setInputBalance(inputBalanceResponse.data);

      const outputBalanceResponse = await axios.get(`${API}/token-balance`, {
        params: {
          wallet: publicKey.toString(),
          token_mint: outputToken.address
        }
      });
      setOutputBalance(outputBalanceResponse.data);
    } catch (error) {
      console.error("Error fetching balances:", error);
    }
  };

  const fetchQuote = async () => {
    try {
      const decimals = inputToken.decimals || 9;
      const amount = Math.floor(parseFloat(inputAmount) * Math.pow(10, decimals));
      
      const response = await axios.get(`${API}/quote`, {
        params: {
          inputMint: inputToken.address,
          outputMint: outputToken.address,
          amount,
          slippageBps: slippage,
        },
      });
      
      const outDecimals = outputToken.decimals || 9;
      const outAmount = parseFloat(response.data.outAmount) / Math.pow(10, outDecimals);
      setOutputAmount(outAmount.toFixed(6));
    } catch (error) {
      console.error("Quote error:", error);
      setOutputAmount("N/A");
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

      toast.success(`Swap successful! TX: ${signature.slice(0, 8)}...`);
      setInputAmount("");
      setOutputAmount("");
      
      // Refresh balances after swap
      setTimeout(() => fetchBalances(), 2000);
    } catch (error) {
      console.error("Swap error:", error);
      toast.error(error.response?.data?.detail || "Swap failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSwitchTokens = () => {
    const temp = inputToken;
    setInputToken(outputToken);
    setOutputToken(temp);
    setInputAmount(outputAmount);
    setOutputAmount("");
  };

  const TokenButton = ({ token, balance, onClick, label }) => (
    <button
      onClick={onClick}
      className="w-full p-3 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-all flex items-center justify-between group"
    >
      <div className="flex items-center gap-3">
        {token.logoURI ? (
          <img
            src={token.logoURI}
            alt={token.symbol}
            className="w-8 h-8 rounded-full"
            onError={(e) => {
              e.target.style.display = "none";
            }}
          />
        ) : (
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-sm">
            {token.symbol?.[0] || "?"}
          </div>
        )}
        <div className="text-left">
          <div className="text-sm font-medium text-white/80">{label}</div>
          <div className="text-lg font-bold text-white">{token.symbol}</div>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {connected && balance && (
          <div className="text-right mr-2">
            <div className="text-xs text-white/60">Balance</div>
            <div className="text-sm font-medium text-white">
              {balance.uiAmount?.toFixed(4) || "0"}
            </div>
          </div>
        )}
        <ChevronDown className="h-5 w-5 text-white/60 group-hover:text-white transition-colors" />
      </div>
    </button>
  );

  return (
    <>
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
            <div className="mt-4 p-4 bg-white/5 rounded-xl space-y-3">
              <div>
                <label className="text-sm text-white/60 font-mono">Slippage Tolerance (%)</label>
                <Input
                  type="number"
                  value={slippage / 100}
                  onChange={(e) => setSlippage(parseFloat(e.target.value) * 100)}
                  className="mt-2 bg-black/20 border-white/10 text-white"
                />
              </div>
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

          {/* Input Token Section */}
          <div className="space-y-2">
            <TokenButton
              token={inputToken}
              balance={inputBalance}
              onClick={() => setShowInputTokenDialog(true)}
              label="From"
            />
            <Input
              data-testid="input-amount"
              type="number"
              placeholder="0.0"
              value={inputAmount}
              onChange={(e) => setInputAmount(e.target.value)}
              disabled={loading}
              className="bg-black/20 border-white/10 focus:border-[#1D6FFF] focus:ring-1 focus:ring-[#1D6FFF] rounded-xl h-14 text-lg px-4 text-white font-mono placeholder:text-white/20"
            />
            {inputBalance && connected && (
              <div className="flex justify-between text-xs text-white/60 px-1">
                <span>Available: {inputBalance.uiAmount?.toFixed(4)}</span>
                <button
                  onClick={() => setInputAmount(inputBalance.uiAmount?.toString() || "0")}
                  className="text-purple-400 hover:text-purple-300"
                >
                  MAX
                </button>
              </div>
            )}
          </div>

          {/* Switch Button */}
          <div className="flex justify-center">
            <button
              onClick={handleSwitchTokens}
              className="p-2 bg-white/5 rounded-full hover:bg-white/10 transition-all hover:scale-110 active:scale-95"
            >
              <ArrowRightLeft className="h-5 w-5 text-[#1D6FFF]" />
            </button>
          </div>

          {/* Output Token Section */}
          <div className="space-y-2">
            <TokenButton
              token={outputToken}
              balance={outputBalance}
              onClick={() => setShowOutputTokenDialog(true)}
              label="To"
            />
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

      {/* Token Selection Dialogs */}
      <TokenSelectDialog
        open={showInputTokenDialog}
        onOpenChange={setShowInputTokenDialog}
        onSelectToken={(token) => {
          if (token.address === outputToken.address) {
            toast.error("Input and output tokens must be different");
            return;
          }
          setInputToken(token);
        }}
        selectedToken={inputToken}
      />

      <TokenSelectDialog
        open={showOutputTokenDialog}
        onOpenChange={setShowOutputTokenDialog}
        onSelectToken={(token) => {
          if (token.address === inputToken.address) {
            toast.error("Input and output tokens must be different");
            return;
          }
          setOutputToken(token);
        }}
        selectedToken={outputToken}
      />
    </>
  );
}