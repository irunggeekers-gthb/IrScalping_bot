import json, os, requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

stats = json.load(open("stats.json"))

win = stats["win"]
loss = stats["loss"]
total = stats["total"]

wr = round((win/(win+loss))*100,2) if win+loss>0 else 0

msg = f"""📊 *LAPORAN MINGGUAN*

Total Signal: {total}
WIN: {win}
LOSS: {loss}
WINRATE: {wr}%
"""

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
)
