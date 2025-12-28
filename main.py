import requests
import pandas as pd
from datetime import datetime

BASE_URL = "https://indodax.com/api"

# =========================
# AMBIL SEMUA PAIR IDR
# =========================
def get_all_pairs():
    url = f"{BASE_URL}/tickers"
    r = requests.get(url, timeout=10)
    data = r.json()["tickers"]

    pairs = []
    for pair in data.keys():
        if pair.endswith("_idr"):
            pairs.append(pair)

    return pairs

# =========================
# AMBIL DATA CANDLE
# =========================
def get_candles(pair, interval="5m", limit=200):
    url = f"{BASE_URL}/candles"
    params = {
        "pair": pair,
        "interval": interval,
        "limit": limit
    }

    r = requests.get(url, params=params, timeout=10)
    candles = r.json()

    df = pd.DataFrame(candles, columns=[
        "timestamp", "open", "high", "low", "close", "volume"
    ])

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    df[["open","high","low","close","volume"]] = df[["open","high","low","close","volume"]].astype(float)

    return df

# =========================
# TEST DATA
# =========================
def main():
    pairs = get_all_pairs()
    print(f"TOTAL PAIR IDR: {len(pairs)}")

    test_pair = pairs[0]
    print(f"TEST PAIR: {test_pair}")

    df = get_candles(test_pair, "5m")

    print(df.tail())
    print("DATA OK -", datetime.now())

if __name__ == "__main__":
    main()
