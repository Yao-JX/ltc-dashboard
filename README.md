# 台灣高齡人口長照供需落差分析與需求預測

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ltc-dashboard-ekx3eycnu4t2hgdyhjeqzh.streamlit.app/)
[![每月自動更新長照資料](https://github.com/Yao-JX/ltc-dashboard/actions/workflows/update-data.yml/badge.svg)](https://github.com/Yao-JX/ltc-dashboard/actions/workflows/update-data.yml)

線上儀表板：https://ltc-dashboard-ekx3eycnu4t2hgdyhjeqzh.streamlit.app/

這是期末專題。我們用政府公開資料分析各縣市高齡人口（需求）和長照資源（供給）是否平衡，
找出資源相對不足的地區，再預測未來的高齡化趨勢與床位缺口。後來又加了三塊：用 SQL 資料庫管資料、
用機器學習把「供給不足」做成分類預測、以及把時間序列預測換成多種方法互相比較。

## 做了哪些事

- 蒐集 5 個來源的真實政府資料（內政部、衛福部），放在 `data/raw/`。
- 清理後做成一張縣市主表 `data/processed/county_master.csv`，含供需指標。
- 人口、機構、身障資料都對齊到 2025 年。
- 畫了 14 張圖（含自己用 geojson 畫的台灣分縣市地圖），放在 `output/`。
- 需求預測：老化指數趨勢外推、2030 床位缺口推估。
- 互動式儀表板（Streamlit + Plotly），六個分頁。
- 把整理好的資料灌進 SQLite，用 SQL 做查詢。
- 機器學習：邏輯迴歸 / 決策樹 / 隨機森林預測縣市是否供給不足，比準確率、看特徵重要度。
- 時間序列升級：線性、CAGR、移動平均三種預測做回測比較。
- GitHub Actions 每月自動重抓資料、重算、重跑模型。

## 快速開始

```bash
pip install -r requirements.txt

python scripts/build_master.py        # 原始檔 → 縣市主表＋指標＋預測
python scripts/make_charts.py         # 產出 output/ 的靜態圖
python scripts/build_db.py            # 把 processed CSV 灌進 SQLite
python scripts/ml_supply_gap.py       # 機器學習：供給不足分類
python scripts/timeseries_compare.py  # 三種預測方法比較
streamlit run app.py                  # 開互動式儀表板
```

完整分析過程也可以直接開 `長照供需分析.ipynb`，由上到下 Run All 會跑完整條流程。

## 資料夾結構

```
0618/
├─ app.py                          Streamlit 互動式儀表板
├─ 長照供需分析.ipynb               完整分析過程（可獨立 Run All）
├─ README.md / SOURCES.md / ARCHITECTURE.md / USAGE.md / DEPLOY.md
├─ requirements.txt
├─ data/
│  ├─ raw/                         原始下載檔（人口、老化指數、身障、機構、長照 PDF）
│  └─ processed/                   清理後的資料表
│      ├─ county_master.csv            縣市主表（需求 + 供給 + 缺口 + 涵蓋率 + 脆弱度）
│      ├─ aging_index_timeseries.csv   各縣市老化指數 2010–2025
│      ├─ forecast_aging_index.csv     老化指數線性預測 2026–2030
│      ├─ forecast_bed_demand_2030.csv 2030 床位缺口推估
│      ├─ forecast_method_comparison.csv / forecast_method_backtest.csv  三種預測方法與回測
│      ├─ ml_model_scores.csv / ml_feature_importance.csv / ml_predictions.csv  機器學習結果
│      └─ risk_comparison.csv          新舊觀點（床位密度 vs 涵蓋率）對照
├─ assets/tw_counties.json         台灣縣市界 geojson（g0v）
├─ output/                         圖表 PNG（14 張）
└─ scripts/
   ├─ download_data.py    自動下載最新原始資料
   ├─ parse_ltc_pdfs.py   解析長照 PDF（涵蓋率、ABC 據點）
   ├─ build_master.py     建縣市主表、指標、預測
   ├─ make_charts.py      產靜態圖表
   ├─ build_db.py         建 SQLite 並示範查詢
   ├─ ml_supply_gap.py    機器學習分類
   └─ timeseries_compare.py  時間序列方法比較
```

## 圖表（output/）

1. `01_bed_gap_ranking.png` — 每千名老人核定床數排名
2. `02_elderly_ratio.png` — 各縣市老年人口比例
3. `03_aging_trend_forecast.png` — 老化指數趨勢 2010–2025 + 線性預測 2026–2030
4. `04_supply_demand_scatter.png` — 老年人口 vs 核定床數
5. `05_map_elderly_ratio.png` — 老年比例分縣市地圖
6. `06_map_bed_supply.png` — 每千名老人床數分縣市地圖
7. `07_bed_demand_gap_2030.png` — 2030 床位缺口推估
8. `08_coverage_rate_ranking.png` — 長照服務涵蓋率排名（真實供需缺口）
9. `09_map_coverage_rate.png` — 涵蓋率分縣市地圖
10. `10_rank_comparison.png` — 床位密度 vs 涵蓋率排名對照
11. `11_vulnerability_index.png` — 多維度脆弱度指數排名
12. `12_model_comparison.png` — 三種分類模型準確率
13. `13_feature_importance.png` — 隨機森林特徵重要度
14. `14_forecast_methods.png` — 線性 / CAGR / 移動平均預測對照

## 主表（county_master.csv）資料字典

| 欄位 | 說明 | 年 |
| --- | --- | --- |
| 縣市 | 22 直轄市/縣市 | — |
| 總人口 / 老年人口_65歲以上 / 高齡人口_75歲以上 | 人口（人） | 2025/5 |
| 老年人口比例% / 高齡人口比例% | 65+、75+ 佔比 | 2025/5 |
| 機構數 / 核定床數 | 老人福利機構家數、核定床位合計 | 2025 |
| 身障總人數 / 身障65歲以上 | 領證身心障礙者人數 | 2025 |
| 每千名老人核定床數 | 床位密度 = 床數 ÷ (65+/1000) | — |
| 床數供需指數_對中位數% | 相對全國中位數的落差，負值=偏低 | — |
| 長照服務涵蓋率% / 未滿足需求比例% | 衛福部，以失能推估需求為分母 | 2025 |
| 脆弱度指數 | 未滿足需求＋深度老化＋A 據點不足的 z-score 合成 | — |

## 主要發現（以長照服務涵蓋率為主軸）

一開始只用「每千名老人核定床數」當供給指標，但這個指標沒算照護人力，而且分母用老人數
會高估偏鄉、低估都會。後來改用衛福部「長照服務涵蓋率」（分母是失能推估需求、分子是實際服務人數），
結論整個翻過來，過程記在 `data/processed/risk_comparison.csv` 和圖 08–11。

- 真實供需缺口最大的是離島 + 北部都會圈：連江 33%、金門 43%、臺北 58%、基隆 70%、
  新竹市 77%、桃園 78%、苗栗 78%、新北 80%（涵蓋率越低代表越未滿足）。
- 離島最危險：人口少、難布建 A 整合中心（連江達成率 0%）、難留照護人力，等於「老人少卻乏人照顧」。
- 東部、南部反而涵蓋良好（臺東 112%、花蓮 109%、嘉義縣 115%、屏東 106%），長照 2.0 布建有成效。
- 方法校正：床位密度指標把臺中誤判為最危險（實際涵蓋率 89%），把嘉義縣誤判為不足（實際 115% 全國最佳）。
- 老年人口比例：嘉義縣最高（24.5%）、新竹縣最低（15.3%）。

## 機器學習：預測縣市是否供給不足

把「縣市是否長照供給不足」做成二元分類（涵蓋率 < 80% 標成不足）。特徵只用人口/供給結構欄位
（老年比例、高齡比例、每千名老人床數與機構數、A 達成率、身障老人占比），刻意不放涵蓋率本身或
由它算出來的欄位，避免資料洩漏。比較三種模型，用 5-fold 交叉驗證（22 個縣市樣本很少，數字當方法示範）：

| 模型 | 交叉驗證準確率 |
| --- | --- |
| 邏輯迴歸 | 0.78 |
| 決策樹 | 0.73 |
| 隨機森林 | 0.82 |

隨機森林表現最好。特徵重要度顯示「高齡人口比例」與「老年人口比例」最能決定一個縣市是否供給不足，
床位密度與 A 達成率次之——和前面用涵蓋率分析得到的結論方向一致。結果存在 `ml_*.csv`，
儀表板「供給不足預測(ML)」分頁也看得到。

## 資料庫：SQLite

`build_db.py` 把 `data/processed` 的 7 張 CSV 灌進一個 SQLite 檔（`ltc.db`），之後就能直接用 SQL 查，
例如涵蓋率最低前 5 名、老年比例最高、主表 JOIN 2030 缺口等。儀表板的「資料庫查詢(SQL)」分頁
是在記憶體裡即時建庫，可以直接打 SQL 試。（`ltc.db` 可由腳本重建，沒進版控。）

## 時間序列：三種預測方法比較

第八節原本只用線性迴歸外推老化指數。但老化其實在加速，直線會低估，所以又加了 CAGR（年均複合成長率）
和移動平均兩種方法。選法不是用講的，而是回測：把每個縣市最後 3 年遮起來、用前面資料預測再比對，
算平均絕對誤差（MAE）。結果 CAGR 最準（3.33）、移動平均次之（3.77）、線性最差（5.25），印證
「直線低估加速中的老化」。所以主圖維持線性（最好解釋），但 2030 數字改用「線性～CAGR」當區間看。

## 政策建議方向

1. 離島：在地培力 + 跨縣市支援 + 遠距/巡迴照護，補 A/C 據點與人力缺口。
2. 北部都會：提升長照 2.0 給付使用率、銜接外勞與正式服務、擴充居家/社區量能。
3. 資源配置以涵蓋率與失能需求成長為依據，而非單純床位數。

## 方法與限制

- 預測：對各縣市老化指數、老年比率以最近 10 年做迴歸外推到 2030，並補上 CAGR / 移動平均對照。
- 2030 床位缺口假設總人口維持 2025 水準（保守），主要驅動是老年比率上升。
- 核定床數代表機構住宿式供給，未涵蓋居家/社區式服務量，是機構式長照供給的代理指標。
- 身障人數是「領證」人數，與「失能」不完全相同，只當需求面輔助參考。
- 機器學習只有 22 個縣市樣本，結論當方法示範，不宜過度解讀。
