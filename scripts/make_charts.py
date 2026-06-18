# -*- coding: utf-8 -*-
"""產出視覺化圖表：缺口排名、老年比例、老化指數趨勢+預測、供需散佈、分縣市地圖。"""
import os, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "output")
os.makedirs(OUT, exist_ok=True)

# 中文字型
FONT = FontProperties(fname=r"C:\Windows\Fonts\msjh.ttc")
plt.rcParams["axes.unicode_minus"] = False
def cjk(ax, title=None, xl=None, yl=None):
    if title: ax.set_title(title, fontproperties=FONT, fontsize=15, fontweight="bold")
    if xl: ax.set_xlabel(xl, fontproperties=FONT, fontsize=11)
    if yl: ax.set_ylabel(yl, fontproperties=FONT, fontsize=11)
    for lab in ax.get_xticklabels() + ax.get_yticklabels():
        lab.set_fontproperties(FONT)

m = pd.read_csv(os.path.join(BASE, "data", "processed", "county_master.csv"))
ts = pd.read_csv(os.path.join(BASE, "data", "processed", "aging_index_timeseries.csv"))
fc = pd.read_csv(os.path.join(BASE, "data", "processed", "forecast_aging_index.csv"))

# ---- 圖1 每千名老人核定床數 缺口排名 ----
d = m.sort_values("每千名老人核定床數")
fig, ax = plt.subplots(figsize=(10, 8))
colors = ["#d62728" if v < 0 else "#2ca02c" for v in d["床數供需指數_對中位數%"]]
ax.barh(d["縣市"], d["每千名老人核定床數"], color=colors)
ax.axvline(m["每千名老人核定床數"].median(), color="gray", ls="--", lw=1)
ax.text(m["每千名老人核定床數"].median(), -0.8, "全國中位數", fontproperties=FONT, color="gray", fontsize=9)
for i, v in enumerate(d["每千名老人核定床數"]):
    ax.text(v + 0.2, i, f"{v:.1f}", fontproperties=FONT, va="center", fontsize=9)
cjk(ax, "各縣市每千名老人核定床數（紅=供給低於中位數）", "每千名 65 歲以上人口之核定床數")
plt.tight_layout(); plt.savefig(os.path.join(OUT, "01_bed_gap_ranking.png"), dpi=130); plt.close()

# ---- 圖2 老年人口比例 ----
d = m.sort_values("老年人口比例%", ascending=True)
fig, ax = plt.subplots(figsize=(10, 8))
ax.barh(d["縣市"], d["老年人口比例%"], color="#1f77b4")
ax.axvline(20, color="red", ls="--", lw=1); ax.text(20.1, 0, "超高齡(20%)", fontproperties=FONT, color="red", fontsize=9)
ax.axvline(14, color="orange", ls="--", lw=1); ax.text(14.1, 0, "高齡(14%)", fontproperties=FONT, color="orange", fontsize=9)
for i, v in enumerate(d["老年人口比例%"]):
    ax.text(v + 0.1, i, f"{v:.1f}%", fontproperties=FONT, va="center", fontsize=9)
cjk(ax, "各縣市老年人口（65+）比例（2025）", "佔總人口比例 %")
plt.tight_layout(); plt.savefig(os.path.join(OUT, "02_elderly_ratio.png"), dpi=130); plt.close()

# ---- 圖3 老化指數趨勢 + 預測（代表性縣市）----
reps = ["臺北市", "新北市", "桃園市", "嘉義縣", "南投縣", "新竹市"]
fig, ax = plt.subplots(figsize=(11, 7))
cmap = plt.cm.tab10
for i, c in enumerate(reps):
    a = ts[ts["縣市"] == c].sort_values("年_西元")
    f = fc[fc["縣市"] == c].sort_values("年_西元")
    col = cmap(i)
    ax.plot(a["年_西元"], a["老化指數"], "-o", color=col, ms=3, label=c)
    if len(a) and len(f):
        ax.plot([a["年_西元"].iloc[-1]] + list(f["年_西元"]),
                [a["老化指數"].iloc[-1]] + list(f["老化指數_預測"]), "--", color=col, lw=1.5)
ax.axhline(100, color="gray", ls=":", lw=1); ax.text(2010, 103, "老化指數=100（老年=幼年）", fontproperties=FONT, color="gray", fontsize=9)
ax.axvspan(2026, 2030, color="orange", alpha=0.08)
ax.text(2027.5, ax.get_ylim()[1]*0.05, "預測", fontproperties=FONT, color="orange", fontsize=11)
leg = ax.legend(prop=FONT, ncol=3, loc="upper left")
cjk(ax, "代表縣市老化指數趨勢 2010–2025 與預測 2026–2030", "西元年", "老化指數（老年/幼年×100）")
plt.tight_layout(); plt.savefig(os.path.join(OUT, "03_aging_trend_forecast.png"), dpi=130); plt.close()

# ---- 圖4 供需散佈：老年人口 vs 核定床數 ----
fig, ax = plt.subplots(figsize=(10, 8))
x = m["老年人口_65歲以上"]; y = m["核定床數"]
ax.scatter(x, y, s=m["總人口"]/8000, c=m["每千名老人核定床數"], cmap="RdYlGn", edgecolor="k", alpha=0.85)
# 中位供給比參考線
med = m["每千名老人核定床數"].median()
xs = np.linspace(x.min(), x.max(), 50)
ax.plot(xs, med*xs/1000, "--", color="gray", lw=1, label=f"中位供給比 {med:.1f}床/千人")
for _, r in m.iterrows():
    ax.annotate(r["縣市"], (r["老年人口_65歲以上"], r["核定床數"]), fontproperties=FONT, fontsize=8,
                xytext=(3,3), textcoords="offset points")
ax.legend(prop=FONT)
cjk(ax, "長照供需散佈（點大小=總人口，顏色=每千名老人床數）", "老年人口 65 歲以上（人）", "核定床數")
plt.tight_layout(); plt.savefig(os.path.join(OUT, "04_supply_demand_scatter.png"), dpi=130); plt.close()

# ---- 圖5/6 分縣市地圖（choropleth）----
geo = json.load(open(os.path.join(BASE, "assets", "tw_counties.json"), encoding="utf-8"))
def norm_name(n):
    n = n.replace("台", "臺")
    return {"桃園縣": "桃園市"}.get(n, n)

def draw_map(value_col, title, fname, cmap_name, reverse=False):
    vals = m.set_index("縣市")[value_col]
    vmin, vmax = vals.min(), vals.max()
    norm = Normalize(vmin, vmax)
    cmap = plt.get_cmap(cmap_name + ("_r" if reverse else ""))
    fig, ax = plt.subplots(figsize=(8, 10))
    for feat in geo["features"]:
        name = norm_name(feat["properties"]["COUNTYNAME"])
        v = vals.get(name, np.nan)
        color = cmap(norm(v)) if pd.notna(v) else "#dddddd"
        geom = feat["geometry"]; polys = []
        if geom["type"] == "Polygon": polys = [geom["coordinates"]]
        elif geom["type"] == "MultiPolygon": polys = geom["coordinates"]
        for poly in polys:
            ring = np.array(poly[0])
            ax.add_patch(MplPolygon(ring, closed=True, facecolor=color, edgecolor="white", lw=0.4))
    # 標註本島縣市名
    for feat in geo["features"]:
        name = norm_name(feat["properties"]["COUNTYNAME"])
        geom = feat["geometry"]
        pts = np.vstack([np.array(p[0]) for p in (geom["coordinates"] if geom["type"]=="MultiPolygon" else [geom["coordinates"]])])
        cx, cy = pts[:,0].mean(), pts[:,1].mean()
        if 119.5 < cx < 122.1 and 21.8 < cy < 25.4:
            ax.text(cx, cy, name, fontproperties=FONT, fontsize=7, ha="center", va="center")
    ax.set_xlim(118.0, 122.1); ax.set_ylim(21.8, 25.4); ax.set_aspect("equal"); ax.axis("off")
    sm = ScalarMappable(norm=norm, cmap=cmap); sm.set_array([])
    cb = fig.colorbar(sm, ax=ax, fraction=0.035, pad=0.02)
    for lab in cb.ax.get_yticklabels(): lab.set_fontproperties(FONT)
    ax.set_title(title, fontproperties=FONT, fontsize=15, fontweight="bold")
    plt.tight_layout(); plt.savefig(os.path.join(OUT, fname), dpi=130); plt.close()

draw_map("老年人口比例%", "各縣市老年人口比例（2025）", "05_map_elderly_ratio.png", "OrRd")
draw_map("每千名老人核定床數", "各縣市每千名老人核定床數（綠=充足 紅=不足）", "06_map_bed_supply.png", "RdYlGn")

# ---- 圖7 2030 床位缺口 ----
dem = pd.read_csv(os.path.join(BASE, "data", "processed", "forecast_bed_demand_2030.csv"))
d = dem.sort_values("2030床位缺口")
fig, ax = plt.subplots(figsize=(10, 8))
colors = ["#2ca02c" if v <= 0 else "#d62728" for v in d["2030床位缺口"]]
ax.barh(d["縣市"], d["2030床位缺口"], color=colors)
ax.axvline(0, color="k", lw=0.8)
for i, v in enumerate(d["2030床位缺口"]):
    ax.text(v + (60 if v >= 0 else -60), i, f"{v:+,}", fontproperties=FONT, va="center",
            ha="left" if v >= 0 else "right", fontsize=8)
cjk(ax, "2030 年床位缺口推估（維持全國中位服務水準；紅=需擴充）", "需新增床數（正值=不足）")
plt.tight_layout(); plt.savefig(os.path.join(OUT, "07_bed_demand_gap_2030.png"), dpi=130); plt.close()

# ---- 圖8 長照服務涵蓋率排名（真實供需缺口）----
if "長照服務涵蓋率%" in m.columns:
    d = m.sort_values("長照服務涵蓋率%")
    fig, ax = plt.subplots(figsize=(10, 8))
    colors = ["#d62728" if v < 80 else ("#ff7f0e" if v < 100 else "#2ca02c") for v in d["長照服務涵蓋率%"]]
    ax.barh(d["縣市"], d["長照服務涵蓋率%"], color=colors)
    ax.axvline(100, color="green", ls="--", lw=1); ax.axvline(80, color="red", ls=":", lw=1)
    for i, v in enumerate(d["長照服務涵蓋率%"]):
        ax.text(v + 1, i, f"{v:.0f}%", fontproperties=FONT, va="center", fontsize=9)
    cjk(ax, "各縣市長照服務涵蓋率（以失能推估需求為分母；紅<80%＝未滿足高）", "涵蓋率 %（服務人數/長照需求人數）")
    plt.tight_layout(); plt.savefig(os.path.join(OUT, "08_coverage_rate_ranking.png"), dpi=130); plt.close()

    # ---- 圖9 涵蓋率地圖 ----
    draw_map("長照服務涵蓋率%", "各縣市長照服務涵蓋率（紅=未滿足高 綠=已滿足）", "09_map_coverage_rate.png", "RdYlGn")

# ---- 圖10 兩種觀點對照：床位密度排名 vs 涵蓋率排名 ----
cmp_path = os.path.join(BASE, "data", "processed", "risk_comparison.csv")
if os.path.exists(cmp_path):
    cmp = pd.read_csv(cmp_path)
    fig, ax = plt.subplots(figsize=(9, 9))
    ax.scatter(cmp["床位密度缺口排名(舊)"], cmp["涵蓋率缺口排名"], s=60, color="#1f77b4")
    for _, r in cmp.iterrows():
        ax.annotate(r["縣市"], (r["床位密度缺口排名(舊)"], r["涵蓋率缺口排名"]),
                    fontproperties=FONT, fontsize=8, xytext=(4, 2), textcoords="offset points")
    ax.plot([1, 22], [1, 22], "--", color="gray", lw=1)
    ax.set_xlim(0, 23); ax.set_ylim(0, 23)
    cjk(ax, "兩種缺口觀點對照（左下=兩者皆危險；偏離對角線=結論不同）",
        "床位密度缺口排名（舊，1=最不足）", "涵蓋率缺口排名（1=最未滿足）")
    plt.tight_layout(); plt.savefig(os.path.join(OUT, "10_rank_comparison.png"), dpi=130); plt.close()

# ---- 圖11 多維度脆弱度指數排名 ----
if "脆弱度指數" in m.columns:
    d = m.sort_values("脆弱度指數")
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(d["縣市"], d["脆弱度指數"], color=plt.cm.RdYlGn_r((d["脆弱度指數"]-d["脆弱度指數"].min())/(d["脆弱度指數"].max()-d["脆弱度指數"].min())))
    ax.axvline(0, color="k", lw=0.8)
    cjk(ax, "多維度脆弱度指數（未滿足需求＋深度老化＋整合資源不足；越右越需關注）", "脆弱度指數 (z-score 平均)")
    plt.tight_layout(); plt.savefig(os.path.join(OUT, "11_vulnerability_index.png"), dpi=130); plt.close()

print("已輸出圖表至 output/：")
for f in sorted(os.listdir(OUT)):
    print("  ", f)
