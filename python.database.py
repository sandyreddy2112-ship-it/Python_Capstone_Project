"""
SQLite Database Storage for Stock Watchlists and Calculation History.
"""

import sqlite3
import datetime
import os
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stocks_data.db")


def get_db_connection():
    """Returns a connection to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes SQLite database tables for watchlist and calculation history."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Watchlist table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            exchange TEXT DEFAULT 'NSE',
            last_price REAL,
            target_support REAL,
            target_resistance REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Calculation History table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calculation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            name TEXT NOT NULL,
            period TEXT NOT NULL,
            current_price REAL NOT NULL,
            pivot REAL,
            s1 REAL,
            s2 REAL,
            r1 REAL,
            r2 REAL,
            sma20 REAL,
            sma50 REAL,
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def add_to_watchlist(
    symbol: str,
    name: str,
    exchange: str = "NSE",
    last_price: Optional[float] = None,
    target_support: Optional[float] = None,
    target_resistance: Optional[float] = None,
    notes: Optional[str] = None
) -> bool:
    """Adds or updates a stock in the user's watchlist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO watchlist (symbol, name, exchange, last_price, target_support, target_resistance, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(symbol) DO UPDATE SET
                name=excluded.name,
                exchange=excluded.exchange,
                last_price=COALESCE(excluded.last_price, watchlist.last_price),
                target_support=COALESCE(excluded.target_support, watchlist.target_support),
                target_resistance=COALESCE(excluded.target_resistance, watchlist.target_resistance),
                notes=COALESCE(excluded.notes, watchlist.notes),
                updated_at=CURRENT_TIMESTAMP
        """, (symbol.upper(), name, exchange, last_price, target_support, target_resistance, notes))
        conn.commit()
        return True
    except Exception as e:
        print(f"Database error in add_to_watchlist: {e}")
        return False
    finally:
        conn.close()


def remove_from_watchlist(symbol: str) -> bool:
    """Removes a stock from the watchlist by symbol."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM watchlist WHERE symbol = ?", (symbol.upper(),))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Database error in remove_from_watchlist: {e}")
        return False
    finally:
        conn.close()


def get_watchlist() -> List[Dict[str, Any]]:
    """Retrieves all stocks from the user's watchlist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM watchlist ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def is_in_watchlist(symbol: str) -> bool:
    """Checks if a stock symbol is already saved in the watchlist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM watchlist WHERE symbol = ?", (symbol.upper(),))
        row = cursor.fetchone()
        return row is not None
    finally:
        conn.close()


def log_calculation(
    symbol: str,
    name: str,
    period: str,
    current_price: float,
    pivot: Optional[float] = None,
    s1: Optional[float] = None,
    s2: Optional[float] = None,
    r1: Optional[float] = None,
    r2: Optional[float] = None,
    sma20: Optional[float] = None,
    sma50: Optional[float] = None
) -> bool:
    """Logs a calculation into history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO calculation_history 
            (symbol, name, period, current_price, pivot, s1, s2, r1, r2, sma20, sma50, calculated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (symbol.upper(), name, period, current_price, pivot, s1, s2, r1, r2, sma20, sma50))
        conn.commit()
        return True
    except Exception as e:
        print(f"Database error in log_calculation: {e}")
        return False
    finally:
        conn.close()


def get_calculation_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Fetches calculation history sorted from newest to oldest."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM calculation_history ORDER BY calculated_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def clear_calculation_history() -> bool:
    """Clears all records in calculation history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM calculation_history")
        conn.commit()
        return True
    except Exception as e:
        print(f"Database error in clear_calculation_history: {e}")
        return False
    finally:
        conn.close()


def delete_history_item(item_id: int) -> bool:
    """Deletes a specific calculation history item by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM calculation_history WHERE id = ?", (item_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Database error in delete_history_item: {e}")
        return False
    finally:
        conn.close()
