"""
Data analysis and visualization module.
Produces 5 professional dark-themed charts from the SQLite database.
"""

import os
import sys
import sqlite3
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from datetime import datetime

matplotlib.use("Agg")  # Non-interactive backend – safe for server use

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "data", "weather.db")
OUT_DIR  = os.path.join(BASE_DIR, "analysis")

# ── Palette ────────────────────────────────────────────────────────────────────
BG_COLOR      = "#0d1117"
CARD_COLOR    = "#161b22"
ACCENT        = "#58a6ff"
ACCENT2       = "#3fb950"
ACCENT3       = "#f78166"
TEXT_COLOR    = "#e6edf3"
MUTED_TEXT    = "#8b949e"
GRID_COLOR    = "#21262d"

CITY_COLORS = [
    "#58a6ff", "#3fb950", "#f78166", "#d2a8ff",
    "#ffa657", "#79c0ff", "#56d364", "#ff7b72",
    "#cae8ff", "#7ee787",
]


def _apply_dark_style():
    plt.rcParams.update({
        "figure.facecolor":   BG_COLOR,
        "axes.facecolor":     CARD_COLOR,
        "axes.edgecolor":     GRID_COLOR,
        "axes.labelcolor":    TEXT_COLOR,
        "axes.titlecolor":    TEXT_COLOR,
        "xtick.color":        MUTED_TEXT,
        "ytick.color":        MUTED_TEXT,
        "text.color":         TEXT_COLOR,
        "grid.color":         GRID_COLOR,
        "grid.linestyle":     "--",
        "grid.alpha":         0.5,
        "legend.facecolor":   CARD_COLOR,
        "legend.edgecolor":   GRID_COLOR,
        "legend.labelcolor":  TEXT_COLOR,
        "font.family":        "DejaVu Sans",
        "font.size":          11,
    })


# ── Data loaders ───────────────────────────────────────────────────────────────

def _load_current() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        """
        SELECT city, temp_c, feels_like_c, humidity, wind_speed_kmh,
               weather_desc, latitude, longitude, fetched_at
        FROM weather_current
        ORDER BY fetched_at DESC
        """,
        conn,
    )
    conn.close()
    # Keep only the most-recent row per city
    df = df.drop_duplicates(subset="city", keep="first").reset_index(drop=True)
    return df


def _load_forecast() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        """
        SELECT city, forecast_date, max_temp_c, min_temp_c, avg_temp_c,
               avg_humidity, total_rain_mm
        FROM weather_forecast
        ORDER BY city, forecast_date
        """,
        conn,
    )
    conn.close()
    df["forecast_date"] = pd.to_datetime(df["forecast_date"])
    return df


def _save(fig, name: str):
    path = os.path.join(OUT_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    print(f"  [Chart] Saved → {path}")


# ── Chart 1 – Horizontal bar: current temperature comparison ──────────────────

def chart_temp_bar(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(CARD_COLOR)

    df_sorted = df.sort_values("temp_c", ascending=True).reset_index(drop=True)
    bars = ax.barh(
        df_sorted["city"],
        df_sorted["temp_c"],
        color=CITY_COLORS[: len(df_sorted)],
        edgecolor="none",
        height=0.6,
    )

    # Value labels
    for bar, val in zip(bars, df_sorted["temp_c"]):
        ax.text(
            bar.get_width() + 0.3,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.1f} °C",
            va="center",
            ha="left",
            color=TEXT_COLOR,
            fontsize=10,
        )

    ax.set_xlabel("Temperature (°C)", color=TEXT_COLOR)
    ax.set_title("Current Temperature — 10 Iranian Cities", color=TEXT_COLOR,
                 fontsize=15, fontweight="bold", pad=15)
    ax.axvline(df_sorted["temp_c"].mean(), color=MUTED_TEXT, linewidth=1,
               linestyle="--", label=f"Mean: {df_sorted['temp_c'].mean():.1f} °C")
    ax.legend()
    ax.grid(axis="x", color=GRID_COLOR, linestyle="--", alpha=0.5)
    ax.spines[:].set_visible(False)

    _save(fig, "01_temp_bar.png")


# ── Chart 2 – Line chart: 3-day temperature trend (top 5 cities) ──────────────

def chart_temp_trend(df_current: pd.DataFrame, df_forecast: pd.DataFrame):
    top5 = (
        df_current.sort_values("temp_c", ascending=False)
        .head(5)["city"]
        .tolist()
    )

    fig, ax = plt.subplots(figsize=(13, 7))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(CARD_COLOR)

    for i, city in enumerate(top5):
        city_df = df_forecast[df_forecast["city"] == city].drop_duplicates(
            subset="forecast_date"
        )
        if city_df.empty:
            continue
        ax.plot(
            city_df["forecast_date"],
            city_df["avg_temp_c"],
            marker="o",
            linewidth=2.5,
            markersize=7,
            color=CITY_COLORS[i],
            label=city,
        )
        # Fill between min/max
        ax.fill_between(
            city_df["forecast_date"],
            city_df["min_temp_c"],
            city_df["max_temp_c"],
            alpha=0.10,
            color=CITY_COLORS[i],
        )

    ax.set_xlabel("Date", color=TEXT_COLOR)
    ax.set_ylabel("Temperature (°C)", color=TEXT_COLOR)
    ax.set_title("3-Day Temperature Trend — Top 5 Hottest Cities",
                 color=TEXT_COLOR, fontsize=15, fontweight="bold", pad=15)
    ax.legend(loc="upper right")
    ax.grid(color=GRID_COLOR, linestyle="--", alpha=0.5)
    ax.spines[:].set_visible(False)
    fig.autofmt_xdate()

    _save(fig, "02_temp_trend.png")


# ── Chart 3 – Heatmap: avg temperature & humidity per city ────────────────────

def chart_heatmap(df: pd.DataFrame):
    # Build a small metrics matrix
    heat_df = df[["city", "temp_c", "humidity", "wind_speed_kmh", "feels_like_c"]].copy()
    heat_df = heat_df.set_index("city")
    heat_df.columns = ["Temp (°C)", "Humidity (%)", "Wind (km/h)", "Feels Like (°C)"]

    # Normalise each column to [0,1] for visual consistency
    normed = (heat_df - heat_df.min()) / (heat_df.max() - heat_df.min())

    fig, axes = plt.subplots(1, 2, figsize=(16, 7), gridspec_kw={"width_ratios": [1.4, 1]})
    fig.patch.set_facecolor(BG_COLOR)

    # Left: normalised heatmap
    ax = axes[0]
    ax.set_facecolor(CARD_COLOR)
    cmap = sns.diverging_palette(220, 20, as_cmap=True)
    sns.heatmap(
        normed,
        ax=ax,
        cmap="YlOrRd",
        linewidths=0.5,
        linecolor=BG_COLOR,
        annot=heat_df.round(1),
        fmt=".1f",
        annot_kws={"size": 10, "color": BG_COLOR},
        cbar_kws={"shrink": 0.8, "label": "Normalised value"},
    )
    ax.set_title("Weather Metrics Heatmap", color=TEXT_COLOR,
                 fontsize=14, fontweight="bold", pad=12)
    ax.tick_params(colors=TEXT_COLOR)
    ax.set_xlabel("")
    ax.set_ylabel("")

    # Right: humidity ranking bar
    ax2 = axes[1]
    ax2.set_facecolor(CARD_COLOR)
    df_h = df.sort_values("humidity", ascending=True)
    bars = ax2.barh(df_h["city"], df_h["humidity"],
                    color=ACCENT, edgecolor="none", height=0.6)
    for bar, val in zip(bars, df_h["humidity"]):
        ax2.text(bar.get_width() - 2, bar.get_y() + bar.get_height() / 2,
                 f"{val}%", va="center", ha="right", color=BG_COLOR,
                 fontsize=9, fontweight="bold")
    ax2.set_xlabel("Humidity (%)", color=TEXT_COLOR)
    ax2.set_title("Humidity Ranking", color=TEXT_COLOR,
                  fontsize=14, fontweight="bold", pad=12)
    ax2.spines[:].set_visible(False)
    ax2.grid(axis="x", color=GRID_COLOR, alpha=0.4)

    plt.tight_layout(pad=2.0)
    _save(fig, "03_heatmap.png")


# ── Chart 4 – Bubble scatter: temp × humidity (bubble = wind speed) ───────────

def chart_bubble(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(13, 8))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(CARD_COLOR)

    wind_vals = df["wind_speed_kmh"].fillna(10)
    # Scale bubble area: min 100, max 1500
    wind_norm = (wind_vals - wind_vals.min()) / (wind_vals.max() - wind_vals.min() + 1e-9)
    sizes = 100 + wind_norm * 1400

    sc = ax.scatter(
        df["temp_c"],
        df["humidity"],
        s=sizes,
        c=df["temp_c"],
        cmap="plasma",
        alpha=0.85,
        edgecolors=TEXT_COLOR,
        linewidths=0.6,
    )

    for _, row in df.iterrows():
        ax.annotate(
            row["city"],
            (row["temp_c"], row["humidity"]),
            textcoords="offset points",
            xytext=(8, 4),
            color=TEXT_COLOR,
            fontsize=9,
        )

    cbar = fig.colorbar(sc, ax=ax, shrink=0.7, pad=0.02)
    cbar.set_label("Temperature (°C)", color=TEXT_COLOR)
    cbar.ax.yaxis.set_tick_params(color=MUTED_TEXT)

    ax.set_xlabel("Temperature (°C)", color=TEXT_COLOR)
    ax.set_ylabel("Humidity (%)", color=TEXT_COLOR)
    ax.set_title("Temperature vs Humidity  (bubble size = wind speed)",
                 color=TEXT_COLOR, fontsize=14, fontweight="bold", pad=15)
    ax.grid(color=GRID_COLOR, linestyle="--", alpha=0.5)
    ax.spines[:].set_visible(False)

    # Wind speed legend
    for wind_label, wind_val in [("Low wind", wind_vals.min()), ("High wind", wind_vals.max())]:
        wn = (wind_val - wind_vals.min()) / (wind_vals.max() - wind_vals.min() + 1e-9)
        ax.scatter([], [], s=100 + wn * 1400, c=MUTED_TEXT, alpha=0.5,
                   label=f"{wind_label} ({wind_val:.0f} km/h)")
    ax.legend(scatterpoints=1, labelspacing=1.2, loc="upper right")

    _save(fig, "04_bubble_scatter.png")


# ── Chart 5 – Combined dashboard ──────────────────────────────────────────────

def chart_dashboard(df: pd.DataFrame, df_forecast: pd.DataFrame):
    fig = plt.figure(figsize=(18, 10))
    fig.patch.set_facecolor(BG_COLOR)
    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.35)

    # ── KPI cards (top row) ──────────────────────────────────────────
    hottest  = df.loc[df["temp_c"].idxmax()]
    coolest  = df.loc[df["temp_c"].idxmin()]
    moistest = df.loc[df["humidity"].idxmax()]
    windiest = df.loc[df["wind_speed_kmh"].idxmax()]

    kpi_data = [
        ("🌡  Hottest",    hottest["city"],   f"{hottest['temp_c']:.1f} °C",   ACCENT3),
        ("❄️  Coolest",    coolest["city"],   f"{coolest['temp_c']:.1f} °C",   ACCENT),
        ("💧 Moistest",   moistest["city"],  f"{moistest['humidity']} %",      ACCENT2),
    ]

    for col_idx, (label, city, value, color) in enumerate(kpi_data):
        ax_card = fig.add_subplot(gs[0, col_idx])
        ax_card.set_facecolor(CARD_COLOR)
        ax_card.set_xlim(0, 1)
        ax_card.set_ylim(0, 1)
        ax_card.axis("off")
        ax_card.text(0.5, 0.75, label,   ha="center", va="center",
                     fontsize=12, color=MUTED_TEXT)
        ax_card.text(0.5, 0.50, city,    ha="center", va="center",
                     fontsize=18, fontweight="bold", color=color)
        ax_card.text(0.5, 0.25, value,   ha="center", va="center",
                     fontsize=22, fontweight="bold", color=TEXT_COLOR)
        for spine in ax_card.spines.values():
            spine.set_edgecolor(color)
            spine.set_linewidth(2)
            spine.set_visible(True)

    # ── Bottom-left: wind speed bar ────────────────────────────────
    ax_wind = fig.add_subplot(gs[1, 0])
    ax_wind.set_facecolor(CARD_COLOR)
    dfw = df.sort_values("wind_speed_kmh", ascending=True)
    ax_wind.barh(dfw["city"], dfw["wind_speed_kmh"],
                 color=ACCENT2, edgecolor="none", height=0.6)
    ax_wind.set_xlabel("Wind Speed (km/h)", color=TEXT_COLOR)
    ax_wind.set_title("Wind Speed", color=TEXT_COLOR, fontweight="bold")
    ax_wind.spines[:].set_visible(False)
    ax_wind.grid(axis="x", color=GRID_COLOR, alpha=0.4)

    # ── Bottom-centre: feels-like vs actual ───────────────────────
    ax_feel = fig.add_subplot(gs[1, 1])
    ax_feel.set_facecolor(CARD_COLOR)
    x = np.arange(len(df))
    w = 0.38
    ax_feel.bar(x - w / 2, df["temp_c"],         width=w, label="Actual",    color=ACCENT,  alpha=0.9)
    ax_feel.bar(x + w / 2, df["feels_like_c"],   width=w, label="Feels Like",color=ACCENT3, alpha=0.9)
    ax_feel.set_xticks(x)
    ax_feel.set_xticklabels(df["city"], rotation=45, ha="right", color=TEXT_COLOR, fontsize=8)
    ax_feel.set_ylabel("°C", color=TEXT_COLOR)
    ax_feel.set_title("Actual vs Feels Like", color=TEXT_COLOR, fontweight="bold")
    ax_feel.legend(fontsize=9)
    ax_feel.spines[:].set_visible(False)
    ax_feel.grid(axis="y", color=GRID_COLOR, alpha=0.4)

    # ── Bottom-right: forecast avg temp (all cities, line) ────────
    ax_fc = fig.add_subplot(gs[1, 2])
    ax_fc.set_facecolor(CARD_COLOR)
    for i, city in enumerate(df["city"].tolist()[:5]):
        cdf = df_forecast[df_forecast["city"] == city].drop_duplicates("forecast_date")
        if cdf.empty:
            continue
        ax_fc.plot(cdf["forecast_date"], cdf["avg_temp_c"],
                   marker="o", markersize=4, linewidth=1.8,
                   color=CITY_COLORS[i], label=city)
    ax_fc.set_title("3-Day Forecast (Top 5)", color=TEXT_COLOR, fontweight="bold")
    ax_fc.set_ylabel("°C", color=TEXT_COLOR)
    ax_fc.legend(fontsize=8)
    ax_fc.grid(color=GRID_COLOR, alpha=0.4)
    ax_fc.spines[:].set_visible(False)
    fig.autofmt_xdate()

    fig.suptitle(
        f"Iran Weather Intelligence Dashboard  •  {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        color=TEXT_COLOR, fontsize=16, fontweight="bold", y=1.01,
    )

    _save(fig, "05_dashboard.png")


# ── Entry point ────────────────────────────────────────────────────────────────

def run_analysis():
    _apply_dark_style()
    os.makedirs(OUT_DIR, exist_ok=True)

    print("\n[Analysis] Loading data from database...")
    df_current  = _load_current()
    df_forecast = _load_forecast()

    if df_current.empty:
        print("[Analysis] No current-weather data found. Run the spider first.")
        sys.exit(1)

    print(f"[Analysis] {len(df_current)} cities loaded. Generating charts...\n")

    chart_temp_bar(df_current)
    chart_temp_trend(df_current, df_forecast)
    chart_heatmap(df_current)
    chart_bubble(df_current)
    chart_dashboard(df_current, df_forecast)

    print("\n[Analysis] All 5 charts saved to analysis/")


if __name__ == "__main__":
    run_analysis()
