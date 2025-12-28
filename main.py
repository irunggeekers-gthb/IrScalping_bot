import requests
import pandas as pd
import numpy as np
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from datetime import datetime

BASE_URL = "https://indodax.com/api"

# =========================
# AMBIL SEMUA PAIR IDR
# =========================
def get_all_pairs():
    r = requests.get(f"{BASE_URL}/tickers", timeout=10)
    data = r.json()["tickers"]
    return [p for p in data.keys() if p.endswith("_idr")]

# =========================
# AMBIL DATA CANDLE
# =========================
def get_candles(pair, interval="5m", limit=200):
    r = requests.get(
        f"{BASE_URL}/candles",
        params={"pair": pair, "interval": interval, "limit": limit},
        timeout=10
    )
    df = pd.DataFrame(r.json(), columns=[
        "timestamp","open","high","low","close","volume"
    ])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    df[["open","high","low","close","volume"]] = df[["open","high","low","close","volume"]].astype(float)
    return df

# =========================
# HITUNG INDIKATOR
# =========================
def apply_indicators(df):
    df["ema50"] = EMAIndicator(df["close"], 50).ema_indicator()
    df["ema200"] = EMAIndicator(df["close"], 200).ema_indicator()
    df["rsi"] = RSIIndicator(df["close"], 14).rsi()
    df["atr"] = AverageTrueRange(
        high=df["high"],
