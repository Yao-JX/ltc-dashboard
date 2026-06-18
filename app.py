# -*- coding: utf-8 -*-
"""
台灣長照供需互動式儀表板 (Streamlit)
執行： streamlit run app.py
"""
import os, json
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

BASE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.join(BASE, "data", "processed")

st.set_page_config(page_title="台灣長照供需儀表板", layout="wide", page_icon="🧓")

@st.cache_data
def load():
    m = pd.read_csv(os.path.join(PROC, "county_master.csv"))
    ts = pd.read_csv(os.path.join(PROC, "aging_index_timeseries.csv"))
    fc = pd.read_csv(os.path.join(PROC, "forecast_aging_index.csv"))
    dem = pd.read_csv(os.path.join(PROC, "forecast_bed_demand_2030.csv"))
    geo = json.load(open(os.path.join(BASE, "assets", "tw_counties.json"), encoding="utf-8"))
    for f in geo["features"]:
        n = f["properties"]["COUNTYNAME"].replace("台", "臺")
        f["properties"]["COUNTYNAME"] = {"桃園縣": "桃園市"}.get(n, n)
    return m, ts, fc, dem, geo

m, ts, fc, dem, geo = load()

st.title("🧓 台灣高齡人口長照供需落差分析儀表板")
st.caption("資料：內政部戶政司（人口 2025/5）、衛福部（老人福利機構、身心障礙者 2025）、戶政司老化指數時間序列")

# ---- KPI ----
c1, c2, c3, c4 = st.columns(4)
c1.metric("全國老年人口(65+)", f"{m['老年人口_65歲以上'].sum():,}")
c2.metric("全國老人福利機構", f"{int(m['機構數'].sum()):,} 家")
c3.metric("全國核定床數", f"{int(m['核定床數'].sum()):,} 床")
c4.metric("2030 總床位缺口推估", f"{int(dem[dem['2030床位缺口']>0]['2030床位缺口'].sum()):,} 床")

tab1, tab2, tab3, tab4 = st.tabs(["🗺️ 供需地圖", "📊 缺口排名", "📈 趨勢與預測", "🔎 縣市詳情"])

# ---- Tab1 地圖 ----
with tab1:
    opts = [c for c in ["長照服務涵蓋率%", "脆弱度指數", "每千名老人核定床數", "老年人口比例%", "高齡人口比例%", "核定床數", "機構數"] if c in m.columns]
    metric = st.selectbox("選擇指標", opts)
    rev = metric in ("每千名老人核定床數", "長照服務涵蓋率%")  # 數值越低越需關注→反向色階
    fig = px.choropleth(
        m, geojson=geo, locations="縣市", featureidkey="properties.COUNTYNAME",
        color=metric, color_continuous_scale="RdYlGn" if rev else "OrRd",
        hover_data=["老年人口比例%", "機構數", "核定床數", "每千名老人核定床數"])
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(height=650, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

# ---- Tab2 排名 ----
with tab2:
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

# ---- Tab3 趨勢與預測 ----
with tab3:
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
                name=f"{c}(預測)", line=dict(color=col, dash="dash"), showlegend=False))
    fig.add_hline(y=100, line_dash="dot", line_color="gray")
    fig.update_layout(height=600, xaxis_title="西元年", yaxis_title="老化指數（老年/幼年×100）")
    st.plotly_chart(fig, use_container_width=True)

# ---- Tab4 縣市詳情 ----
with tab4:
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
    st.info(f"📌 **2030 預估**：老年人口將達 **{int(dr['老年人口_2030預估']):,}** 人"
            f"（比率 {dr['老年比率_2030預估%']}%）；維持全國中位服務水準需 "
            f"**{int(dr['2030維持中位服務所需床數']):,}** 床，"
            f"床位缺口 **{int(dr['2030床位缺口']):+,}** 床。")
