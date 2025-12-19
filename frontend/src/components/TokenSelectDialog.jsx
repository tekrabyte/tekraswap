import { useState, useEffect, useMemo } from "react";
import { useWallet } from "@solana/wallet-adapter-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, X } from "lucide-react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export function TokenSelectDialog({ open, onOpenChange, onSelectToken, selectedToken }) {
  const { publicKey } = useWallet();
  const [tokens, setTokens] = useState([]);
  const [balances, setBalances] = useState({});
  const [searchQuery, setSearchQuery] = useState("");
  const [customAddress, setCustomAddress] = useState("");
  const [loading, setLoading] = useState(false);
  const [showCustomInput, setShowCustomInput] = useState(false);

  useEffect(() => {
    if (open) {
      fetchTokenList();
    }
  }, [open]);

  useEffect(() => {
    if (open && publicKey && tokens.length > 0) {
      fetchBalances();
    }
  }, [open, publicKey, tokens]);

  const fetchTokenList = async () => {
    try {
      const response = await axios.get(`${API}/token-list`);
      setTokens(response.data.tokens || []);
    } catch (error) {
      console.error("Error fetching token list:", error);
    }
  };

  const fetchBalances = async () => {
    if (!publicKey) return;
    
    try {
      const tokenMints = tokens.map(t => t.address);
      const response = await axios.post(`${API}/token-balances`, {
        wallet: publicKey.toString(),
        token_mints: tokenMints
      });
      setBalances(response.data.balances || {});
    } catch (error) {
      console.error("Error fetching balances:", error);
    }
  };

  const handleCustomToken = async () => {
    if (!customAddress.trim()) return;
    
    setLoading(true);
    try {
      // Validate token
      const validateResponse = await axios.post(`${API}/validate-token/${customAddress}`);
      
      if (!validateResponse.data.valid) {
        alert("Invalid token address");
        return;
      }

      // Get metadata
      const metadataResponse = await axios.get(`${API}/token-metadata/${customAddress}`);
      const metadata = metadataResponse.data;

      // Add to token list
      const existingToken = tokens.find(t => t.address === customAddress);
      if (!existingToken) {
        setTokens(prev => [...prev, metadata]);
      }

      // Select the token
      onSelectToken(metadata);
      onOpenChange(false);
      setCustomAddress("");
      setShowCustomInput(false);
    } catch (error) {
      console.error("Error adding custom token:", error);
      alert(error.response?.data?.detail || "Failed to add token");
    } finally {
      setLoading(false);
    }
  };

  const filteredTokens = useMemo(() => {
    if (!searchQuery.trim()) return tokens;
    
    const query = searchQuery.trim().toLowerCase();
    
    return tokens.filter(token => {
      // Search by name (case insensitive)
      const nameMatch = token.name?.toLowerCase().includes(query);
      
      // Search by symbol (case insensitive)
      const symbolMatch = token.symbol?.toLowerCase().includes(query);
      
      // Search by address (case insensitive, support partial match)
      // User bisa paste full address atau sebagian address
      const addressMatch = token.address?.toLowerCase().includes(query);
      
      return nameMatch || symbolMatch || addressMatch;
    });
  }, [tokens, searchQuery]);

  const handleSelectToken = (token) => {
    onSelectToken(token);
    onOpenChange(false);
    setSearchQuery("");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md bg-[#0B0C12] border-white/10">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold text-white">
            Pilih Token
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Search Input */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <Input
              placeholder="Cari nama atau paste address"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-white/5 border-white/10 text-white"
            />
          </div>

          {/* Custom Token Input */}
          {showCustomInput ? (
            <div className="space-y-2 p-3 bg-white/5 rounded-lg border border-white/10">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">Custom Token Address</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setShowCustomInput(false);
                    setCustomAddress("");
                  }}
                  className="h-6 w-6 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <Input
                placeholder="Paste token address"
                value={customAddress}
                onChange={(e) => setCustomAddress(e.target.value)}
                className="bg-white/5 border-white/10 text-white text-sm"
              />
              <Button
                onClick={handleCustomToken}
                disabled={loading || !customAddress.trim()}
                className="w-full bg-gradient-to-r from-purple-500 to-pink-500"
                size="sm"
              >
                {loading ? "Validating..." : "Add Token"}
              </Button>
            </div>
          ) : (
            <Button
              variant="outline"
              onClick={() => setShowCustomInput(true)}
              className="w-full border-white/10 text-purple-400 hover:bg-white/5"
            >
              + Add Custom Token
            </Button>
          )}

          {/* Token List */}
          <div className="max-h-96 overflow-y-auto space-y-1 custom-scrollbar">
            {filteredTokens.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                No tokens found
              </div>
            ) : (
              filteredTokens.map((token) => {
                const balance = balances[token.address];
                const isSelected = selectedToken?.address === token.address;

                return (
                  <button
                    key={token.address}
                    onClick={() => handleSelectToken(token)}
                    disabled={isSelected}
                    className={`w-full p-3 rounded-lg flex items-center justify-between hover:bg-white/10 transition-colors ${
                      isSelected ? "bg-white/5 cursor-not-allowed" : ""
                    }`}
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
                        <div className="font-semibold text-white">
                          {token.symbol || "UNKNOWN"}
                        </div>
                        <div className="text-xs text-gray-400">
                          {token.name || "Unknown Token"}
                        </div>
                      </div>
                    </div>
                    
                    {publicKey && balance && (
                      <div className="text-right">
                        <div className="text-sm text-white font-medium">
                          {balance.uiAmount?.toFixed(4) || "0"}
                        </div>
                        <div className="text-xs text-gray-400">Balance</div>
                      </div>
                    )}
                  </button>
                );
              })
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
