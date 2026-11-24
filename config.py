import os

BASE_URL = os.environ.get(
    "PIZZAEXPRESS_API_URL",
    "https://pizzaexpress-production-11f6.up.railway.app",
).rstrip("/")