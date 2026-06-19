# -*- coding: utf-8 -*-
"""
把「縣市是否長照供給不足」做成一個二元分類問題。

標籤：長照服務涵蓋率 < 80% 視為「供給不足」(1)，其餘為 0。
      （80% 是「未滿足需求 > 兩成」的分界，比用中位數切更有政策意義。）
特徵：刻意只用「跟涵蓋率沒有直接關係」的人口/供給結構欄位，避免資料洩漏
      （不能拿未滿足比例、脆弱度這種本來就由涵蓋率算出來的欄位當特徵）。

比較邏輯迴歸 / 決策樹 / 隨機森林三種模型的準確率，並看特徵重要度。
資料只有 22 個縣市，樣本很少，所以用 5-fold 交叉驗證評估，結論當「方法示範」看。

輸出:
  output/12_model_comparison.png
  output/13_feature_importance.png
  data/processed/ml_model_scores.csv
  data/processed/ml_feature_importance.csv
  data/processed/ml_predictions.csv
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_val_score

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(BASE, "data", "processed")
OUT = os.path.join(BASE, "output")
os.makedirs(OUT, exist_ok=True)

try:
    FONT = FontProperties(fname=r"C:\Windows\Fonts\msjh.ttc")
except Exception:
    FONT = FontProperties()
plt.rcParams["axes.unicode_minus"] = False

COVERAGE_GAP_THRESHOLD = 80      # 涵蓋率低於此值 = 供給不足

FEATURES = [
    "老年人口比例%",
    "高齡人口比例%",
    "每千名老人核定床數",
    "每千名老人機構數",
    "A達成率%",
    "身障老人占比%",
]


def load_dataset():
    m = pd.read_csv(os.path.join(PROC, "county_master.csv"))
    # 身障老人占比 = 65 歲以上身障人數 / 65 歲以上人口
    m["身障老人占比%"] = (m["身障65歲以上"] / m["老年人口_65歲以上"] * 100).round(2)
    m["供給不足"] = (m["長照服務涵蓋率%"] < COVERAGE_GAP_THRESHOLD).astype(int)
    data = m.dropna(subset=FEATURES + ["供給不足"]).copy()
    X = data[FEATURES].astype(float)
    y = data["供給不足"]
    print(f"樣本數 {len(data)}；供給不足 {y.sum()} 個、供給尚可 {(y == 0).sum()} 個")
    print("供給不足縣市:", ", ".join(data.loc[y == 1, "縣市"]))
    return data, X, y


def evaluate_models(X, y):
    models = {
        "邏輯迴歸": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)),
        "決策樹": DecisionTreeClassifier(max_depth=3, random_state=0),
        "隨機森林": RandomForestClassifier(n_estimators=300, random_state=0),
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
    rows = []
    for name, model in models.items():
        scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy")
        rows.append({"模型": name, "交叉驗證準確率": round(scores.mean(), 3),
                     "標準差": round(scores.std(), 3)})
        print(f"{name:<6} 準確率 {scores.mean():.3f} ± {scores.std():.3f}")
    scores_df = pd.DataFrame(rows)
    scores_df.to_csv(os.path.join(PROC, "ml_model_scores.csv"),
                     index=False, encoding="utf-8-sig")
    return models, scores_df


def feature_importance(X, y):
    """隨機森林的特徵重要度 + 邏輯迴歸的標準化係數，看哪些因素最能預測供給不足。"""
    rf = RandomForestClassifier(n_estimators=300, random_state=0).fit(X, y)
    logit = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(X, y)
    coef = logit.named_steps["logisticregression"].coef_[0]
    imp = pd.DataFrame({
        "特徵": FEATURES,
        "隨機森林重要度": rf.feature_importances_.round(3),
        "邏輯迴歸係數": coef.round(3),
    }).sort_values("隨機森林重要度", ascending=False)
    imp.to_csv(os.path.join(PROC, "ml_feature_importance.csv"),
               index=False, encoding="utf-8-sig")
    print("\n特徵重要度（隨機森林）:")
    print(imp.to_string(index=False))
    return rf, imp


def save_predictions(data, X, y, rf):
    """用隨機森林對全部縣市做預測，存實際 vs 預測與不足機率。"""
    prob = rf.predict_proba(X)[:, 1]
    pred = (prob >= 0.5).astype(int)
    out = pd.DataFrame({
        "縣市": data["縣市"].values,
        "長照服務涵蓋率%": data["長照服務涵蓋率%"].values,
        "實際_供給不足": y.values,
        "預測_供給不足": pred,
        "預測不足機率": prob.round(3),
    }).sort_values("預測不足機率", ascending=False)
    out.to_csv(os.path.join(PROC, "ml_predictions.csv"),
               index=False, encoding="utf-8-sig")
    acc = (out["實際_供給不足"] == out["預測_供給不足"]).mean()
    print(f"\n隨機森林對全資料的重判正確率 {acc:.3f}（僅供參考，非交叉驗證）")
    return out


def chart_model_comparison(scores_df):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(scores_df["模型"], scores_df["交叉驗證準確率"],
                  yerr=scores_df["標準差"], capsize=5,
                  color=["#4c72b0", "#55a868", "#c44e52"])
    for b, v in zip(bars, scores_df["交叉驗證準確率"]):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.2f}",
                ha="center", fontproperties=FONT)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("5-fold 交叉驗證準確率", fontproperties=FONT)
    ax.set_title("三種分類模型預測「供給不足」準確率比較", fontproperties=FONT, fontsize=14)
    for lab in ax.get_xticklabels():
        lab.set_fontproperties(FONT)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "12_model_comparison.png"), dpi=130)
    plt.close()


def chart_feature_importance(imp):
    d = imp.sort_values("隨機森林重要度")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(d["特徵"], d["隨機森林重要度"], color="#c44e52")
    for i, v in enumerate(d["隨機森林重要度"]):
        ax.text(v + 0.005, i, f"{v:.2f}", va="center", fontproperties=FONT)
    ax.set_xlabel("重要度（越大越能決定是否供給不足）", fontproperties=FONT)
    ax.set_title("隨機森林：哪些因素最能預測長照供給不足", fontproperties=FONT, fontsize=14)
    for lab in ax.get_yticklabels():
        lab.set_fontproperties(FONT)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "13_feature_importance.png"), dpi=130)
    plt.close()


if __name__ == "__main__":
    data, X, y = load_dataset()
    models, scores_df = evaluate_models(X, y)
    rf, imp = feature_importance(X, y)
    save_predictions(data, X, y, rf)
    chart_model_comparison(scores_df)
    chart_feature_importance(imp)
    print("\n已輸出 12_model_comparison.png / 13_feature_importance.png 與 3 個 ml_*.csv")
