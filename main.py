import requests
import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from datetime import datetime
import os

# =========================
# CONFIG
# =========================
BASE_URL = "https://indodax.com/api"
TIMEFRAME = "15m"
CANDLE_LIMIT = 200
MIN_CANDLE = 200
RISK_REWARD_MIN = 4

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# =========================
# TELEGRAM
# =========================
def send_telegram(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Telegram ENV belum ada")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    })

# =========================
# GET PAIRS
# =========================
def get_all_pairs():
    r = requests.get(f"{BASE_URL}/tickers", timeout=10)
    return [p for p in r.json()["tickers"] if p.endswith("_idr")]

# =========================
# GET CANDLES
# =========================
def get_candles(pair):
    r = requests.get(
        f"{BASE_URL}/candles",
        params={"pair": pair, "interval": TIMEFRAME, "limit": CANDLE_LIMIT},
        timeout=10
    )
    data = r.json()
    if not data or len(data) < MIN_CANDLE:
        return None

    df = pd.DataFrame(data, columns=[
        "timestamp","open","high","low","close","volume"
    ])
    df[["open","high","low","close","volume"]] = \
        df[["open","high","low","close","volume"]].astype(float)
    return df

# =========================
# INDICATORS
# =========================
def apply_indicators(df):
    df["ema50"] = EMAIndicator(df["close"], 50).ema_indicator()
    df["ema200"] = EMAIndicator(df["close"], 200).ema_indicator()
    df["rsi"] = RSIIndicator(df["close"], 14).rsi()
    df["atr"] = AverageTrueRange(
        df["high"], df["low"], df["close"], 14
    ).average_true_range()
    df["vol_ma"] = df["volume"].rolling(20).mean()
    df.dropna(inplace=True)
    return df if len(df) > 50 else None

# =========================
# FILTERS
# =========================
def hh_hl(df):
    h = df["high"].iloc[-4:]
    l = df["low"].iloc[-4:]
    return h.iloc[-1] > h.iloc[-2] > h.iloc[-3] and \
           l.iloc[-1] > l.iloc[-2] > l.iloc[-3]

def is_sideways(df):
    return (df["atr"].iloc[-1] / df["close"].iloc[-1]) < 0.002

# =========================
# SIGNAL LOGIC
# =========================
def analyze(pair):
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
        hh_hl(df)
    ]

    if sum(conditions) < 4:
        return None
    if is_sideways(df) or last["rsi"] >= 78:
        return None

    entry = last["close"]
    sl = entry - (last["atr"] * 1.5)
    risk = entry - sl
    tp4 = entry + (risk * 4)

    rr = (tp4 - entry) / risk
    if rr < RISK_REWARD_MIN:
        return None

    return {
        "pair": pair.upper().replace("_", "/"),
        "entry": round(entry, 0),
        "sl": round(sl, 0),
        "tp1": round(entry + risk * 1, 0),
        "tp2": round(entry + risk * 2, 0),
        "tp3": round(entry + risk * 3, 0),
        "tp4": round(tp4, 0),
        "rsi": round(last["rsi"], 2)
    }

# =========================
# MAIN
# =========================
def main():
    pairs = get_all_pairs()
    signals = []

    for pair in pairs:
        try:
            s = analyze(pair)
            if s:
                signals.append(s)
        except:
            pass

    if not signals:
        send_telegram(
            "🚫 *NO TRADE*\n\n"
            "Market belum memenuhi kriteria:\n"
            "- Trend belum valid\n"
            "- Volume lemah / sideways\n"
            "- RR < 1:4\n\n"
            "Timeframe: 15M"
        )
        return

    for s in signals:
        msg = (
            "📈 *SIGNAL BUY*\n"
            f"Pair: {s['pair']}\n"
            f"Entry: {s['entry']}\n"
            f"Stop Loss: {s['sl']}\n\n"
            f"TP1: {s['tp1']}\n"
            f"TP2: {s['tp2']}\n"
            f"TP3: {s['tp3']}\n"
            f"TP4: {s['tp4']} ⭐\n\n"
            "Timeframe: 15M\n"
            "Confidence: HIGH\n"
            f"RSI: {s['rsi']}"
        )
        send_telegram(msg)

if __name__ == "__main__":
    main()
