"""
Support and Resistance Mathematical Calculations
Contains 100% traditional mathematical and technical analysis algorithms:
- Standard Classical Pivot Points (Floor Pivots) & Fibonacci Pivots
- Historical Swing Highs and Lows with percentage clustering
- Simple Moving Averages (SMA 20, SMA 50, SMA 200)
- Distance and level proximity metrics

NO AI, Machine Learning, or Deep Learning is used.
"""

from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd


def calculate_pivot_points(high: float, low: float, close: float) -> Dict[str, float]:
    """
    Calculates Standard Classical Floor Pivot Points from previous period High, Low, Close.
    Formulas:
        Pivot Point (PP) = (High + Low + Close) / 3
        Resistance 1 (R1) = (2 * PP) - Low
        Support 1 (S1)    = (2 * PP) - High
        Resistance 2 (R2) = PP + (High - Low)
        Support 2 (S2)    = PP - (High - Low)
        Resistance 3 (R3) = High + 2 * (PP - Low)
        Support 3 (S3)    = Low - 2 * (High - PP)
    """
    pp = (high + low + close) / 3.0
    r1 = (2.0 * pp) - low
    s1 = (2.0 * pp) - high
    r2 = pp + (high - low)
    s2 = pp - (high - low)
    r3 = high + 2.0 * (pp - low)
    s3 = low - 2.0 * (high - pp)

    # Fibonacci Pivot Points
    range_hl = high - low
    fib_r1 = pp + (0.382 * range_hl)
    fib_r2 = pp + (0.618 * range_hl)
    fib_r3 = pp + (1.000 * range_hl)
    fib_s1 = pp - (0.382 * range_hl)
    fib_s2 = pp - (0.618 * range_hl)
    fib_s3 = pp - (1.000 * range_hl)

    return {
        "pivot": round(pp, 2),
        "r1": round(r1, 2),
        "s1": round(s1, 2),
        "r2": round(r2, 2),
        "s2": round(s2, 2),
        "r3": round(r3, 2),
        "s3": round(s3, 2),
        "fibonacci": {
            "pivot": round(pp, 2),
            "r1": round(fib_r1, 2),
            "r2": round(fib_r2, 2),
            "r3": round(fib_r3, 2),
            "s1": round(fib_s1, 2),
            "s2": round(fib_s2, 2),
            "s3": round(fib_s3, 2),
        }
    }


def calculate_moving_averages(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculates 20-day, 50-day, and 200-day Simple Moving Averages (SMA).
    Returns latest SMA values and historical series for charting.
    """
    if df.empty or "Close" not in df.columns:
        return {"sma20": None, "sma50": None, "sma200": None, "series": {}}

    close_series = df["Close"]
    sma20_series = close_series.rolling(window=20).mean()
    sma50_series = close_series.rolling(window=50).mean()
    sma200_series = close_series.rolling(window=200).mean()

    def get_latest(series: pd.Series) -> Optional[float]:
        val = series.dropna()
        if not val.empty:
            return round(float(val.iloc[-1]), 2)
        return None

    # Replace NaNs with None for JSON serialization
    sma20_clean = [round(float(v), 2) if pd.notna(v) else None for v in sma20_series]
    sma50_clean = [round(float(v), 2) if pd.notna(v) else None for v in sma50_series]
    sma200_clean = [round(float(v), 2) if pd.notna(v) else None for v in sma200_series]

    return {
        "sma20": get_latest(sma20_series),
        "sma50": get_latest(sma50_series),
        "sma200": get_latest(sma200_series),
        "series": {
            "sma20": sma20_clean,
            "sma50": sma50_clean,
            "sma200": sma200_clean
        }
    }


def find_swing_highs_and_lows(df: pd.DataFrame, window: int = 3) -> Dict[str, List[Dict[str, Any]]]:
    """
    Identifies local swing highs (peaks) and swing lows (troughs) using a rolling window.
    A swing high occurs at index i if df['High'][i] is greater than or equal to highs
    in the preceding and following `window` bars.
    A swing low occurs at index i if df['Low'][i] is less than or equal to lows
    in the preceding and following `window` bars.
    """
    swing_highs = []
    swing_lows = []

    if len(df) < (window * 2 + 1):
        return {"highs": swing_highs, "lows": swing_lows}

    highs = df["High"].values
    lows = df["Low"].values
    dates = df.index

    for i in range(window, len(df) - window):
        current_high = highs[i]
        is_swing_high = True
        for offset in range(-window, window + 1):
            if offset == 0:
                continue
            if highs[i + offset] > current_high:
                is_swing_high = False
                break
        if is_swing_high:
            date_str = str(dates[i].date()) if hasattr(dates[i], "date") else str(dates[i])
            swing_highs.append({
                "price": round(float(current_high), 2),
                "date": date_str,
                "index": i
            })

        current_low = lows[i]
        is_swing_low = True
        for offset in range(-window, window + 1):
            if offset == 0:
                continue
            if lows[i + offset] < current_low:
                is_swing_low = False
                break
        if is_swing_low:
            date_str = str(dates[i].date()) if hasattr(dates[i], "date") else str(dates[i])
            swing_lows.append({
                "price": round(float(current_low), 2),
                "date": date_str,
                "index": i
            })

    return {"highs": swing_highs, "lows": swing_lows}


def cluster_price_levels(levels: List[Dict[str, Any]], tolerance_pct: float = 1.25) -> List[Dict[str, Any]]:
    """
    Groups nearby price levels within a configurable percentage tolerance.
    For each cluster:
      - average price is calculated
      - touch count (strength) is tallied
      - min/max bounds of the zone are noted
      - sorted by touch count (descending) and proximity
    """
    if not levels:
        return []

    # Sort levels by price ascending
    sorted_levels = sorted(levels, key=lambda x: x["price"])
    clusters: List[List[Dict[str, Any]]] = []

    for item in sorted_levels:
        price = item["price"]
        matched_cluster = None
        for cluster in clusters:
            cluster_avg = sum(p["price"] for p in cluster) / len(cluster)
            pct_diff = abs(price - cluster_avg) / cluster_avg * 100.0
            if pct_diff <= tolerance_pct:
                matched_cluster = cluster
                break

        if matched_cluster is not None:
            matched_cluster.append(item)
        else:
            clusters.append([item])

    result = []
    for cluster in clusters:
        prices = [p["price"] for p in cluster]
        dates = [p["date"] for p in cluster if "date" in p]
        avg_price = round(sum(prices) / len(prices), 2)
        min_price = round(min(prices), 2)
        max_price = round(max(prices), 2)
        touches = len(cluster)

        result.append({
            "price": avg_price,
            "zone_min": min_price,
            "zone_max": max_price,
            "touches": touches,
            "dates": dates,
            "recent_date": dates[-1] if dates else ""
        })

    # Sort primarily by touches (strength) descending, then price
    result.sort(key=lambda x: (x["touches"], x["price"]), reverse=True)
    return result


def compute_percentage_distance(current_price: float, target_price: Optional[float]) -> Optional[Dict[str, Any]]:
    """
    Calculates point difference and percentage distance between current price and a target level.
    Positive percentage means current price is ABOVE the target level.
    Negative percentage means current price is BELOW the target level.
    """
    if target_price is None or target_price <= 0 or current_price <= 0:
        return None

    diff_points = round(current_price - target_price, 2)
    pct_dist = round(((current_price - target_price) / target_price) * 100.0, 2)

    if abs(pct_dist) < 0.25:
        relation = "at_level"
        description = "Testing Level"
    elif current_price > target_price:
        relation = "above"
        description = f"+{abs(pct_dist)}% Above"
    else:
        relation = "below"
        description = f"-{abs(pct_dist)}% Below"

    return {
        "diff_points": diff_points,
        "percentage": pct_dist,
        "absolute_percentage": abs(pct_dist),
        "relation": relation,
        "description": description
    }


def analyze_all_levels(
    current_price: float,
    pivot_data: Dict[str, Any],
    moving_averages: Dict[str, Any],
    swing_highs_clustered: List[Dict[str, Any]],
    swing_lows_clustered: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Combines all support and resistance levels into a structured analysis:
    - Segregates levels into Supports (below current price) and Resistances (above current price)
    - Computes distance from current price for each
    - Determines immediate (nearest) support and immediate (nearest) resistance
    """
    supports = []
    resistances = []
    all_levels = []

    # 1. Pivot Points
    pivot_items = [
        ("Pivot Point (PP)", pivot_data.get("pivot"), "pivot", "Central reference point based on previous session"),
        ("Pivot Support 1 (S1)", pivot_data.get("s1"), "support", "First floor pivot support level"),
        ("Pivot Support 2 (S2)", pivot_data.get("s2"), "support", "Second floor pivot support level"),
        ("Pivot Support 3 (S3)", pivot_data.get("s3"), "support", "Major floor pivot support level"),
        ("Pivot Resistance 1 (R1)", pivot_data.get("r1"), "resistance", "First floor pivot resistance level"),
        ("Pivot Resistance 2 (R2)", pivot_data.get("r2"), "resistance", "Second floor pivot resistance level"),
        ("Pivot Resistance 3 (R3)", pivot_data.get("r3"), "resistance", "Major floor pivot resistance level"),
    ]

    for name, price, level_type, desc in pivot_items:
        if price is not None and price > 0:
            dist = compute_percentage_distance(current_price, price)
            entry = {
                "name": name,
                "price": price,
                "type": level_type,
                "category": "Pivot Point",
                "description": desc,
                "distance": dist,
                "strength": 2  # Standard pivot strength
            }
            all_levels.append(entry)
            if price < current_price:
                supports.append(entry)
            elif price > current_price:
                resistances.append(entry)

    # 2. Moving Averages (Reference indicators)
    ma_items = [
        ("20-Day SMA", moving_averages.get("sma20"), "Short-term trend reference"),
        ("50-Day SMA", moving_averages.get("sma50"), "Medium-term trend reference"),
        ("200-Day SMA", moving_averages.get("sma200"), "Long-term trend reference")
    ]

    ma_entries = []
    for name, price, desc in ma_items:
        if price is not None and price > 0:
            dist = compute_percentage_distance(current_price, price)
            bias = "Bullish" if current_price >= price else "Bearish"
            entry = {
                "name": name,
                "price": price,
                "type": "indicator",
                "bias": bias,
                "category": "Moving Average",
                "description": f"{desc} ({bias} bias)",
                "distance": dist
            }
            ma_entries.append(entry)
            all_levels.append(entry)

    # 3. Swing Highs (typically act as Resistance, but if price broke above them, can act as Support)
    for idx, cluster in enumerate(swing_highs_clustered[:5]):
        price = cluster["price"]
        dist = compute_percentage_distance(current_price, price)
        touches = cluster["touches"]
        role = "Resistance" if price > current_price else "Support (Prior Resistance)"
        level_type = "resistance" if price > current_price else "support"
        entry = {
            "name": f"Swing Peak #{idx + 1}",
            "price": price,
            "zone_min": cluster["zone_min"],
            "zone_max": cluster["zone_max"],
            "type": level_type,
            "category": "Price Action Swing",
            "touches": touches,
            "strength": touches,
            "description": f"Tested {touches}x peak zone ({cluster['zone_min']} - {cluster['zone_max']})",
            "distance": dist
        }
        all_levels.append(entry)
        if level_type == "support":
            supports.append(entry)
        else:
            resistances.append(entry)

    # 4. Swing Lows (typically act as Support, but if price broke below them, can act as Resistance)
    for idx, cluster in enumerate(swing_lows_clustered[:5]):
        price = cluster["price"]
        dist = compute_percentage_distance(current_price, price)
        touches = cluster["touches"]
        role = "Support" if price < current_price else "Resistance (Prior Support)"
        level_type = "support" if price < current_price else "resistance"
        entry = {
            "name": f"Swing Trough #{idx + 1}",
            "price": price,
            "zone_min": cluster["zone_min"],
            "zone_max": cluster["zone_max"],
            "type": level_type,
            "category": "Price Action Swing",
            "touches": touches,
            "strength": touches,
            "description": f"Tested {touches}x bounce zone ({cluster['zone_min']} - {cluster['zone_max']})",
            "distance": dist
        }
        all_levels.append(entry)
        if level_type == "support":
            supports.append(entry)
        else:
            resistances.append(entry)

    # Sort supports: highest price first (closest to current price)
    supports.sort(key=lambda x: x["price"], reverse=True)

    # Sort resistances: lowest price first (closest to current price)
    resistances.sort(key=lambda x: x["price"])

    nearest_support = supports[0] if supports else None
    nearest_resistance = resistances[0] if resistances else None

    return {
        "all_levels": all_levels,
        "supports": supports,
        "resistances": resistances,
        "moving_averages": ma_entries,
        "nearest_support": nearest_support,
        "nearest_resistance": nearest_resistance,
        "pivot_point": pivot_data.get("pivot"),
        "pivot_distance": compute_percentage_distance(current_price, pivot_data.get("pivot"))
    }
