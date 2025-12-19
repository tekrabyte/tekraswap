/**
 * Utility functions untuk format angka dengan user-friendly
 * Khususnya untuk cryptocurrency prices yang bisa sangat kecil
 * Dengan dukungan multi-currency (USD, IDR)
 */

/**
 * Format harga cryptocurrency dengan cara yang lebih readable
 * Menghindari scientific notation (e-10) yang membingungkan user
 * 
 * @param {number} price - Harga dalam USD
 * @param {object} options - Opsi formatting
 * @returns {string} Formatted price string
 * 
 * Contoh:
 * - 0.00000057 → "$0.00000057" (bukan "$5.7e-7")
 * - 0.0023 → "$0.0023"
 * - 1.234 → "$1.23"
 * - 1234.56 → "$1,234.56"
 */
export function formatPrice(price, options = {}) {
  const {
    showDollarSign = true,
    minDecimals = 2,
    maxDecimals = 8,
  } = options;

  // Handle invalid inputs
  if (price === null || price === undefined || isNaN(price)) {
    return showDollarSign ? "$0.00" : "0.00";
  }

  const numPrice = Number(price);

  // Handle zero
  if (numPrice === 0) {
    return showDollarSign ? "$0.00" : "0.00";
  }

  let formatted;

  // Untuk harga sangat besar (> $1M)
  if (numPrice >= 1000000) {
    formatted = numPrice.toLocaleString('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });
  }
  // Untuk harga normal (>= $1)
  else if (numPrice >= 1) {
    formatted = numPrice.toLocaleString('en-US', {
      minimumFractionDigits: minDecimals,
      maximumFractionDigits: 2,
    });
  }
  // Untuk harga kecil ($0.01 - $1)
  else if (numPrice >= 0.01) {
    formatted = numPrice.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 4,
    });
  }
  // Untuk harga sangat kecil (< $0.01)
  // INI YANG PALING PENTING - hindari scientific notation!
  else {
    // Hitung berapa desimal yang dibutuhkan
    // Cari digit pertama yang bukan 0
    const str = numPrice.toString();
    
    // Jika sudah dalam bentuk scientific notation (e-10), convert dulu
    if (str.includes('e')) {
      // Parse scientific notation secara manual
      const [mantissa, exponent] = str.split('e');
      const exp = parseInt(exponent);
      const decimalsNeeded = Math.abs(exp) + (mantissa.replace('.', '').length - 1);
      formatted = numPrice.toFixed(Math.min(decimalsNeeded, maxDecimals));
    } else {
      // Format dengan decimals yang cukup untuk show nilai
      // Contoh: 0.00000577 butuh 8 decimals
      const match = str.match(/0\.0*[1-9]/);
      if (match) {
        const zerosAfterDecimal = match[0].length - 2; // -2 untuk "0."
        const decimalsNeeded = zerosAfterDecimal + 2; // +2 untuk show 2 digit signifikan
        formatted = numPrice.toFixed(Math.min(decimalsNeeded, maxDecimals));
      } else {
        formatted = numPrice.toFixed(maxDecimals);
      }
    }
    
    // Remove trailing zeros tapi keep minimal 2 decimals
    formatted = parseFloat(formatted).toFixed(maxDecimals);
    // Remove unnecessary trailing zeros
    formatted = formatted.replace(/\.?0+$/, '');
    // Make sure we have at least some decimals
    if (!formatted.includes('.')) {
      formatted += '.00';
    }
  }

  return showDollarSign ? `$${formatted}` : formatted;
}

/**
 * Format harga dalam IDR (Indonesian Rupiah)
 * 
 * @param {number} idrAmount - Jumlah dalam IDR
 * @param {object} options - Opsi formatting
 * @returns {string} Formatted IDR string
 * 
 * Contoh:
 * - 15000 → "Rp 15,000"
 * - 1500000 → "Rp 1,500,000"
 * - 0.5 → "Rp 1" (rounded)
 */
export function formatIDR(idrAmount, options = {}) {
  const {
    showSymbol = true,
    useShortFormat = false, // Jika true, pakai format 15K, 1.5M, dll
  } = options;

  // Handle invalid inputs
  if (idrAmount === null || idrAmount === undefined || isNaN(idrAmount)) {
    return showSymbol ? "Rp 0" : "0";
  }

  const numAmount = Number(idrAmount);

  // Handle zero
  if (numAmount === 0) {
    return showSymbol ? "Rp 0" : "0";
  }

  let formatted;

  // Short format dengan K/M/B suffix
  if (useShortFormat) {
    if (numAmount >= 1e9) {
      formatted = (numAmount / 1e9).toFixed(2) + 'M'; // Miliar
    } else if (numAmount >= 1e6) {
      formatted = (numAmount / 1e6).toFixed(2) + 'Jt'; // Juta
    } else if (numAmount >= 1e3) {
      formatted = (numAmount / 1e3).toFixed(1) + 'K'; // Ribu
    } else {
      formatted = Math.round(numAmount).toString();
    }
  } else {
    // Full format dengan comma separator
    // IDR biasanya tidak pakai desimal, round ke integer
    formatted = Math.round(numAmount).toLocaleString('id-ID');
  }

  return showSymbol ? `Rp ${formatted}` : formatted;
}

/**
 * Format harga dengan currency support (USD atau IDR)
 * 
 * @param {number} usdPrice - Harga dalam USD
 * @param {string} currency - 'USD' atau 'IDR'
 * @param {number} exchangeRate - Rate USD to IDR (optional, default 15800)
 * @returns {string} Formatted price in selected currency
 */
export function formatPriceWithCurrency(usdPrice, currency = 'USD', exchangeRate = 15800) {
  if (currency === 'IDR') {
    const idrPrice = usdPrice * exchangeRate;
    return formatIDR(idrPrice, { useShortFormat: idrPrice >= 1000 });
  }
  return formatPrice(usdPrice);
}

/**
 * Format angka dengan K, M, B suffix untuk volume dan market cap
 * 
 * @param {number} num - Angka yang akan diformat
 * @param {object} options - Opsi formatting
 * @returns {string} Formatted string
 * 
 * Contoh:
 * - 1234 → "1.23K"
 * - 1234567 → "1.23M"
 * - 1234567890 → "1.23B"
 */
export function formatLargeNumber(num, options = {}) {
  const {
    showDollarSign = true,
    decimals = 2,
  } = options;

  // Handle invalid inputs
  if (num === null || num === undefined || isNaN(num)) {
    return showDollarSign ? "$0" : "0";
  }

  const numValue = Number(num);

  // Handle zero or very small numbers
  if (numValue === 0 || numValue < 0.01) {
    return showDollarSign ? "$0.00" : "0.00";
  }

  let formatted;
  let suffix = '';

  // Billion
  if (numValue >= 1e9) {
    formatted = (numValue / 1e9).toFixed(decimals);
    suffix = 'B';
  }
  // Million
  else if (numValue >= 1e6) {
    formatted = (numValue / 1e6).toFixed(decimals);
    suffix = 'M';
  }
  // Thousand
  else if (numValue >= 1e3) {
    formatted = (numValue / 1e3).toFixed(decimals);
    suffix = 'K';
  }
  // Less than 1000
  else {
    formatted = numValue.toFixed(decimals);
  }

  // Remove trailing zeros
  formatted = parseFloat(formatted).toString();

  const dollarSign = showDollarSign ? '$' : '';
  return `${dollarSign}${formatted}${suffix}`;
}

/**
 * Format token balance dengan decimals yang sesuai
 * 
 * @param {number} balance - Token balance
 * @param {number} decimals - Token decimals (e.g., 9 for SOL, 6 for USDC)
 * @returns {string} Formatted balance
 */
export function formatTokenBalance(balance, decimals = 9) {
  if (balance === null || balance === undefined || isNaN(balance)) {
    return "0";
  }

  const numBalance = Number(balance);

  if (numBalance === 0) {
    return "0";
  }

  // Untuk balance besar, show dengan comma separator
  if (numBalance >= 1000) {
    return numBalance.toLocaleString('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });
  }

  // Untuk balance normal, show dengan decimals yang sesuai
  if (numBalance >= 1) {
    return numBalance.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: Math.min(decimals > 6 ? 4 : 2, 6),
    });
  }

  // Untuk balance kecil
  return numBalance.toFixed(Math.min(decimals > 6 ? 6 : 4, 8));
}

/**
 * Format percentage dengan proper sign
 * 
 * @param {number} percent - Percentage value
 * @returns {string} Formatted percentage with color indicator
 */
export function formatPercentage(percent) {
  if (percent === null || percent === undefined || isNaN(percent)) {
    return "0.00%";
  }

  const numPercent = Number(percent);
  const sign = numPercent >= 0 ? '+' : '';
  
  return `${sign}${numPercent.toFixed(2)}%`;
}

/**
 * Format USD value dengan proper decimals
 * 
 * @param {number} value - USD value
 * @returns {string} Formatted USD value
 */
export function formatUSD(value) {
  if (value === null || value === undefined || isNaN(value)) {
    return "$0.00";
  }

  const numValue = Number(value);

  if (numValue === 0) {
    return "$0.00";
  }

  // Use formatLargeNumber for large values
  if (numValue >= 1000) {
    return formatLargeNumber(numValue, { showDollarSign: true, decimals: 2 });
  }

  // For normal values
  return numValue.toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}
