import os

API_PORT = os.environ.get("PIZZAEXPRESS_PORT", "8001")

BASE_URL = os.environ.get(
    "PIZZAEXPRESS_API_URL",
    "https://ranking-drinkable-blouse.ngrok-free.dev",
).rstrip("/")