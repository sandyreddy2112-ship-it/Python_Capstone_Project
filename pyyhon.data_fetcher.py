"""
Stock Data Fetcher for Indian Stock Market (NSE / BSE) using yfinance.
Handles symbol normalization, fetching historical OHLC data, and market metadata.
"""

from typing import Dict, Any, Optional, Tuple
import datetime
import pandas as pd
import yfinance as yf


# Popular Nifty 50 and Indian Market Tickers for quick suggestions
POPULAR_INDIAN_STOCKS = [
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries Ltd", "exchange": "NSE", "sector": "Energy & Petrochemicals"},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "exchange": "NSE", "sector": "Information Technology"},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank Ltd", "exchange": "NSE", "sector": "Banking & Financials"},
    {"symbol": "INFY.NS", "name": "Infosys Ltd", "exchange": "NSE", "sector": "Information Technology"},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank Ltd", "exchange": "NSE", "sector": "Banking & Financials"},
    {"symbol": "SBIN.NS", "name": "State Bank of India", "exchange": "NSE", "sector": "Banking & Financials"},
    {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel Ltd", "exchange": "NSE", "sector": "Telecommunications"},
    {"symbol": "ITC.NS", "name": "ITC Ltd", "exchange": "NSE", "sector": "FMCG"},
    {"symbol": "LT.NS", "name": "Larsen & Toubro Ltd", "exchange": "NSE", "sector": "Engineering & Construction"},
    {"symbol": "TATAMOTORS.NS", "name": "Tata Motors Ltd", "exchange": "NSE", "sector": "Automobiles"},
    {"symbol": "WIPRO.NS", "name": "Wipro Ltd", "exchange": "NSE", "sector": "Information Technology"},
    {"symbol": "MARUTI.NS", "name": "Maruti Suzuki India", "exchange": "NSE", "sector": "Automobiles"},
    {"symbol": "^NSEI", "name": "Nifty 50 Index", "exchange": "NSE", "sector": "Index Benchmark"},
    {"symbol": "^BSESN", "name": "BSE Sensex 30 Index", "exchange": "BSE", "sector": "Index Benchmark"}
]


def normalize_symbol(raw_symbol: str, default_exchange: str = "NSE") -> str:
    """
    Cleans and standardizes Indian stock symbols.
    If no suffix is provided (like .NS or .BO), appends the appropriate exchange suffix.
    """
    if not raw_symbol:
        return ""
    
    symbol = raw_symbol.strip().upper()

    # Index aliases
    if symbol in ("NIFTY", "NIFTY50", "NIFTY 50"):
        return "^NSEI"
    if symbol in ("BANKNIFTY", "NIFTYBANK"):
        return "^NSEBANK"
    if symbol in ("SENSEX", "BSESENSEX"):
        return "^BSESN"

    # If it already has an exchange suffix or index prefix, preserve it
    if symbol.startswith("^") or symbol.endswith(".NS") or symbol.endswith(".BO"):
        return symbol

    # Otherwise append exchange suffix
    if default_exchange.upper() == "BSE":
        return f"{symbol}.BO"
    return f"{symbol}.NS"


def fetch_stock_data(symbol: str, period: str = "6mo", exchange: str = "NSE") -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Fetches historical OHLC data and profile information for an Indian stock.
    Returns: (data_dict, error_message)
    """
    normalized_sym = normalize_symbol(symbol, exchange)
    if not normalized_sym:
        return None, "Please provide a valid stock symbol."

    valid_periods = ["1mo", "3mo", "6mo", "1y", "2y", "5y"]
    if period not in valid_periods:
        period = "6mo"

    try:
        ticker = yf.Ticker(normalized_sym)
        # Fetch historical data (daily bars)
        hist = ticker.history(period=period, interval="1d")

        if hist.empty or len(hist) < 3:
            # Try alternate exchange if failed and no explicit suffix was typed
            alt_sym = None
            if normalized_sym.endswith(".NS"):
                alt_sym = normalized_sym.replace(".NS", ".BO")
            elif normalized_sym.endswith(".BO"):
                alt_sym = normalized_sym.replace(".BO", ".NS")

            if alt_sym:
                ticker_alt = yf.Ticker(alt_sym)
                hist_alt = ticker_alt.history(period=period, interval="1d")
                if not hist_alt.empty and len(hist_alt) >= 3:
                    ticker = ticker_alt
                    hist = hist_alt
                    normalized_sym = alt_sym

            if hist.empty or len(hist) < 3:
                return None, f"Stock symbol '{normalized_sym}' not found or has no historical price data. Please check if the ticker symbol is correct for NSE (.NS) or BSE (.BO)."

        # Fetch metadata safely
        info: Dict[str, Any] = {}
        try:
            info = ticker.info or {}
        except Exception:
            info = {}

        company_name = info.get("longName") or info.get("shortName") or normalized_sym
        sector = info.get("sector") or info.get("industry") or "Indian Equity"
        currency = info.get("currency") or "INR"

        # Format historical chart data
        # We supply dates, timestamps (ms), open, high, low, close, volume
        chart_data = []
        for index_val, row in hist.iterrows():
            if hasattr(index_val, "strftime"):
                date_str = index_val.strftime("%Y-%m-%d")
                ts_ms = int(index_val.timestamp() * 1000)
            else:
                date_str = str(index_val)
                ts_ms = 0

            chart_data.append({
                "date": date_str,
                "timestamp": ts_ms,
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row.get("Volume", 0))
            })

        # Latest session data
        latest_row = hist.iloc[-1]
        latest_date = hist.index[-1]
        latest_date_str = latest_date.strftime("%d %b %Y") if hasattr(latest_date, "strftime") else str(latest_date)

        current_close = round(float(latest_row["Close"]), 2)
        current_open = round(float(latest_row["Open"]), 2)
        current_high = round(float(latest_row["High"]), 2)
        current_low = round(float(latest_row["Low"]), 2)
        current_volume = int(latest_row.get("Volume", 0))

        # Previous session for price change calculation & standard pivot calculation
        prev_row = hist.iloc[-2] if len(hist) >= 2 else latest_row
        prev_close = round(float(prev_row["Close"]), 2)
        prev_high = round(float(prev_row["High"]), 2)
        prev_low = round(float(prev_row["Low"]), 2)

        change_points = round(current_close - prev_close, 2)
        change_pct = round(((current_close - prev_close) / prev_close) * 100.0, 2) if prev_close > 0 else 0.0

        # 52-week Range
        fifty_two_high = info.get("fiftyTwoWeekHigh")
        fifty_two_low = info.get("fiftyTwoWeekLow")
        if not fifty_two_high:
            fifty_two_high = round(float(hist["High"].max()), 2)
        else:
            fifty_two_high = round(float(fifty_two_high), 2)

        if not fifty_two_low:
            fifty_two_low = round(float(hist["Low"].min()), 2)
        else:
            fifty_two_low = round(float(fifty_two_low), 2)

        return {
            "symbol": normalized_sym,
            "company_name": company_name,
            "exchange": "BSE" if normalized_sym.endswith(".BO") else "NSE",
            "sector": sector,
            "currency": currency,
            "period": period,
            "latest": {
                "date": latest_date_str,
                "close": current_close,
                "open": current_open,
                "high": current_high,
                "low": current_low,
                "volume": current_volume,
                "prev_close": prev_close,
                "change": change_points,
                "change_percent": change_pct,
                "is_positive": change_points >= 0
            },
            "previous_session": {
                "high": prev_high,
                "low": prev_low,
                "close": prev_close
            },
            "stats": {
                "fifty_two_week_high": fifty_two_high,
                "fifty_two_week_low": fifty_two_low,
                "day_range": f"₹{current_low:,.2f} - ₹{current_high:,.2f}",
                "fifty_two_range": f"₹{fifty_two_low:,.2f} - ₹{fifty_two_high:,.2f}",
                "total_bars": len(hist)
            },
            "dataframe": hist,
            "chart_data": chart_data
        }, None

    except Exception as e:
        error_msg = str(e)
        if "HTTPError" in error_msg or "404" in error_msg:
            return None, f"Ticker '{normalized_sym}' not found on Yahoo Finance. Make sure the symbol is valid on NSE or BSE."
        return None, f"Error fetching stock data for '{normalized_sym}': {error_msg}"
