"""
Flask Application for Stock Support and Resistance Level Calculator.
Indian Stock Market (NSE / BSE).
"""

import io
import csv
from flask import Flask, render_template, request, jsonify, Response
import database
import calculations
import data_fetcher

app = Flask(__name__)

# Initialize database tables on startup
database.init_db()


@app.route("/")
def index():
    """Main dashboard page."""
    return render_template("index.html", popular_stocks=data_fetcher.POPULAR_INDIAN_STOCKS)


@app.route("/watchlist")
def watchlist_page():
    """Watchlist page."""
    items = database.get_watchlist()
    return render_template("watchlist.html", watchlist=items)


@app.route("/history")
def history_page():
    """Calculation history page."""
    records = database.get_calculation_history(limit=100)
    return render_template("history.html", history=records)


@app.route("/guide")
def guide_page():
    """Beginner technical analysis education guide."""
    return render_template("guide.html")


# ==================== API ENDPOINTS ====================

@app.route("/api/popular-stocks", methods=["GET"])
def get_popular_stocks():
    """Returns popular Indian stocks for quick selection."""
    return jsonify({"success": True, "stocks": data_fetcher.POPULAR_INDIAN_STOCKS})


@app.route("/api/analyze", methods=["POST"])
def analyze_stock():
    """
    Analyzes an Indian stock:
    - Fetches historical OHLC prices
    - Calculates Pivot Points (Floor & Fibonacci)
    - Calculates 20-day, 50-day, 200-day Simple Moving Averages
    - Detects historical swing highs & lows with clustering
    - Computes distance to all levels
    - Automatically logs calculation into SQLite history
    """
    try:
        data = request.get_json() or {}
        symbol = data.get("symbol", "").strip()
        period = data.get("period", "6mo").strip()
        exchange = data.get("exchange", "NSE").strip()
        swing_window = int(data.get("swing_window", 3))
        tolerance_pct = float(data.get("tolerance_pct", 1.25))

        if not symbol:
            return jsonify({"success": False, "error": "Please enter an Indian stock symbol (e.g. RELIANCE, TCS.NS)."}), 400

        # Fetch market data
        stock_data, error = data_fetcher.fetch_stock_data(symbol, period=period, exchange=exchange)
        if error or not stock_data:
            return jsonify({"success": False, "error": error or "Failed to fetch stock data."}), 404

        df = stock_data["dataframe"]
        current_close = stock_data["latest"]["close"]
        prev_session = stock_data["previous_session"]

        # 1. Pivot Points (from previous completed trading day)
        pivot_data = calculations.calculate_pivot_points(
            high=prev_session["high"],
            low=prev_session["low"],
            close=prev_session["close"]
        )

        # 2. Moving Averages
        ma_data = calculations.calculate_moving_averages(df)

        # 3. Swing Highs & Lows (Price Action)
        swings = calculations.find_swing_highs_and_lows(df, window=swing_window)
        clustered_highs = calculations.cluster_price_levels(swings["highs"], tolerance_pct=tolerance_pct)
        clustered_lows = calculations.cluster_price_levels(swings["lows"], tolerance_pct=tolerance_pct)

        # 4. Comprehensive Analysis (Supports, Resistances, Nearest Levels, Distances)
        analysis = calculations.analyze_all_levels(
            current_price=current_close,
            pivot_data=pivot_data,
            moving_averages=ma_data,
            swing_highs_clustered=clustered_highs,
            swing_lows_clustered=clustered_lows
        )

        # Check watchlist status
        in_watchlist = database.is_in_watchlist(stock_data["symbol"])

        # Log into SQLite calculation history
        database.log_calculation(
            symbol=stock_data["symbol"],
            name=stock_data["company_name"],
            period=period,
            current_price=current_close,
            pivot=pivot_data.get("pivot"),
            s1=pivot_data.get("s1"),
            s2=pivot_data.get("s2"),
            r1=pivot_data.get("r1"),
            r2=pivot_data.get("r2"),
            sma20=ma_data.get("sma20"),
            sma50=ma_data.get("sma50")
        )

        # Build clean JSON response
        response_payload = {
            "success": True,
            "symbol": stock_data["symbol"],
            "company_name": stock_data["company_name"],
            "exchange": stock_data["exchange"],
            "sector": stock_data["sector"],
            "currency": stock_data["currency"],
            "period": stock_data["period"],
            "latest": stock_data["latest"],
            "stats": stock_data["stats"],
            "previous_session": prev_session,
            "pivot_points": pivot_data,
            "moving_averages": {
                "sma20": ma_data["sma20"],
                "sma50": ma_data["sma50"],
                "sma200": ma_data["sma200"]
            },
            "swing_levels": {
                "resistance_clusters": clustered_highs[:5],
                "support_clusters": clustered_lows[:5]
            },
            "analysis": {
                "nearest_support": analysis["nearest_support"],
                "nearest_resistance": analysis["nearest_resistance"],
                "supports": analysis["supports"][:6],
                "resistances": analysis["resistances"][:6],
                "all_levels": analysis["all_levels"],
                "pivot_point": analysis["pivot_point"],
                "pivot_distance": analysis["pivot_distance"]
            },
            "chart": {
                "ohlc": stock_data["chart_data"],
                "sma20_series": ma_data["series"]["sma20"],
                "sma50_series": ma_data["series"]["sma50"],
                "sma200_series": ma_data["series"]["sma200"]
            },
            "in_watchlist": in_watchlist
        }

        return jsonify(response_payload)

    except Exception as e:
        return jsonify({"success": False, "error": f"Internal calculation error: {str(e)}"}), 500


@app.route("/api/watchlist", methods=["GET"])
def get_watchlist_api():
    """Fetches user watchlist."""
    items = database.get_watchlist()
    return jsonify({"success": True, "watchlist": items})


@app.route("/api/watchlist/add", methods=["POST"])
def add_to_watchlist_api():
    """Adds or updates a stock in the watchlist."""
    data = request.get_json() or {}
    symbol = data.get("symbol", "").strip()
    name = data.get("name", symbol).strip()
    exchange = data.get("exchange", "NSE").strip()
    last_price = data.get("last_price")
    target_support = data.get("target_support")
    target_resistance = data.get("target_resistance")
    notes = data.get("notes", "").strip()

    if not symbol:
        return jsonify({"success": False, "error": "Symbol is required."}), 400

    success = database.add_to_watchlist(
        symbol=symbol,
        name=name,
        exchange=exchange,
        last_price=float(last_price) if last_price is not None else None,
        target_support=float(target_support) if target_support is not None else None,
        target_resistance=float(target_resistance) if target_resistance is not None else None,
        notes=notes
    )

    if success:
        return jsonify({"success": True, "message": f"'{symbol}' saved to watchlist."})
    return jsonify({"success": False, "error": "Failed to update watchlist."}), 500


@app.route("/api/watchlist/remove", methods=["POST"])
def remove_from_watchlist_api():
    """Removes a stock from the watchlist."""
    data = request.get_json() or {}
    symbol = data.get("symbol", "").strip()
    if not symbol:
        return jsonify({"success": False, "error": "Symbol is required."}), 400

    success = database.remove_from_watchlist(symbol)
    if success:
        return jsonify({"success": True, "message": f"'{symbol}' removed from watchlist."})
    return jsonify({"success": False, "error": "Failed to remove from watchlist."}), 500


@app.route("/api/history", methods=["GET"])
def get_history_api():
    """Retrieves calculation history."""
    records = database.get_calculation_history(limit=100)
    return jsonify({"success": True, "history": records})


@app.route("/api/history/clear", methods=["POST"])
def clear_history_api():
    """Clears all calculation history."""
    success = database.clear_calculation_history()
    return jsonify({"success": success})


@app.route("/api/history/<int:item_id>", methods=["DELETE"])
def delete_history_api(item_id: int):
    """Deletes a single history item."""
    success = database.delete_history_item(item_id)
    return jsonify({"success": success})


@app.route("/api/export/csv", methods=["GET"])
def export_csv():
    """Exports calculated levels as a CSV file."""
    symbol = request.args.get("symbol", "STOCK").strip().upper()
    price = request.args.get("price", "0.00")
    
    # We can accept levels via query or compute them
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Symbol", symbol])
    writer.writerow(["Current Price (INR)", price])
    writer.writerow([])
    writer.writerow(["Level Name", "Category", "Price (INR)", "Distance (%)", "Description"])

    # Extract query params for levels
    for key, label in [
        ("pp", "Pivot Point (PP)"),
        ("r1", "Resistance 1 (R1)"),
        ("s1", "Support 1 (S1)"),
        ("r2", "Resistance 2 (R2)"),
        ("s2", "Support 2 (S2)"),
        ("sma20", "20-Day SMA"),
        ("sma50", "50-Day SMA")
    ]:
        val = request.args.get(key)
        if val:
            try:
                p_val = float(val)
                c_val = float(price)
                pct = round(((c_val - p_val) / p_val) * 100.0, 2) if p_val > 0 else 0.0
                dist_str = f"+{abs(pct)}%" if c_val >= p_val else f"-{abs(pct)}%"
                writer.writerow([label, "Technical Level", f"₹{p_val:.2f}", dist_str, "Key indicator level"])
            except ValueError:
                pass

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={symbol}_support_resistance_levels.csv"}
    )


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
