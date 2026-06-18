# -*- coding: utf-8 -*-
"""解析衛福部長照專區 PDF：服務涵蓋率、ABC據點布建 → CSV。"""
import os, re
import pdfplumber
import pandas as pd

BASE = r"C:\Users\y\03-SQL_Demo\0618"
RAW = os.path.join(BASE, "data", "raw")
OUT = os.path.join(BASE, "data", "processed")

COUNTIES = ["新北市","臺北市","桃園市","臺中市","臺南市","高雄市","宜蘭縣","新竹縣",
            "苗栗縣","彰化縣","南投縣","雲林縣","嘉義縣","屏東縣","臺東縣","花蓮縣",
            "澎湖縣","基隆市","新竹市","嘉義市","金門縣","連江縣"]

def num(s):
    return float(s.replace(",", "").replace("%", ""))

# ---- 涵蓋率 ----
def parse_coverage():
    rows = []
    with pdfplumber.open(os.path.join(RAW, "ltc_coverage_rate.pdf")) as pdf:
        for p in pdf.pages:
            for ln in (p.extract_text() or "").split("\n"):
                t = ln.split()
                if len(t) < 7:
                    continue
                name = "".join(t[:-6])
                if name not in COUNTIES:
                    continue
                a, b, c, d, e, f = t[-6:]
                rows.append({
                    "縣市": name,
                    "長照推估需求人數": int(num(a)),
                    "長照服務使用人數": int(num(e)),
                    "長照服務涵蓋率%": round(num(f), 2),
                    "未滿足需求比例%": round(100 - num(f), 2),
                })
    df = pd.DataFrame(rows).drop_duplicates("縣市")
    df.to_csv(os.path.join(OUT, "ltc_coverage.csv"), index=False, encoding="utf-8-sig")
    print("涵蓋率：", len(df), "縣市")
    return df

# ---- ABC 據點布建 ----
def parse_resources():
    rows = []
    with pdfplumber.open(os.path.join(RAW, "ltc_county_resources.pdf")) as pdf:
        for p in pdf.pages:
            for ln in (p.extract_text() or "").split("\n"):
                t = ln.split()
                if len(t) < 10:
                    continue
                name = "".join(t[:-9])
                if name not in COUNTIES:
                    continue
                v = [num(x) for x in t[-9:]]
                rows.append({
                    "縣市": name,
                    "A整合中心_實際": int(v[1]), "A達成率%": round(v[2], 1),
                    "B特約單位_實際": int(v[4]), "B達成率%": round(v[5], 1),
                    "C巷弄站_實際": int(v[7]), "C達成率%": round(v[8], 1),
                })
    df = pd.DataFrame(rows).drop_duplicates("縣市")
    df.to_csv(os.path.join(OUT, "ltc_resources.csv"), index=False, encoding="utf-8-sig")
    print("ABC據點：", len(df), "縣市")
    return df

if __name__ == "__main__":
    cov = parse_coverage()
    res = parse_resources()
    pd.set_option("display.unicode.east_asian_width", True)
    pd.set_option("display.width", 200)
    print(cov.sort_values("長照服務涵蓋率%").to_string(index=False))
