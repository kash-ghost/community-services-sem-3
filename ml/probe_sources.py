# -*- coding: utf-8 -*-
import requests

def test_sources():
    # 1. Test Overpass with User-Agent
    headers = {"User-Agent": "GurugramFloodStudy/1.0 (academic research)"}
    q = "[out:json][timeout:30];(way[\"waterway\"](28.20,76.80,28.55,77.25););out geom 10;"
    try:
        r = requests.post("https://overpass-api.de/api/interpreter", data={"data": q}, headers=headers, timeout=30)
        print("OVERPASS STATUS:", r.status_code)
        if r.status_code == 200:
            print("OVERPASS COUNT:", len(r.json().get("elements", [])))
    except Exception as e:
        print("OVERPASS ERROR:", e)

    # 2. Test ESA WorldCover tile URLs
    urls = [
        "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N27E075_Map.tif",
        "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_v200_2021_N27E075_Map.tif",
        "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v100/2020/map/ESA_WorldCover_10m_2020_v100_N27E075_Map.tif",
        "https://zenodo.org/record/7254221/files/ESA_WorldCover_10m_2021_v200_N27E075_Map.tif",
        "https://esa-worldcover.s3.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N27E075_Map.tif",
    ]
    for u in urls:
        try:
            head = requests.head(u, timeout=10)
            print(f"URL: {u} -> {head.status_code}")
        except Exception as e:
            print(f"URL: {u} -> ERR: {e}")

if __name__ == "__main__":
    test_sources()
