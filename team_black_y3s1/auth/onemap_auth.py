import os
import requests
from dotenv import load_dotenv

load_dotenv()

ONEMAP_EMAIL = os.getenv("ONEMAP_API_EMAIL")
ONEMAP_PASSWORD = os.getenv("ONEMAP_API_PASSWORD")
ONEMAP_BASE_URL = os.getenv("ONEMAP_BASE_URL")

_token_cache = None


def set_access_token(token):
    global _token_cache
    _token_cache = token


def get_access_token():
    global _token_cache
    if _token_cache:
        return _token_cache

    try:
        response = requests.post(
            f"{ONEMAP_BASE_URL}/api/auth/post/getToken",
            json={"email": ONEMAP_EMAIL, "password": ONEMAP_PASSWORD},
        )
        response.raise_for_status()
        token = response.json()["access_token"]
        set_access_token(token)
        return token
    except Exception as e:
        print("Token fetch failed:", e)
        raise
