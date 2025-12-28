import requests
import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from datetime import datetime

BASE_URL = "https://indodax.com/api"
TIMEFRAME = "5m"
CANDLE_LIMIT = 200
MIN_CANDLE = 200

# =========================
# GET ALL IDR PAIRS
# =========================
def get_all_pairs():
    r = requests.get(f"{BASE_URL}/tickers", timeout=10)
    data = r.json().get("tickers", {})
    return [p for p in data if p.endswith("_idr")]

# =========================
# GET CANDLES (SAFE)
# =========================
def get_candles(pair):
    r = requests.get(
        f"{BASE_URL}/candles",
        params={"pair": pair, "interval": TIMEFRAME, "limit": CANDLE_LIMIT},
        timeout=10
    )

    data = r.json()

    # ❌ jika data kosong
    if not data or len(data) < MIN_CANDLE:
        return None

    df = pd.DataFrame(
        data,
        columns=["timestamp", "open", "high", "low", "close", "volume"]
    )

    df[["open","high","low","close","volume"]] = \
        df[["open","high","low","close","volume"]].astype(float)

    return df

# =========================
# APPLY INDICATORS (SAFE)
# =========================
def apply_indicators(df):
    df["ema50"] = EMAIndicator(df["close"], 50).ema_indicator()
    df["ema200"] = EMAIndicator(df["close"], 200).ema_indicator()
    df["rsi"] = RSIIndicator(df["close"], 14).rsi()

    atr = AverageTrueRange(
        df["high"], df["low"], df["close"], 14
    ).average_true_range()

    df["atr"] = atr
    df["vol_ma"] = df["volume"].rolling(20).mean()

    df = df.dropna()

    if len(df) < 50:
        return None

    return df

# =========================
# MARKET STRUCTURE
# =========================
def higher_high_higher_low(df):
    h = df["high"].iloc[-4:]
    l = df["low"].iloc[-4:]
    return h.iloc[-1] > h.iloc[-2] > h.iloc[-3] and \
           l.iloc[-1] > l.iloc[-2] > l.iloc[-3]

# =========================
# SIDEWAYS FILTER
# =========================
def is_sideways(df):
    atr = df["atr"].iloc[-1]
    price = df["close"].iloc[-1]
    return (atr / price) < 0.002

# =========================
# ANALYZE PAIR
# =========================
def analyze_pair(pair):
    df = get_candles(pair)
    if df is None:
        return None

    df = apply_indicators(df)
    if df is None:
        return None

    last = df.iloc[-1]

    conditions = [
        last["ema50"] > last["ema200"],
        last["close"] > last["ema50"],
        55 <= last["rsi"] <= 70,
        last["volume"] > last["vol_ma"],
        higher_high_higher_low(df)
    ]

    score = sum(conditions)

    if is_sideways(df):
        return None

    if last["rsi"] >= 78:
        return None

    if score >= 4:
        return {
            "pair": pair,
            "price": last["close"],
            "ema50": last["ema50"],
            "ema200": last["ema200"],
            "rsi": round(last["rsi"], 2),
            "atr": last["atr"],
            "score": score
        }

    return None

# =========================
# MAIN
# =========================
def main():
    pairs = get_all_pairs()
    print(f"TOTAL PAIR IDR: {len(pairs)}")

    signals = []

    for pair in pairs:
        try:
            result = analyze_pair(pair)
            if result:
                signals.append(result)
                print(f"✅ SIGNAL VALID: {pair} | SCORE {result['score']}")
        except Exception as e:
            print(f"❌ SKIP {pair}: {e}")

    print("=" * 50)
    print(f"TOTAL POTENSI SIGNAL: {len(signals)}")
    print("SELESAI -", datetime.now())

if __name__ == "__main__":
    main()
