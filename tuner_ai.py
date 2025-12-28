import json

stats = json.load(open("stats.json"))
tuner = json.load(open("tuner.json"))

win = stats["win"]
loss = stats["loss"]

if win + loss < 10:
    exit()

wr = win / (win + loss) * 100

if wr < 75:
    tuner["rsi_low"] += 1
    tuner["rsi_high"] -= 1
    tuner["atr_mult"] = min(2.0, tuner["atr_mult"] + 0.1)
    tuner["volume_mult"] += 0.1

json.dump(tuner, open("tuner.json", "w"), indent=2)
