import requests
import pandas as pd
import numpy as np
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from datetime import datetime

BASE_URL = "https://indodax.com/api"
TIMEFRAME = "5m"
CANDLE_LIMIT = 200

# =========================
# AMBIL SEMUA PAIR IDR
# =========================
def get_all_pairs():
    r = requests.get(f"{BASE_URL}/tickers", timeout=10)
    data = r.json()["tickers"]
    return [pair for pair in data if pair.endswith("_idr")]

# ====
