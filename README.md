# 🌤 Iran Live Climate

> A complete **data pipeline** that collects, stores, and visualises live weather data for 10 major Iranian cities — with a single command.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Scrapy](https://img.shields.io/badge/Scrapy-2.11-brightgreen?logo=scrapy)
![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey?logo=sqlite)
![Pandas](https://img.shields.io/badge/Pandas-2.2-blue?logo=pandas)
![Matplotlib](https://img.shields.io/badge/Matplotlib-3.9-orange)

---

## What It Does

| Step | Description |
|------|-------------|
| 🕷 **Crawl** | A Scrapy spider fetches live weather + 3-day forecast from [wttr.in](https://wttr.in) |
| 🗄 **Store** | Raw data is validated and persisted in a local SQLite database |
| 📊 **Analyse** | Pandas loads the data and Matplotlib/Seaborn render 5 professional dark-theme charts |

**Cities covered:** Tehran · Isfahan · Mashhad · Shiraz · Tabriz · Ahvaz · Rasht · Kerman · Yazd · Urmia

---

## Charts Generated

| # | File | Description |
|---|------|-------------|
| 1 | `01_temp_bar.png` | Horizontal bar chart — current temperature comparison |
| 2 | `02_temp_trend.png` | Line chart — 3-day forecast for the 5 hottest cities |
| 3 | `03_heatmap.png` | Heatmap — temperature, humidity, wind, feels-like per city |
| 4 | `04_bubble_scatter.png` | Bubble scatter — temperature × humidity (bubble = wind speed) |
| 5 | `05_dashboard.png` | Combined dashboard — KPI cards + bar + grouped bar + forecast |

---

## Project Structure

```
iran-weather-intelligence/
├── main.py                  # Entry point — runs everything
├── requirements.txt
├── scrapy.cfg
├── crawler/
│   ├── wttr_spider.py       # Scrapy spider (wttr.in JSON API)
│   ├── middlewares.py       # Random User-Agent rotation
│   ├── pipelines.py         # SQLite persistence + validation
│   └── settings.py          # Scrapy configuration
├── database/
│   └── db_manager.py        # Connection helper & schema creation
├── analysis/
│   └── analyze.py           # Data loading + 5 charts
└── data/
    └── weather.db           # Auto-created SQLite database
```

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/mahdirostami2004/weather_crawler.git
cd iran-weather-intelligence

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the full pipeline
python main.py
```

Charts are saved in the `analysis/` folder.

---

## Data Pipeline

```
wttr.in JSON API
      │
      ▼
[Scrapy Spider]  ← random User-Agent, retry on failure, 1 s delay
      │
      ▼
[Validation]     ← temp range check, humidity check
      │
      ▼
[SQLite DB]      ← weather_current + weather_forecast tables
      │
      ▼
[Pandas / NumPy] ← aggregation, normalisation
      │
      ▼
[5 PNG Charts]   ← dark theme, saved to analysis/
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web scraping | Scrapy 2.11 (middleware, pipelines, retry) |
| Storage | SQLite via Python `sqlite3` |
| Data processing | Pandas, NumPy |
| Visualisation | Matplotlib, Seaborn |
| Runtime | Python 3.10 + virtualenv |

---

## Why This Project

- **Real data** — live API, not synthetic or mocked.  
- **Clean architecture** — crawling, storage and analysis are fully separated.  
- **Production patterns** — User-Agent rotation, retry logic, data validation before persistence.  
- **Zero heavy infrastructure** — SQLite only, runs with a single command.  
- **Extendable** — swap SQLite → PostgreSQL, add Docker, FastAPI, or Celery scheduling with minimal effort.

---

## Author

**Mahdi Rostami**  
GitHub: [github.com/mahdirostami2004](https://github.com/mahdirostami2004)
