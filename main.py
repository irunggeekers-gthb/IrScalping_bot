import requests, os, json
import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from datetime import datetime

BASE = "https://indodax.com/api"
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

TF_ENTRY = "15m"
TF_TREND = "1h"
LIMIT = 200

STATE_FILE = "state.json"
STATS_FILE = "stats.json"
TUNER_FILE = "tuner.json"

# ================= UTIL =================
def load_json(f, d):
    try:
        return json.load(open(f))
    except:
        return d

def save_json(f, d):
    json.dump(d, open(f, "w"), indent=2)

def send_telegram(msg):
    if BOT_TOKEN and CHAT_ID:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        )

# ================= DATA =================
def get_pairs():
    return [p for p in requests.get(f"{BASE}/tickers").json()["tickers"] if p.endswith("_idr")]

def get_candles(pair, tf):
    r = requests.get(f"{BASE}/candles", params={"pair": pair, "interval": tf, "limit": LIMIT})
    d = r.json()
    if not d or len(d) < LIMIT:
        return None
    df = pd.DataFrame(d, columns=["t","o","h","l","c","v"])
    df[["o","h","l","c","v"]] = df[["o","h","l","c","v"]].astype(float)
    return df

# ================= INDICATORS =================
def indicators(df):
    df["ema50"] = EMAIndicator(df["c"], 50).ema_indicator()
    df["ema200"] = EMAIndicator(df["c"], 200).ema_indicator()
    df["rsi"] = RSIIndicator(df["c"], 14).rsi()
    df["atr"] = AverageTrueRange(df["h"], df["l"], df["c"], 14).average_true_range()
    df["vol_ma"] = df["v"].rolling(20).mean()
    df.dropna(inplace=True)
    return df if len(df) > 50 else None

# ================= FILTER =================
def hh_hl(df):
    return (
        df["h"].iloc[-1] > df["h"].iloc[-2] > df["h"].iloc[-3] and
        df["l"].iloc[-1] > df["l"].iloc[-2] > df["l"].iloc[-3]
    )

# ================= ANALYZE =================
def analyze(pair):
    tuner = load_json(TUNER_FILE, {})
    state = load_json(STATE_FILE, {})

    if state.get(pair) == "ACTIVE":
        return None

    df_trend = indicators(get_candles(pair, TF_TREND))
    if df_trend is None:
        return None
    if df_trend.iloc[-1]["ema50"] <= df_trend.iloc[-1]["ema200"]:
        state[pair] = "RESET"
        save_json(STATE_FILE, state)
        return None

    df = indicators(get_candles(pair, TF_ENTRY))
    if df is None:
        return None

    last = df.iloc[-1]

    cond = [
        last["ema50"] > last["ema200"],
        last["c"] > last["ema50"],
        tuner["rsi_low"] <= last["rsi"] <= tuner["rsi_high"],
        last["v"] > last["vol_ma"] * tuner["volume_mult"],
        hh_hl(df)
    ]

    if sum(cond) < 4:
        return None

    if (last["atr"] / last["c"]) < tuner["sideways_ratio"]:
        return None

    entry = last["c"]
    sl = entry - last["atr"] * tuner["atr_mult"]
    risk = entry - sl
    tp4 = entry + risk * 4

    if (tp4 - entry) / risk < 4:
        return None

    state[pair] = "ACTIVE"
    save_json(STATE_FILE, state)

    stats = load_json(STATS_FILE, {"total":0,"win":0,"loss":0,"signals":[]})
    stats["total"] += 1
    stats["signals"].append({
        "pair": pair,
        "time": str(datetime.now()),
        "entry": entry,
        "sl": sl,
        "tp4": tp4,
        "status": "OPEN"
    })
    save_json(STATS_FILE, stats)

    return {
        "pair": pair.upper().replace("_","/"),
        "entry": round(entry),
        "sl": round(sl),
        "tp1": round(entry+risk),
        "tp2": round(entry+risk*2),
        "tp3": round(entry+risk*3),
        "tp4": round(tp4),
        "rsi": round(last["rsi"],2)
    }

# ================= MAIN =================
def main():
    signals = []
    for p in get_pairs():
        try:
            s = analyze(p)
            if s:
                signals.append(s)
        except:
            pass

    if not signals:
        send_telegram("🚫 *NO TRADE*\nFilter ELITE aktif\nTF: 15M")
        return

    for s in signals:
        send_telegram(
            f"📈 *SIGNAL BUY*\n"
            f"Pair: {s['pair']}\n"
            f"Entry: {s['entry']}\n"
            f"SL: {s['sl']}\n\n"
            f"TP1: {s['tp1']}\nTP2: {s['tp2']}\nTP3: {s['tp3']}\nTP4: {s['tp4']} ⭐\n\n"
            f"TF: 15M\nConfidence: HIGH\nRSI: {s['rsi']}"
        )

if __name__ == "__main__":
    main()
