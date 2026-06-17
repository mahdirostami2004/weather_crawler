"""
Scrapy project settings for Iran Weather Intelligence.
"""

BOT_NAME = "iran_weather"

SPIDER_MODULES = ["crawler"]
NEWSPIDER_MODULE = "crawler"

# Obey robots.txt
ROBOTSTXT_OBEY = True

# Polite crawling: one request at a time, 1-second delay
CONCURRENT_REQUESTS = 1
DOWNLOAD_DELAY = 1.0
RANDOMIZE_DOWNLOAD_DELAY = True

# Disable cookies (not needed for this API)
COOKIES_ENABLED = False

# Timeout
DOWNLOAD_TIMEOUT = 30

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Default headers
DEFAULT_REQUEST_HEADERS = {
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

# Middlewares
DOWNLOADER_MIDDLEWARES = {
    "crawler.middlewares.RandomUserAgentMiddleware": 400,
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 550,
    "scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware": 810,
}

# Item pipelines
ITEM_PIPELINES = {
    "crawler.pipelines.WeatherSQLitePipeline": 300,
}

# Logging
LOG_LEVEL = "INFO"

# Feed exports (optional, kept off by default)
FEEDS = {}

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
