# -*- coding: utf-8 -*-
import requests

mirrors = [
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.nchc.org.tw/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
]

headers = {"User-Agent": "GurugramFloodStudy/1.0 (academic research)"}
q = """[out:json][timeout:25];
(
  way["waterway"](28.20,76.80,28.55,77.25);
);
out geom 5;"""

for m in mirrors:
    try:
        r = requests.post(m, data={"data": q}, headers=headers, timeout=20)
        print(f"Mirror: {m} -> {r.status_code}")
        if r.status_code == 200:
            print("Features:", len(r.json().get("elements", [])))
            break
    except Exception as e:
        print(f"Mirror {m} failed: {e}")
