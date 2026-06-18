# -*- coding: utf-8 -*-
"""探索各原始檔結構，確認欄位與編碼後再撰寫清理流程。"""
import os, glob, pandas as pd
RAW = r"C:\Users\y\03-SQL_Demo\0618\data\raw"

def line(t): print("\n" + "="*70 + f"\n{t}\n" + "="*70)

# 1) 14226 單一年齡人口
line("14226 單一年齡人口")
df = pd.read_csv(os.path.join(RAW, "14226_population_single_age.csv"))
print("shape", df.shape)
print("第一欄名", df.columns[0])
key = df.iloc[:,0].astype(str)
parts = key.str.split("/", expand=True)
print("切割後欄位數", parts.shape[1])
regions = parts[1].str.strip().unique() if parts.shape[1] > 1 else []
print("區域數", len(regions))
print("區域樣本", list(regions[:30]))
print("性別值", parts[2].str.strip().unique() if parts.shape[1] > 2 else "n/a")

# 2) 8572 老人福利機構 (Big5)
line("8572 老人福利機構 (inst_1.csv, big5)")
inst = pd.read_csv(os.path.join(RAW, "elderly_institutions_8572", "inst_1.csv"), encoding="big5", on_bad_lines="skip")
print("欄位", list(inst.columns))
print("列數", len(inst))
print(inst.head(2).to_string())

# 3) 身障 年齡×縣市
line("disability_by_age_county.xls (實為xlsx)")
xl = pd.ExcelFile(os.path.join(RAW, "disability_by_age_county.xls"))
print("sheets", xl.sheet_names)
d = pd.read_excel(xl, sheet_name=0, header=None, nrows=12)
print(d.to_string())

# 4) 老化指數時間序列
line("ris_aging_index_by_county.xls")
xl2 = pd.ExcelFile(os.path.join(RAW, "ris_aging_index_by_county.xls"))
print("sheets", xl2.sheet_names)
a = pd.read_excel(xl2, sheet_name=0, header=None, nrows=12)
print(a.to_string())
