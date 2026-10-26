# IndiLevels: Stock Support and Resistance Level Calculator 📈

A beginner-friendly web application for calculating key **Support and Resistance levels** for Indian equities on the **National Stock Exchange (NSE)** and **Bombay Stock Exchange (BSE)**.

Built with **Python, Flask, HTML, CSS, JavaScript, and Bootstrap 5**, IndiLevels strictly uses **100% traditional technical analysis and pure mathematical formulas**. There is **no Artificial Intelligence (AI), Machine Learning (ML), or Deep Learning** used anywhere in this project.

---

## 🌟 Key Features

### 1. Indian Stock Search & Market Normalization
- Supports Indian tickers across **NSE (`.NS`)** and **BSE (`.BO`)**, such as `RELIANCE.NS`, `TCS.NS`, `SBIN.NS`, `HDFCBANK.NS`, and `INFY.NS`.
- Automatically normalizes plain symbols (e.g. typing `RELIANCE` defaults to `RELIANCE.NS` or selected exchange).
- Quick-pick shortcut pills for top Nifty 50 and Sensex heavyweights.
- Flexible historical period selection: **1 Month, 3 Months, 6 Months, 1 Year, 2 Years**.
- User-friendly error messages if a symbol is invalid or delisted.

### 2. Traditional Mathematical Support & Resistance Calculations
- **Classical Floor Pivot Points**:
  - Computed using previous completed trading day's Open, High, Low, and Close:
    $$\text{Pivot Point (PP)} = \frac{\text{High} + \text{Low} + \text{Close}}{3}$$
    $$\text{Resistance 1 (R1)} = (2 \times \text{PP}) - \text{Low}$$
    $$\text{Support 1 (S1)} = (2 \times \text{PP}) - \text{High}$$
    $$\text{Resistance 2 (R2)} = \text{PP} + (\text{High} - \text{Low})$$
    $$\text{Support 2 (S2)} = \text{PP} - (\text{High} - \text{Low})$$
    $$\text{Resistance 3 (R3)} = \text{High} + 2 \times (\text{PP} - \text{Low})$$
    $$\text{Support 3 (S3)} = \text{Low} - 2 \times (\text{High} - \text{PP})$$
  - Also includes Fibonacci Pivot Points as reference.

- **Historical Swing Highs & Lows (Price Action Fractals)**:
  - Detects local price peaks (where a bar's High exceeds $N$ preceding and following bars).
  - Detects local price troughs (where a bar's Low is lower than $N$ preceding and following bars).
  - **Dynamic Clustering Algorithm**: Groups nearby swing points within a configurable tolerance percentage (default `1.25%`) into high-conviction support/resistance zones with touch counts.

- **Moving Averages (Reference Indicators)**:
  - Calculates **20-day SMA** (short-term trend reference) and **50-day SMA** (medium-term trend reference).
  - Calculates exact percentage distance and determines bullish/bearish alignment relative to the current price.

### 3. Interactive Chart & Dashboard
- Built with **Chart.js 4.4** and the official annotation plugin.
- Seamless toggles between **Clean Area/Line Chart** and **High-Low Range Band Chart**.
- Dynamic horizontal overlay lines for **Pivot Point (PP)**, **Support 1 & 2**, **Resistance 1 & 2**, and **Moving Averages**.
- Integrated trading volume bar subchart.
- Tooltips displaying exact Open, High, Low, Close, Volume, and Level prices in Indian Rupees (₹).
- Unified levels ranking table sorting all computed levels from highest resistance to lowest support.
- Actionable beginner summary explaining current price position relative to immediate floor and ceiling.

### 4. Watchlist & Calculation History (SQLite Storage)
- **Watchlist**: Save favourite stocks with customizable target support, target resistance, and personal trading strategy notes.
- **Calculation History**: Automatically logs past calculations with timestamps, symbol, period, current price, and key levels. One-click "Re-Run" button to re-calculate instantly with live market data.
- **Data Export**: One-click download of calculation levels as a clean CSV file.
- **Print Friendly**: Built-in styling to print or save a clean one-page PDF technical report.

### 5. Beginner Technical Analysis Guide
- Built-in educational guide explaining:
  - The "Floor" and "Ceiling" concept.
  - Why Support & Resistance are **zones**, not exact pinpoint numbers.
  - Step-by-step mathematical derivation of Floor Pivot Points.
  - The Polarity Principle (old resistance becomes new support).
  - Essential risk management rules (position sizing, stop-loss placement, volume confirmation).

---

## 🏗️ Architecture & Project Structure

```
stock_support_resistance/
├── app.py                     # Flask application & REST API routes
├── calculations.py            # 100% Traditional TA & mathematical calculations
├── data_fetcher.py            # yfinance retrieval, error handling, ticker normalization
├── database.py                # SQLite database management (Watchlist & History)
│
├── static/
│   ├── css/
│   │   └── style.css          # Fintech dark/light styling, glassmorphism, responsive UI
│   └── js/
│       ├── app.js             # Main frontend controller, AJAX calls, UI rendering
│       └── charts.js          # Chart.js integration, level annotations, and toggles
│
├── templates/
│   ├── base.html              # Base layout with navbar, theme toggle, and footer
│   ├── index.html             # Main dashboard, search, KPIs, chart, and levels
│   ├── watchlist.html         # User watchlist management table
│   ├── history.html           # Calculation history table with re-run actions
│   └── guide.html             # Beginner educational guide on Support & Resistance
│
├── tests/
│   ├── test_calculations.py   # Unit tests for mathematical formulas and clustering
│   └── test_app.py            # Integration tests for Flask endpoints and workflows
│
├── requirements.txt           # Python package dependencies
└── README.md                  # Project documentation
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.9, 3.10, or higher
- Internet connection (to fetch daily market data via Yahoo Finance)

### Installation

1. Open a terminal / PowerShell in the project directory:
   ```bash
   cd stock_support_resistance
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the Flask application:
   ```bash
   python app.py
   ```

4. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

---

## 🧪 Running Tests

IndiLevels includes a comprehensive test suite covering mathematical accuracy, edge cases, database transactions, and API endpoints:

```bash
# Run all unit and integration tests
python -m unittest discover tests

# Or run individual test suites:
python -m unittest tests/test_calculations.py
python -m unittest tests/test_app.py
```

---

## ⚖️ Disclaimer

This application is strictly for **educational and technical analysis purposes**. It does not constitute financial, investment, or trading advice. Trading in the Indian stock market involves substantial risk of loss. Always perform your own due diligence or consult a SEBI-registered investment advisor before making financial decisions.
