# -*- coding: utf-8 -*-
"""
台灣長照供需互動式儀表板
跑法：streamlit run app.py
資料都讀 data/processed 下算好的 CSV，所以開網頁很快、不會在前端重算。
"""
import os
import json
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

BASE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.join(BASE, "data", "processed")

st.set_page_config(page_title="台灣長照供需儀表板", layout="wide")


def _csv(name):
    return pd.read_csv(os.path.join(PROC, name))


@st.cache_data
def load():
    m = _csv("county_master.csv")
    ts = _csv("aging_index_timeseries.csv")
    fc = _csv("forecast_aging_index.csv")
    dem = _csv("forecast_bed_demand_2030.csv")
    geo = json.load(open(os.path.join(BASE, "assets", "tw_counties.json"), encoding="utf-8"))
    for f in geo["features"]:
        n = f["properties"]["COUNTYNAME"].replace("台", "臺")
        f["properties"]["COUNTYNAME"] = {"桃園縣": "桃園市"}.get(n, n)
    return m, ts, fc, dem, geo


@st.cache_data
def load_optional(name):
    """ML、方法比較等延伸資料，沒有就回 None，不讓主畫面掛掉。"""
    path = os.path.join(PROC, name)
    return pd.read_csv(path) if os.path.exists(path) else None


@st.cache_resource
def get_db():
    """把所有 processed CSV 灌進記憶體 SQLite，給『資料庫查詢』分頁用。"""
    con = sqlite3.connect(":memory:", check_same_thread=False)
    files = {
        "county_master": "county_master.csv",
        "ltc_coverage": "ltc_coverage.csv",
        "ltc_resources": "ltc_resources.csv",
        "aging_index_timeseries": "aging_index_timeseries.csv",
        "forecast_aging_index": "forecast_aging_index.csv",
        "forecast_bed_demand_2030": "forecast_bed_demand_2030.csv",
        "risk_comparison": "risk_comparison.csv",
    }
    for table, fname in files.items():
        p = os.path.join(PROC, fname)
        if os.path.exists(p):
            pd.read_csv(p).to_sql(table, con, if_exists="replace", index=False)
    return con


m, ts, fc, dem, geo = load()

st.title("台灣高齡人口長照供需落差分析")
st.caption("資料：內政部戶政司（人口 2025/5、老化指數 2010–2025）、衛福部（老人福利機構、身心障礙者、長照涵蓋率 2025）")

c1, c2, c3, c4 = st.columns(4)
c1.metric("全國老年人口(65+)", f"{m['老年人口_65歲以上'].sum():,}")
c2.metric("全國老人福利機構", f"{int(m['機構數'].sum()):,} 家")
c3.metric("全國核定床數", f"{int(m['核定床數'].sum()):,} 床")
c4.metric("2030 總床位缺口推估", f"{int(dem[dem['2030床位缺口']>0]['2030床位缺口'].sum()):,} 床")

tab_map, tab_rank, tab_trend, tab_ml, tab_sql, tab_county = st.tabs(
    ["供需地圖", "缺口排名", "趨勢與預測", "供給不足預測(ML)", "資料庫查詢(SQL)", "縣市詳情"])

# ---- 供需地圖 ----
with tab_map:
    opts = [c for c in ["長照服務涵蓋率%", "脆弱度指數", "每千名老人核定床數",
                        "老年人口比例%", "高齡人口比例%", "核定床數", "機構數"] if c in m.columns]
    metric = st.selectbox("選擇指標", opts)
    rev = metric in ("每千名老人核定床數", "長照服務涵蓋率%")  # 數值越低越需關注 → 反向色階
    fig = px.choropleth(
        m, geojson=geo, locations="縣市", featureidkey="properties.COUNTYNAME",
        color=metric, color_continuous_scale="RdYlGn" if rev else "OrRd",
        hover_data=["老年人口比例%", "機構數", "核定床數", "每千名老人核定床數"])
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(height=650, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

# ---- 缺口排名 ----
with tab_rank:
    colA, colB = st.columns(2)
    with colA:
        st.subheader("每千名老人核定床數（紅=低於中位）")
        d = m.sort_values("每千名老人核定床數")
        fig = px.bar(d, x="每千名老人核定床數", y="縣市", orientation="h",
                     color="床數供需指數_對中位數%", color_continuous_scale="RdYlGn")
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
    with colB:
        st.subheader("2030 床位缺口推估（正值=需擴充）")
        d = dem.sort_values("2030床位缺口")
        fig = px.bar(d, x="2030床位缺口", y="縣市", orientation="h",
                     color="2030床位缺口", color_continuous_scale="RdYlGn_r")
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(m, use_container_width=True)

# ---- 趨勢與預測 ----
with tab_trend:
    sel = st.multiselect("選擇縣市", sorted(m["縣市"].unique()),
                         default=["臺北市", "新北市", "桃園市", "嘉義縣", "新竹市"])
    fig = go.Figure()
    pal = px.colors.qualitative.Set1
    for i, c in enumerate(sel):
        a = ts[ts["縣市"] == c].sort_values("年_西元")
        f = fc[fc["縣市"] == c].sort_values("年_西元")
        col = pal[i % len(pal)]
        fig.add_trace(go.Scatter(x=a["年_西元"], y=a["老化指數"], name=c, line=dict(color=col)))
        if len(a) and len(f):
            fig.add_trace(go.Scatter(
                x=[a["年_西元"].iloc[-1]] + list(f["年_西元"]),
                y=[a["老化指數"].iloc[-1]] + list(f["老化指數_預測"]),
                name=f"{c}(線性預測)", line=dict(color=col, dash="dash"), showlegend=False))
    fig.add_hline(y=100, line_dash="dot", line_color="gray")
    fig.update_layout(height=520, xaxis_title="西元年", yaxis_title="老化指數（老年/幼年×100）")
    st.plotly_chart(fig, use_container_width=True)

    methodcmp = load_optional("forecast_method_comparison.csv")
    backtest = load_optional("forecast_method_backtest.csv")
    if methodcmp is not None:
        st.subheader("2030 預測：三種方法比較")
        st.caption("線性、年均成長率(CAGR)、移動平均三種外推法。回測（遮最後 3 年比對）顯示老化指數在加速，"
                   "直線會低估，所以實務上把 2030 當「線性～CAGR」的區間看比較保守。")
        if backtest is not None:
            cols = st.columns(len(backtest))
            for col, (_, r) in zip(cols, backtest.iterrows()):
                col.metric(f"{r['方法']} 回測誤差(MAE)", f"{r['回測MAE']:.2f}")
        st.dataframe(methodcmp, use_container_width=True)

# ---- 供給不足預測 (ML) ----
with tab_ml:
    scores = load_optional("ml_model_scores.csv")
    imp = load_optional("ml_feature_importance.csv")
    preds = load_optional("ml_predictions.csv")
    if scores is None:
        st.info("尚未產生機器學習結果，請先在本機執行 `python scripts/ml_supply_gap.py`。")
    else:
        st.subheader("把「縣市是否長照供給不足」當二元分類來預測")
        st.caption("標籤：長照服務涵蓋率 < 80% 視為供給不足。特徵只用人口/供給結構欄位（老年比例、"
                   "高齡比例、每千名老人床數與機構數、A 整合中心達成率、身障老人占比），避免用涵蓋率本身造成洩漏。"
                   "只有 22 個縣市、樣本很少，準確率用 5-fold 交叉驗證估，當方法示範看。")
        colA, colB = st.columns([1, 1])
        with colA:
            st.markdown("**三種模型準確率**")
            fig = px.bar(scores, x="模型", y="交叉驗證準確率", error_y="標準差",
                         range_y=[0, 1.05], text="交叉驗證準確率")
            fig.update_traces(textposition="outside")
            fig.update_layout(height=380)
            st.plotly_chart(fig, use_container_width=True)
        with colB:
            if imp is not None:
                st.markdown("**特徵重要度（隨機森林）**")
                d = imp.sort_values("隨機森林重要度")
                fig = px.bar(d, x="隨機森林重要度", y="特徵", orientation="h")
                fig.update_layout(height=380)
                st.plotly_chart(fig, use_container_width=True)
        if preds is not None:
            st.markdown("**各縣市預測（隨機森林，依不足機率排序）**")
            st.dataframe(preds, use_container_width=True)

# ---- 資料庫查詢 (SQL) ----
with tab_sql:
    st.subheader("用 SQL 查資料")
    st.caption("把 data/processed 的 7 張 CSV 載進記憶體 SQLite，直接下 SQL。"
               "可用表：county_master、ltc_coverage、ltc_resources、aging_index_timeseries、"
               "forecast_aging_index、forecast_bed_demand_2030、risk_comparison。")
    examples = {
        "涵蓋率最低前 5 名":
            'SELECT 縣市, "長照服務涵蓋率%" AS 涵蓋率\nFROM county_master\nORDER BY 涵蓋率 ASC\nLIMIT 5;',
        "老年比例最高前 5 名":
            'SELECT 縣市, "老年人口比例%" AS 老年比例, 核定床數\nFROM county_master\nORDER BY 老年比例 DESC\nLIMIT 5;',
        "涵蓋率<80% 且 A 達成率偏低":
            'SELECT 縣市, "長照服務涵蓋率%" AS 涵蓋率, "A達成率%" AS A達成率\n'
            'FROM county_master\nWHERE "長照服務涵蓋率%" < 80\nORDER BY A達成率 ASC;',
        "主表 JOIN 2030 床位缺口":
            'SELECT c.縣市, c."老年人口比例%" AS 老年比例, d."2030床位缺口" AS 缺口\n'
            'FROM county_master c\nJOIN forecast_bed_demand_2030 d ON c.縣市 = d.縣市\n'
            'ORDER BY 缺口 DESC\nLIMIT 8;',
    }
    pick = st.selectbox("範例查詢", list(examples.keys()))
    sql = st.text_area("SQL", examples[pick], height=140)
    if st.button("執行查詢"):
        try:
            st.dataframe(pd.read_sql_query(sql, get_db()), use_container_width=True)
        except Exception as e:
            st.error(f"查詢出錯：{e}")

# ---- 縣市詳情 ----
with tab_county:
    c = st.selectbox("選擇縣市", sorted(m["縣市"].unique()))
    row = m[m["縣市"] == c].iloc[0]
    dr = dem[dem["縣市"] == c].iloc[0]
    k1, k2, k3 = st.columns(3)
    k1.metric("總人口", f"{int(row['總人口']):,}")
    k2.metric("老年人口(65+)", f"{int(row['老年人口_65歲以上']):,}", f"{row['老年人口比例%']}%")
    k3.metric("供給不足缺口排名", f"第 {int(row['供給不足缺口排名'])} 名 / 22")
    k4, k5, k6 = st.columns(3)
    k4.metric("機構數", f"{int(row['機構數'])} 家")
    k5.metric("核定床數", f"{int(row['核定床數']):,} 床")
    k6.metric("每千名老人床數", f"{row['每千名老人核定床數']}", f"{row['床數供需指數_對中位數%']}% vs 中位")
    st.info(f"2030 預估：老年人口將達 {int(dr['老年人口_2030預估']):,} 人"
            f"（比率 {dr['老年比率_2030預估%']}%）；維持全國中位服務水準需 "
            f"{int(dr['2030維持中位服務所需床數']):,} 床，"
            f"床位缺口 {int(dr['2030床位缺口']):+,} 床。")
