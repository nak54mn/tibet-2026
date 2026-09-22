#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每天更新 weather.js：用 Open-Meteo 抓西藏行程各點的預報（含實際海拔）。"""

import json, sys, time, urllib.request
from datetime import datetime, timedelta, timezone

TRIP_START = "2026-09-25"
TRIP_END   = "2026-10-05"
OUT        = "weather.js"
CST        = timezone(timedelta(hours=8))

POINTS = {
    "shanghai":  ("上海",       31.20, 121.47,    5),
    "shuangliu": ("成都雙流",   30.58, 103.95,  500),
    "nyingchi":  ("林芝八一鎮", 29.65,  94.36, 2900),
    "sejila":    ("色季拉山口", 29.60,  94.63, 4728),
    "basongcuo": ("巴松措",     30.01,  93.93, 3480),
    "lhasa":     ("拉薩",       29.65,  91.13, 3650),
    "gangbala":  ("岡巴拉山口", 29.13,  90.60, 4990),
    "karola":    ("卡若拉冰川", 28.90,  90.16, 5020),
    "shigatse":  ("日喀則",     29.27,  88.88, 3840),
    "tingri":    ("定日縣城",   28.66,  87.09, 4300),
    "ebc":       ("珠峰大本營", 28.14,  86.85, 5200),
    "gawula":    ("加烏拉山口", 28.44,  86.87, 5198),
    "damxung":   ("當雄縣城",   30.48,  91.10, 4200),
    "namtso":    ("納木錯",     30.72,  90.90, 4718),
}

WMO = {
    0: "晴", 1: "晴", 2: "多云", 3: "阴",
    45: "雾", 48: "雾",
    51: "毛毛雨", 53: "毛毛雨", 55: "毛毛雨",
    56: "冻雨", 57: "冻雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    66: "冻雨", 67: "冻雨",
    71: "小雪", 73: "中雪", 75: "大雪", 77: "雪粒",
    80: "阵雨", 81: "阵雨", 82: "大阵雨",
    85: "阵雪", 86: "大阵雪",
    95: "雷阵雨", 96: "雷阵雨", 99: "雷阵雨",
}

API = ("https://api.open-meteo.com/v1/forecast"
       "?latitude={lat}&longitude={lon}&elevation={ele}"
       "&daily=weather_code,temperature_2m_max,temperature_2m_min"
       "&timezone=Asia%2FShanghai&forecast_days=16")


def fetch(url, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "tibet-2026/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last = e
            time.sleep(3 * (i + 1))
    print("  失敗：%s" % last)
    return None


def main():
    today = datetime.now(CST).date().isoformat()
    if today > TRIP_END:
        print("行程已結束（%s），不更新。" % today)
        return 0

    cities, ok = {}, 0
    for key, (name, lat, lon, ele) in POINTS.items():
        print("抓 %s (%s)" % (name, key))
        data = fetch(API.format(lat=lat, lon=lon, ele=ele))
        if not data or "daily" not in data:
            continue
        d = data["daily"]
        days = {}
        for i, iso in enumerate(d["time"]):
            if iso < TRIP_START or iso > TRIP_END:
                continue
            hi, lo = d["temperature_2m_max"][i], d["temperature_2m_min"][i]
            if hi is None or lo is None:
                continue
            wx = WMO.get(d["weather_code"][i], "多云")
            days[iso] = {"c": [wx, int(round(hi)), int(round(lo))]}
        if days:
            cities[key] = days
            ok += 1

    if ok < len(POINTS) // 2:
        print("只成功 %d 個點，太少，保留舊檔不更新。" % ok)
        return 1

    try:
        old = open(OUT, encoding="utf-8").read()
        old = json.loads(old[old.index("=") + 1: old.rindex(";")])
        for key, days in old.get("cities", {}).items():
            if key not in cities:
                cities[key] = days
                print("沿用舊資料：%s" % key)
    except Exception:
        pass

    out = {
        "updated": datetime.now(CST).strftime("%-m/%-d %H:%M"),
        "sources": {"c": "Open-Meteo"},
        "cities": cities,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("window.TIBET_WX=" + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print("完成：%d 個點，更新時間 %s" % (ok, out["updated"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
