/**
 * Currency formatting utilities with multi-currency support
 * Integrates with CurrencyContext for dynamic currency display
 */

import { formatPrice as formatUSDPrice, formatIDR as formatIDRPrice, formatLargeNumber } from './formatNumber';

/**
 * Format harga sesuai currency yang dipilih
 * 
 * @param {number} usdAmount - Amount dalam USD
 * @param {string} currency - 'USD' or 'IDR'
 * @param {number} exchangeRate - USD to IDR rate
 * @param {object} options - Formatting options
 * @returns {string} Formatted price string
 */
export function formatCurrency(usdAmount, currency = 'USD', exchangeRate = 15800, options = {}) {
  const {
    useShortFormat = false,
    showSymbol = true,
  } = options;

  if (currency === 'IDR') {
    const idrAmount = usdAmount * exchangeRate;
    return formatIDRPrice(idrAmount, { showSymbol, useShortFormat });
  }
  
  return formatUSDPrice(usdAmount, { showDollarSign: showSymbol });
}

/**
 * Format large numbers (volume, market cap) dengan currency
 * 
 * @param {number} usdAmount - Amount dalam USD
 * @param {string} currency - 'USD' or 'IDR'
 * @param {number} exchangeRate - USD to IDR rate
 * @returns {string} Formatted string dengan K/M/B suffix
 */
export function formatLargeCurrency(usdAmount, currency = 'USD', exchangeRate = 15800) {
  if (currency === 'IDR') {
    const idrAmount = usdAmount * exchangeRate;
    
    let formatted;
    let suffix = '';
    
    // Format untuk IDR: Miliar, Juta, Ribu
    if (idrAmount >= 1e12) {
      formatted = (idrAmount / 1e12).toFixed(2);
      suffix = 'T'; // Triliun
    } else if (idrAmount >= 1e9) {
      formatted = (idrAmount / 1e9).toFixed(2);
      suffix = 'M'; // Miliar
    } else if (idrAmount >= 1e6) {
      formatted = (idrAmount / 1e6).toFixed(2);
      suffix = 'Jt'; // Juta
    } else if (idrAmount >= 1e3) {
      formatted = (idrAmount / 1e3).toFixed(1);
      suffix = 'K'; // Ribu
    } else {
      formatted = Math.round(idrAmount).toString();
    }
    
    formatted = parseFloat(formatted).toString();
    return `Rp ${formatted}${suffix}`;
  }
  
  return formatLargeNumber(usdAmount, { showDollarSign: true, decimals: 2 });
}

/**
 * Format token balance (currency-independent)
 */
export function formatTokenBalance(balance, decimals = 9) {
  if (balance === null || balance === undefined || isNaN(balance)) {
    return "0";
  }

  const numBalance = Number(balance);

  if (numBalance === 0) {
    return "0";
  }

  if (numBalance >= 1000) {
    return numBalance.toLocaleString('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });
  }

  if (numBalance >= 1) {
    return numBalance.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: Math.min(decimals > 6 ? 4 : 2, 6),
    });
  }

  return numBalance.toFixed(Math.min(decimals > 6 ? 6 : 4, 8));
}

/**
 * Get currency symbol
 */
export function getCurrencySymbol(currency) {
  return currency === 'USD' ? '$' : 'Rp';
}
