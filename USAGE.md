# 使用教學（USAGE）

怎麼把這個專案跑起來。

---

## 0. 事前準備

- 裝 Python 3.10 以上（我是用 3.12 開發）。
- 開命令提示字元（CMD）或 PowerShell，切到專案資料夾：
  ```cmd
  cd C:\Users\y\03-SQL_Demo\0618
  ```
- 裝套件（只要做一次）：
  ```cmd
  python -m pip install -r requirements.txt
  ```

確認 Python 沒裝錯：`python -c "import streamlit; print('OK')"` 顯示 OK 就對了。

---

## 1. 三種使用方式（依需求擇一）

### 方式 A：看互動式儀表板（最推薦給一般使用者）

```cmd
python -m streamlit run app.py
```

- 終端機會顯示 `Local URL: http://localhost:8501`，瀏覽器會自動打開。
- 六個分頁：供需地圖 / 缺口排名 / 趨勢與預測 / 供給不足預測(ML) / 資料庫查詢(SQL) / 縣市詳情。
- 結束：在終端機按 `Ctrl + C`。

注意：一定要用 `streamlit run`，不要用 `python app.py` 或 `uv run app.py`，那樣不會啟動網頁。

### 方式 B：看完整分析過程（適合報告／作業）

用 Jupyter 或 VS Code 開啟 **`長照供需分析.ipynb`**，由上到下執行（Run All）。
會依序完成：資料下載 → 清理 → 主表 → 圖表 → 預測 → 結論，圖表直接顯示在筆記本內。

```cmd
python -m jupyter notebook 長照供需分析.ipynb
```

### 方式 C：用指令重新產生所有資料與圖表

```cmd
python scripts\parse_ltc_pdfs.py      # 解析長照 PDF → CSV
python scripts\build_master.py        # 原始資料 → 縣市主表＋指標＋預測
python scripts\make_charts.py         # 產出 output\ 的圖（01–11）
python scripts\build_db.py            # 把 processed CSV 灌進 SQLite，順便示範查詢
python scripts\ml_supply_gap.py       # 機器學習：預測縣市是否供給不足（圖 12、13）
python scripts\timeseries_compare.py  # 老化指數三種預測方法比較（圖 14）
```

---

## 2. 各檔案在哪、是什麼

| 想找 | 路徑 |
|---|---|
| 縣市主表（最終結果） | `data\processed\county_master.csv` |
| 新舊觀點對照 | `data\processed\risk_comparison.csv` |
| 2030 床位缺口 | `data\processed\forecast_bed_demand_2030.csv` |
| 機器學習結果 | `data\processed\ml_*.csv` |
| 三種預測方法比較 | `data\processed\forecast_method_*.csv` |
| SQLite 資料庫 | `data\processed\ltc.db`（由 `build_db.py` 重建） |
| 所有圖表 | `output\*.png`（共 14 張） |
| 原始政府資料 | `data\raw\` |
| 資料來源出處 | `SOURCES.md` |
| 方法與發現說明 | `README.md` |

---

## 3. 常見問題

**Q：`ModuleNotFoundError: No module named 'streamlit'`**
A：你執行的 Python 沒裝套件。先 `python -m pip install -r requirements.txt`；
若用 `uv`，要改成 `uv pip install -r requirements.txt` 再 `uv run streamlit run app.py`。

**Q：圖表中文變成方框／亂碼**
A：腳本使用 Windows 內建「微軟正黑體」(`C:\Windows\Fonts\msjh.ttc`)。
非 Windows 系統請改用系統有的中文字型（在 `make_charts.py` 開頭的 `FONT` 設定）。

**Q：想換最新年度資料**
A：刪掉 `data\raw\` 對應檔案後，重跑 notebook 的「資料下載」段或 `build_master.py`，
程式會自動抓最新可用資料。

**Q：儀表板打不開 / 埠被占用**
A：換個埠：`python -m streamlit run app.py --server.port 8502`。
