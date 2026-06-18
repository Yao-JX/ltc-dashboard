# -*- coding: utf-8 -*-
"""
自動下載最新原始資料到 data/raw/ 與 assets/（供 GitHub Actions 每月排程使用）。
- 人口(77132)：自動掃描最新月份
- 其餘來源：重新下載覆蓋；單一來源失敗不影響其他
"""
import os, re, json, glob, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
ASSETS = os.path.join(BASE, "assets")
INST = os.path.join(RAW, "elderly_institutions_8572")
for d in (RAW, ASSETS, INST):
    os.makedirs(d, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0"}

def get(url, headers=None, timeout=120):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    return urllib.request.urlopen(req, timeout=timeout).read()

def save(url, path, headers=None):
    data = get(url, headers, timeout=180)
    with open(path, "wb") as f:
        f.write(data)
    return len(data)

def api_dataset(did):
    return json.loads(get(f"https://data.gov.tw/api/v2/rest/dataset/{did}"))["result"]

def try_step(name, fn):
    try:
        info = fn()
        print(f"[OK] {name} {info or ''}", flush=True)
    except Exception as e:
        print(f"[SKIP] {name} 失敗：{e}（保留既有檔案）", flush=True)

# 1) 人口 77132：並行掃描最新月份
def _probe_ym(url):
    # 只讀前 ~2500 bytes（即使伺服器忽略 Range 也不會整檔下載）；失敗重試 2 次
    for _ in range(3):
        try:
            req = urllib.request.Request(url, headers={**UA, "Range": "bytes=0-2500"})
            with urllib.request.urlopen(req, timeout=25) as r:
                head = r.read(2500).decode("utf-8", "ignore")
            mt = re.search(r"\n(\d{5,6})", head)
            return (int(mt.group(1)), url) if mt else (0, url)
        except Exception:
            continue
    return (0, url)

def dl_population():
    urls = [d["resourceDownloadUrl"] for d in api_dataset(77132)["distribution"]
            if d.get("resourceFormat") == "CSV"]
    with ThreadPoolExecutor(max_workers=20) as ex:
        results = list(ex.map(_probe_ym, urls))
    best_ym, best_url = max(results, key=lambda x: x[0])
    if not best_url or best_ym == 0:
        raise RuntimeError("找不到 77132 任何月份")
    n = save(best_url, os.path.join(RAW, "77132_pop_single_age_latest.csv"))
    return f"期別={best_ym} ({n:,} bytes)"

# 2) 老化指數
def dl_aging():
    n = save("https://www.ris.gov.tw/info-popudata/app/awFastDownload/file/y1s4-00000.xls/y1s4/00000/",
             os.path.join(RAW, "ris_aging_index_by_county.xls"))
    return f"{n:,} bytes"

# 3) 身心障礙（年齡 / 類別）
def dl_disability():
    save("https://www.mohw.gov.tw/dl-69420-9cfd8264-5caf-47f9-b12d-a23c1c9b22a8.html",
         os.path.join(RAW, "disability_by_age_county.xls"), {"Referer": "https://dep.mohw.gov.tw/"})
    save("https://www.mohw.gov.tw/dl-69410-3372b4eb-e96d-4b84-ad30-b9f88d657042.html",
         os.path.join(RAW, "disability_by_type_county.xls"), {"Referer": "https://dep.mohw.gov.tw/"})
    return "2 檔"

# 4) 老人福利機構 8572（22 縣市）
def dl_institutions():
    urls = [d["resourceDownloadUrl"] for d in api_dataset(8572)["distribution"]
            if d.get("resourceFormat") == "CSV"]
    def one(url):
        county = urllib.request.unquote(url.split("/")[-1]).replace("老人福利機構名冊.csv", "")
        save(url, os.path.join(INST, county + ".csv"))
    with ThreadPoolExecutor(max_workers=12) as ex:
        list(ex.map(one, urls))
    return f"{len(urls)} 縣市"

# 5) 長照 PDF（涵蓋率 / ABC據點）
def dl_ltc_pdfs():
    save("https://www.mohw.gov.tw/dl-88608-9d7a650b-ac63-43cb-a469-7d1cb37a2d77.html",
         os.path.join(RAW, "ltc_coverage_rate.pdf"), {"Referer": "https://1966.gov.tw/"})
    save("https://www.mohw.gov.tw/dl-89795-52476cf8-4945-4713-9053-80ea95723d9d.html",
         os.path.join(RAW, "ltc_county_resources.pdf"), {"Referer": "https://1966.gov.tw/"})
    return "2 PDF"

# 6) 縣市界 geojson（變動極少，無則下載）
def dl_geojson():
    p = os.path.join(ASSETS, "tw_counties.json")
    if os.path.exists(p) and os.path.getsize(p) > 100000:
        return "已存在"
    n = save("https://raw.githubusercontent.com/g0v/twgeojson/master/json/twCounty2010.geo.json", p)
    return f"{n:,} bytes"

if __name__ == "__main__":
    try_step("人口(77132)", dl_population)
    try_step("老化指數", dl_aging)
    try_step("身心障礙", dl_disability)
    try_step("老人福利機構(8572)", dl_institutions)
    try_step("長照PDF", dl_ltc_pdfs)
    try_step("縣市界geojson", dl_geojson)
    print("下載完成。")
