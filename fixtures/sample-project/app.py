"""Sample app: reads STRIPE_SECRET which is NOT in .env.example (MISSING)."""
import os

API_KEY = os.getenv("API_KEY")
PORT = int(os.environ.get("PORT", "8000"))
STRIPE_SECRET = os.environ["STRIPE_SECRET"]  # <-- missing from .env.example
