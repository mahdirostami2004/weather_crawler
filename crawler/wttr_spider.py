"""
WttrSpider: fetches current weather and 3-day forecast for 10 Iranian cities
from the free wttr.in JSON API.
"""

import json
import scrapy
from datetime import datetime, timezone


CITIES = [
    "Tehran",
    "Isfahan",
    "Mashhad",
    "Shiraz",
    "Tabriz",
    "Ahvaz",
    "Rasht",
    "Kerman",
    "Yazd",
    "Urmia",
]

# wttr.in v1 JSON endpoint – returns current conditions + 3 days forecast
BASE_URL = "https://wttr.in/{city}?format=j1"

# Wind direction mapping (degrees → compass)
WIND_DIRS = [
    "N", "NNE", "NE", "ENE",
    "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW",
    "W", "WNW", "NW", "NNW",
]


def degrees_to_compass(deg: int) -> str:
    idx = round(deg / 22.5) % 16
    return WIND_DIRS[idx]


class WttrSpider(scrapy.Spider):
    name = "wttr_spider"
    allowed_domains = ["wttr.in"]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,   # wttr.in has no robots.txt restrictions for API
    }

    def start_requests(self):
        fetched_at = datetime.now(timezone.utc).isoformat()
        for city in CITIES:
            url = BASE_URL.format(city=city)
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                cb_kwargs={"city": city, "fetched_at": fetched_at},
                errback=self.handle_error,
            )

    # ------------------------------------------------------------------
    def parse(self, response, city: str, fetched_at: str):
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error(f"[{city}] Failed to parse JSON.")
            return

        # ── Current conditions ────────────────────────────────────────
        current = data.get("current_condition", [{}])[0]
        nearest = data.get("nearest_area", [{}])[0]

        lat = self._safe_float(nearest.get("latitude", "0"))
        lon = self._safe_float(nearest.get("longitude", "0"))
        country = nearest.get("country", [{}])[0].get("value", "IR")

        wind_deg = self._safe_int(current.get("winddirDegree", "0"))
        wind_dir = degrees_to_compass(wind_deg)

        weather_desc = (
            current.get("weatherDesc", [{}])[0].get("value", "")
        )

        yield {
            "item_type":      "current",
            "city":           city,
            "country":        country,
            "latitude":       lat,
            "longitude":      lon,
            "temp_c":         self._safe_float(current.get("temp_C")),
            "feels_like_c":   self._safe_float(current.get("FeelsLikeC")),
            "humidity":       self._safe_int(current.get("humidity")),
            "wind_speed_kmh": self._safe_float(current.get("windspeedKmph")),
            "wind_direction": wind_dir,
            "weather_desc":   weather_desc,
            "visibility_km":  self._safe_float(current.get("visibility")),
            "pressure_mb":    self._safe_float(current.get("pressure")),
            "uv_index":       self._safe_int(current.get("uvIndex")),
            "fetched_at":     fetched_at,
        }

        # ── 3-day forecast ────────────────────────────────────────────
        for day in data.get("weather", []):
            hourly = day.get("hourly", [])
            temps = [self._safe_float(h.get("tempC")) for h in hourly
                     if h.get("tempC") is not None]
            humids = [self._safe_int(h.get("humidity")) for h in hourly
                      if h.get("humidity") is not None]

            avg_temp = round(sum(temps) / len(temps), 1) if temps else None
            avg_hum  = round(sum(humids) / len(humids)) if humids else None

            sunrise_list = day.get("astronomy", [{}])
            sunrise = sunrise_list[0].get("sunrise", "") if sunrise_list else ""
            sunset  = sunrise_list[0].get("sunset", "")  if sunrise_list else ""

            yield {
                "item_type":    "forecast",
                "city":         city,
                "forecast_date": day.get("date"),
                "max_temp_c":   self._safe_float(day.get("maxtempC")),
                "min_temp_c":   self._safe_float(day.get("mintempC")),
                "avg_temp_c":   avg_temp,
                "avg_humidity": avg_hum,
                "total_rain_mm": self._safe_float(day.get("hourly", [{}])[0].get("precipMM", "0")),
                "sunrise":      sunrise,
                "sunset":       sunset,
                "fetched_at":   fetched_at,
            }

    # ------------------------------------------------------------------
    def handle_error(self, failure):
        self.logger.error(f"[Request failed] {failure.request.url}: {failure.value}")

    # ------------------------------------------------------------------
    @staticmethod
    def _safe_float(val):
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_int(val):
        try:
            return int(val)
        except (TypeError, ValueError):
            return None
