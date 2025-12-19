import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CurrencyContext = createContext();

export const useCurrency = () => {
  const context = useContext(CurrencyContext);
  if (!context) {
    throw new Error('useCurrency must be used within CurrencyProvider');
  }
  return context;
};

export const CurrencyProvider = ({ children }) => {
  const [currency, setCurrency] = useState('USD'); // 'USD' or 'IDR'
  const [exchangeRate, setExchangeRate] = useState(15800); // Fallback rate
  const [rateLoading, setRateLoading] = useState(false);
  const [rateSource, setRateSource] = useState('fallback');
  const [lastUpdate, setLastUpdate] = useState(null);

  // Fetch exchange rate on mount and every hour
  useEffect(() => {
    fetchExchangeRate();
    
    // Auto-refresh every hour
    const interval = setInterval(() => {
      fetchExchangeRate(true); // Silent refresh
    }, 3600000); // 1 hour
    
    return () => clearInterval(interval);
  }, []);

  const fetchExchangeRate = async (silent = false) => {
    if (!silent) setRateLoading(true);
    
    try {
      const response = await axios.get(`${API}/exchange-rate`);
      const data = response.data;
      
      setExchangeRate(data.rate);
      setRateSource(data.source);
      setLastUpdate(new Date(data.last_update));
    } catch (error) {
      console.error('Error fetching exchange rate:', error);
      // Keep fallback rate
    } finally {
      if (!silent) setRateLoading(false);
    }
  };

  const toggleCurrency = () => {
    setCurrency(prev => prev === 'USD' ? 'IDR' : 'USD');
  };

  const convertToCurrentCurrency = (usdAmount) => {
    if (!usdAmount) return 0;
    return currency === 'USD' ? usdAmount : usdAmount * exchangeRate;
  };

  const value = {
    currency,
    setCurrency,
    toggleCurrency,
    exchangeRate,
    rateLoading,
    rateSource,
    lastUpdate,
    fetchExchangeRate,
    convertToCurrentCurrency,
  };

  return (
    <CurrencyContext.Provider value={value}>
      {children}
    </CurrencyContext.Provider>
  );
};
