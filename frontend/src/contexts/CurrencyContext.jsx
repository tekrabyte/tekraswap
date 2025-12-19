import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const CurrencyContext = createContext();

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export function CurrencyProvider({ children }) {
  const [currency, setCurrency] = useState('USD'); // 'USD' atau 'IDR'
  const [exchangeRate, setExchangeRate] = useState(15800); // Default rate
  const [rateInfo, setRateInfo] = useState(null);
  const [loading, setLoading] = useState(false);

  // Fetch exchange rate saat component mount dan setiap 1 jam
  useEffect(() => {
    fetchExchangeRate();
    
    // Auto-refresh setiap 1 jam
    const interval = setInterval(() => {
      fetchExchangeRate();
    }, 3600000); // 1 hour
    
    return () => clearInterval(interval);
  }, []);

  const fetchExchangeRate = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/exchange-rate`);
      const data = response.data;
      
      setExchangeRate(data.rate);
      setRateInfo({
        rate: data.rate,
        lastUpdate: data.last_update,
        source: data.source,
      });
      
      console.log(`Exchange rate updated: 1 USD = ${data.rate} IDR (${data.source})`);
    } catch (error) {
      console.error('Failed to fetch exchange rate:', error);
      // Keep default rate jika gagal
    } finally {
      setLoading(false);
    }
  };

  const toggleCurrency = () => {
    setCurrency(prev => prev === 'USD' ? 'IDR' : 'USD');
  };

  const convertUsdToIdr = (usdAmount) => {
    if (!usdAmount) return 0;
    return usdAmount * exchangeRate;
  };

  const value = {
    currency,
    setCurrency,
    toggleCurrency,
    exchangeRate,
    rateInfo,
    loading,
    convertUsdToIdr,
    refreshRate: fetchExchangeRate,
  };

  return (
    <CurrencyContext.Provider value={value}>
      {children}
    </CurrencyContext.Provider>
  );
}

export function useCurrency() {
  const context = useContext(CurrencyContext);
  if (!context) {
    throw new Error('useCurrency must be used within CurrencyProvider');
  }
  return context;
}
