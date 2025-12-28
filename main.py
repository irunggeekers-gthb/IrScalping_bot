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

# =========================
# AMBIL DATA CANDLE
# =========================
def get_candles(pair):
    r = requests.get(
        f"{BASE_URL}/candles",
        params={
            "pair": pair,
            "interval": TIMEFRAME,
            "limit": CANDLE_LIMIT
        },
        timeout=10
    )

    df = pd.DataFrame(
        r.json(),
        columns=["timestamp", "open", "high", "low", "close", "volume"]
    )

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    df[["open", "high", "low", "close", "volume"]] = \
        df[["open", "high", "low", "close", "volume"]].astype(float)

    return df

# =========================
# INDIKATOR TEKNIKAL
# =========================
def apply_indicators(df):
    df["ema50"] = EMAIndicator(df["close"], 50).ema_indicator()
    df["ema200"] = EMAIndicator(df["close"], 200).ema_indicator()
    df["rsi"] = RSIIndicator(df["close"], 14).rsi()

    atr_indicator = AverageTrueRange(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        window=14
    )
    df["atr"] = atr_indicator.average_true_range()

    df["vol_ma"] = df["volume"].rolling(20).mean()
    return df

# =========================
# MARKET STRUCTURE HH HL
# =========================
def is_higher_high_higher_low(df):
    highs = df["high"].iloc[-5:]
    lows = df["low"].iloc[-5:]

    return (
        highs.iloc[-1] > highs.iloc[-2] > highs.iloc[-3] and
        lows.iloc[-1] > lows.iloc[-2] > lows.iloc[-3]
    )

# =========================
# SIDEWAYS FILTER
# =========================
def is_sideways(df):
    atr = df["atr"].iloc[-1]
    price = df["close"].iloc[-1]
    return (atr / price) < 0.002  # range terlalu sempit

# =========================
# ANALISA SINYAL
# =========================
def analyze_pair(pair):
    df = get_candles(pair)
    df = apply_indicators(df)

    last = df.iloc[-1]

    conditions = {
        "trend": last["ema50"] > last["ema200"],
        "price_above_ema": last["close"] > last["ema50"],
        "rsi_ok": 55 <= last["rsi"] <= 70,
        "volume_ok": last["volume"] > last["vol_ma"],
        "structure": is_higher_high_higher_low(df)
    }

    score = sum(conditions.values())

    sideways = is_sideways(df)
    rsi_extreme = last["rsi"] >= 78

    return {
        "pair": pair,
        "score": score,
        "conditions": conditions,
        "sideways": sideways,
        "rsi": round(last["rsi"], 2),
        "ema50": round(last["ema50"], 2),
        "ema200": round(last["ema200"], 2),
        "atr": round(last["atr"], 2),
        "price": last["close"],
        "valid": score >= 4 and not sideways and not rsi_extreme
    }

# =========================
# MAIN
# =========================
def main():
    pairs = get_all_pairs()
    print(f"TOTAL PAIR IDR: {len(pairs)}")

    valid_signals = []

    for pair in pairs:
        try:
            result = analyze_pair(pair)
            if result["valid"]:
                valid_signals.append(result)
                print(f"✅ POTENSI SIGNAL: {pair} | SCORE {result['score']}")
        except Exception as e:
            print(f"❌ ERROR {pair}: {e}")

    print("=" * 50)
    print(f"TOTAL POTENSI SIGNAL: {len(valid_signals)}")
    print("SELESAI -", datetime.now())

if __name__ == "__main__":
    main()
