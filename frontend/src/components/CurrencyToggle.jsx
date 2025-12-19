import React from 'react';
import { useCurrency } from '@/contexts/CurrencyContext';
import { Button } from '@/components/ui/button';
import { DollarSign, RefreshCw } from 'lucide-react';
import { motion } from 'framer-motion';

export function CurrencyToggle({ compact = false, showRefresh = false }) {
  const { currency, toggleCurrency, exchangeRate, rateSource, rateLoading, fetchExchangeRate } = useCurrency();

  if (compact) {
    return (
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleCurrency}
          className="text-white/80 hover:text-white hover:bg-white/10 font-medium"
        >
          <DollarSign className="h-4 w-4 mr-1" />
          {currency}
        </Button>
        {showRefresh && (
          <Button
            variant="ghost"
            size="icon"
            onClick={() => fetchExchangeRate()}
            disabled={rateLoading}
            className="h-8 w-8 text-white/60 hover:text-white"
          >
            <RefreshCw className={`h-3 w-3 ${rateLoading ? 'animate-spin' : ''}`} />
          </Button>
        )}
      </div>
    );
  }

  return (
    <motion.div 
      className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-3"
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <DollarSign className="h-5 w-5 text-white/60" />
          <div>
            <div className="text-sm text-white/50">Currency</div>
            <div className="text-lg font-bold text-white">{currency}</div>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            onClick={toggleCurrency}
            className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-medium"
            size="sm"
          >
            Switch to {currency === 'USD' ? 'IDR' : 'USD'}
          </Button>
          
          {showRefresh && (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => fetchExchangeRate()}
              disabled={rateLoading}
              className="text-white/60 hover:text-white"
            >
              <RefreshCw className={`h-4 w-4 ${rateLoading ? 'animate-spin' : ''}`} />
            </Button>
          )}
        </div>
      </div>
      
      {currency === 'IDR' && (
        <div className="mt-2 pt-2 border-t border-white/5">
          <div className="text-xs text-white/40">
            Rate: 1 USD = Rp {exchangeRate.toLocaleString('id-ID')}
          </div>
          <div className="text-xs text-white/30">
            Source: {rateSource}
          </div>
        </div>
      )}
    </motion.div>
  );
}
