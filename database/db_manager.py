"""
Database manager: handles SQLite connection and table creation.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "weather.db")


def get_connection():
    """Return a connection to the SQLite database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_current (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            city            TEXT    NOT NULL,
            country         TEXT    DEFAULT 'IR',
            latitude        REAL,
            longitude       REAL,
            temp_c          REAL,
            feels_like_c    REAL,
            humidity        INTEGER,
            wind_speed_kmh  REAL,
            wind_direction  TEXT,
            weather_desc    TEXT,
            visibility_km   REAL,
            pressure_mb     REAL,
            uv_index        INTEGER,
            fetched_at      TEXT    NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_forecast (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            city            TEXT    NOT NULL,
            forecast_date   TEXT    NOT NULL,
            max_temp_c      REAL,
            min_temp_c      REAL,
            avg_temp_c      REAL,
            avg_humidity    INTEGER,
            total_rain_mm   REAL,
            sunrise         TEXT,
            sunset          TEXT,
            fetched_at      TEXT    NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Tables ready.")
