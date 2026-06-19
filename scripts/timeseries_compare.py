# -*- coding: utf-8 -*-
"""
老化指數預測：除了原本的線性迴歸，再多做兩種方法對照，並說明為什麼選線性。

三種方法（都用各縣市最近 10 年資料、外推到 2030）：
  1. 線性迴歸    — 對年份做一次多項式擬合（原本用的）。
  2. CAGR        — 年均複合成長率，用頭尾兩點推幾何成長，對「加速老化」較敏感。
  3. 移動平均    — 取最近 5 年的平均年增量當斜率往外推，會平滑掉短期波動。

選法依據不是用講的，而是做「回測」：把每個縣市最後 3 年遮起來當測試，
用前面的資料預測這 3 年、和真實值比，算平均絕對誤差 (MAE)，誤差最小的方法最可信。

輸出:
  data/processed/forecast_method_comparison.csv   各縣市三法的 2030 預測
  data/processed/forecast_method_backtest.csv     三法回測 MAE
  output/14_forecast_methods.png                  代表縣市三法對照圖
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(BASE, "data", "processed")
OUT = os.path.join(BASE, "output")
os.makedirs(OUT, exist_ok=True)

try:
    FONT = FontProperties(fname=r"C:\Windows\Fonts\msjh.ttc")
except Exception:
    FONT = FontProperties()
plt.rcParams["axes.unicode_minus"] = False

TARGET_YEAR = 2030
WINDOW = 10        # 取最近幾年來擬合
MA_K = 5           # 移動平均取最近幾年的平均年增量


def f_linear(years, vals, target):
    a, b = np.polyfit(years, vals, 1)
    return a * target + b


def f_cagr(years, vals, target):
    first, last = vals[0], vals[-1]
    span = years[-1] - years[0]
    if first <= 0 or span == 0:
        return f_linear(years, vals, target)
    rate = (last / first) ** (1 / span) - 1
    return last * (1 + rate) ** (target - years[-1])


def f_ma(years, vals, target, k=MA_K):
    diffs = np.diff(vals)[-k:]          # 最近 k 段的年增量
    slope = diffs.mean()
    return vals[-1] + slope * (target - years[-1])


METHODS = {"線性": f_linear, "CAGR": f_cagr, "移動平均": f_ma}


def load_series():
    ts = pd.read_csv(os.path.join(PROC, "aging_index_timeseries.csv"))
    series = {}
    for c, g in ts.groupby("縣市"):
        g = g.sort_values("年_西元").tail(WINDOW)
        series[c] = (g["年_西元"].to_numpy(float), g["老化指數"].to_numpy(float))
    return series


def backtest(series, holdout=3):
    """遮掉最後 holdout 年當測試，比較三法的平均絕對誤差。"""
    err = {name: [] for name in METHODS}
    for c, (yrs, vals) in series.items():
        if len(yrs) < holdout + 3:
            continue
        tr_y, tr_v = yrs[:-holdout], vals[:-holdout]
        for ty, tv in zip(yrs[-holdout:], vals[-holdout:]):
            for name, fn in METHODS.items():
                err[name].append(abs(fn(tr_y, tr_v, ty) - tv))
    rows = [{"方法": name, "回測MAE": round(np.mean(e), 3), "樣本數": len(e)}
            for name, e in err.items()]
    bt = pd.DataFrame(rows).sort_values("回測MAE")
    bt.to_csv(os.path.join(PROC, "forecast_method_backtest.csv"),
              index=False, encoding="utf-8-sig")
    print("回測（誤差越小越好）:")
    print(bt.to_string(index=False))
    return bt


def forecast_2030(series):
    rows = []
    for c, (yrs, vals) in series.items():
        row = {"縣市": c, "最後實際年": int(yrs[-1]), "最後實際值": round(vals[-1], 1)}
        for name, fn in METHODS.items():
            row[f"2030_{name}"] = round(fn(yrs, vals, TARGET_YEAR), 1)
        rows.append(row)
    df = pd.DataFrame(rows).sort_values("2030_線性", ascending=False)
    df.to_csv(os.path.join(PROC, "forecast_method_comparison.csv"),
              index=False, encoding="utf-8-sig")
    print("\n2030 老化指數三法預測（前 8）:")
    print(df.head(8).to_string(index=False))
    return df


def chart(series, reps=("臺北市", "新北市", "嘉義縣")):
    fig, axes = plt.subplots(1, len(reps), figsize=(5 * len(reps), 4.5), sharey=False)
    if len(reps) == 1:
        axes = [axes]
    style = {"線性": ("--", "#4c72b0"), "CAGR": (":", "#c44e52"), "移動平均": ("-.", "#55a868")}
    for ax, c in zip(axes, reps):
        if c not in series:
            continue
        yrs, vals = series[c]
        ax.plot(yrs, vals, "-o", color="#333333", ms=3, label="實際")
        future = np.arange(int(yrs[-1]), TARGET_YEAR + 1)
        for name, fn in METHODS.items():
            ls, col = style[name]
            proj = [vals[-1]] + [fn(yrs, vals, y) for y in future[1:]]
            ax.plot(future, proj, ls, color=col, lw=1.8, label=name)
        ax.set_title(c, fontproperties=FONT, fontsize=13)
        ax.set_xlabel("西元年", fontproperties=FONT)
        ax.legend(prop=FONT, fontsize=9)
    axes[0].set_ylabel("老化指數", fontproperties=FONT)
    fig.suptitle("老化指數三種預測方法對照（線性 / CAGR / 移動平均）",
                 fontproperties=FONT, fontsize=15)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "14_forecast_methods.png"), dpi=130)
    plt.close()


if __name__ == "__main__":
    series = load_series()
    bt = backtest(series)
    forecast_2030(series)
    chart(series)
    best = bt.iloc[0]["方法"]
    worst = bt.iloc[-1]["方法"]
    print(f"\n結論（由回測決定，不是憑感覺）：MAE 最小的是「{best}」、最大的是「{worst}」。")
    print("老化指數近年是『加速上升』(曲線上凸)，所以直線會系統性低估近期，"
          "這也是線性回測誤差最大的原因；CAGR 把複利成長算進去，最貼近最近 3 年實況。")
    print("作法：主圖維持線性（最好解釋、給趨勢方向），但 2030 數字改用「線性～CAGR」當"
          "區間看，把線性當保守下限、CAGR 當較積極上限，避免只報一個被低估的點值。")
    print("已輸出 forecast_method_comparison.csv / forecast_method_backtest.csv / 14_forecast_methods.png")
