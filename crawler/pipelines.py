"""
Item pipelines for Iran Weather Intelligence.
WeatherSQLitePipeline: validates and persists items to SQLite.
"""

import logging
from database.db_manager import get_connection, init_db

logger = logging.getLogger(__name__)

TEMP_MIN = -60.0
TEMP_MAX = 65.0
HUMIDITY_MIN = 0
HUMIDITY_MAX = 100


class WeatherSQLitePipeline:
    """Validate weather items and save them to the SQLite database."""

    def open_spider(self, spider):
        init_db()
        self.conn = get_connection()
        self.cursor = self.conn.cursor()
        logger.info("[Pipeline] SQLite connection opened.")

    def close_spider(self, spider):
        self.conn.commit()
        self.conn.close()
        logger.info("[Pipeline] SQLite connection closed and committed.")

    def process_item(self, item, spider):
        item_type = item.get("item_type")

        if item_type == "current":
            return self._save_current(item)
        elif item_type == "forecast":
            return self._save_forecast(item)
        else:
            logger.warning(f"[Pipeline] Unknown item_type: {item_type}")
            return item

    # ------------------------------------------------------------------
    def _validate_current(self, item):
        temp = item.get("temp_c")
        humidity = item.get("humidity")

        if temp is None or not (TEMP_MIN <= temp <= TEMP_MAX):
            logger.warning(
                f"[Validation] Rejected current item for {item.get('city')}: "
                f"temp_c={temp} out of range."
            )
            return False

        if humidity is not None and not (HUMIDITY_MIN <= humidity <= HUMIDITY_MAX):
            logger.warning(
                f"[Validation] Rejected current item for {item.get('city')}: "
                f"humidity={humidity} out of range."
            )
            return False

        return True

    def _save_current(self, item):
        if not self._validate_current(item):
            return item

        self.cursor.execute(
            """
            INSERT INTO weather_current
                (city, country, latitude, longitude, temp_c, feels_like_c,
                 humidity, wind_speed_kmh, wind_direction, weather_desc,
                 visibility_km, pressure_mb, uv_index, fetched_at)
            VALUES
                (:city, :country, :latitude, :longitude, :temp_c, :feels_like_c,
                 :humidity, :wind_speed_kmh, :wind_direction, :weather_desc,
                 :visibility_km, :pressure_mb, :uv_index, :fetched_at)
            """,
            dict(item),
        )
        logger.info(f"[Pipeline] Saved current weather for {item['city']}.")
        return item

    def _save_forecast(self, item):
        self.cursor.execute(
            """
            INSERT INTO weather_forecast
                (city, forecast_date, max_temp_c, min_temp_c, avg_temp_c,
                 avg_humidity, total_rain_mm, sunrise, sunset, fetched_at)
            VALUES
                (:city, :forecast_date, :max_temp_c, :min_temp_c, :avg_temp_c,
                 :avg_humidity, :total_rain_mm, :sunrise, :sunset, :fetched_at)
            """,
            dict(item),
        )
        logger.info(
            f"[Pipeline] Saved forecast for {item['city']} on {item['forecast_date']}."
        )
        return item
