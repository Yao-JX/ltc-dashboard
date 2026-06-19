# -*- coding: utf-8 -*-
"""
把 data/processed 的 CSV 灌進一個 SQLite 資料庫 (ltc.db)，
之後查資料就用 SQL，不用每次都重讀一堆 CSV。
順便跑幾個查詢驗證（涵蓋率最低前五、老年比例最高、供需 JOIN 等）。

輸入: data/processed/*.csv
輸出: data/processed/ltc.db
"""
import os
import glob
import sqlite3
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(BASE, "data", "processed")
DB = os.path.join(PROC, "ltc.db")

# CSV 檔名 -> 資料表名（取檔名，去副檔名）
TABLES = {
    "county_master": "county_master.csv",
    "ltc_coverage": "ltc_coverage.csv",
    "ltc_resources": "ltc_resources.csv",
    "aging_index_timeseries": "aging_index_timeseries.csv",
    "forecast_aging_index": "forecast_aging_index.csv",
    "forecast_bed_demand_2030": "forecast_bed_demand_2030.csv",
    "risk_comparison": "risk_comparison.csv",
}


def build():
    if os.path.exists(DB):
        os.remove(DB)              # 每次重建，避免殘留舊資料
    con = sqlite3.connect(DB)
    made = []
    for table, fname in TABLES.items():
        path = os.path.join(PROC, fname)
        if not os.path.exists(path):
            print("跳過（找不到）:", fname)
            continue
        df = pd.read_csv(path)
        df.to_sql(table, con, if_exists="replace", index=False)
        made.append((table, len(df), len(df.columns)))
    con.commit()
    print("ltc.db 已建立，共", len(made), "張表：")
    for t, r, c in made:
        print(f"  {t:<26} {r:>3} 列 x {c:>2} 欄")
    return con


def demo_queries(con):
    """幾個示範查詢，證明資料進得了 SQL 也查得出來。"""
    qs = [
        ("涵蓋率最低前 5 名",
         """SELECT 縣市, "長照服務涵蓋率%" AS 涵蓋率, "未滿足需求比例%" AS 未滿足
            FROM county_master
            ORDER BY 涵蓋率 ASC LIMIT 5"""),
        ("老年人口比例最高前 5 名",
         """SELECT 縣市, "老年人口比例%" AS 老年比例, 核定床數
            FROM county_master
            ORDER BY 老年比例 DESC LIMIT 5"""),
        ("全國核定床數與機構數合計",
         """SELECT SUM(核定床數) AS 總床數, SUM(機構數) AS 總機構數
            FROM county_master"""),
        ("涵蓋率<80% 且 A 整合中心達成率偏低的縣市",
         """SELECT 縣市, "長照服務涵蓋率%" AS 涵蓋率, "A達成率%" AS A達成率
            FROM county_master
            WHERE "長照服務涵蓋率%" < 80
            ORDER BY A達成率 ASC"""),
        ("主表 JOIN 2030 床位缺口（缺口前 5）",
         """SELECT c.縣市, c."老年人口比例%" AS 老年比例, d."2030床位缺口" AS 缺口
            FROM county_master c
            JOIN forecast_bed_demand_2030 d ON c.縣市 = d.縣市
            ORDER BY 缺口 DESC LIMIT 5"""),
    ]
    for title, sql in qs:
        print("\n--- " + title + " ---")
        print(pd.read_sql_query(sql, con).to_string(index=False))


if __name__ == "__main__":
    con = build()
    demo_queries(con)
    con.close()
    print("\n完成，資料庫位置:", DB)
