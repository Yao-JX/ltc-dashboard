# -*- coding: utf-8 -*-
"""
整理台灣長照供需資料，產出縣市主表 / 趨勢序列 / 簡易預測。
輸入: data/raw/*
輸出: data/processed/*
"""
import os, re, glob
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
OUT = os.path.join(BASE, "data", "processed")
os.makedirs(OUT, exist_ok=True)

COUNTIES = ["新北市","臺北市","桃園市","臺中市","臺南市","高雄市","宜蘭縣","新竹縣",
            "苗栗縣","彰化縣","南投縣","雲林縣","嘉義縣","屏東縣","臺東縣","花蓮縣",
            "澎湖縣","基隆市","新竹市","嘉義市","金門縣","連江縣"]

def log(t): print("\n" + "="*60 + f"\n{t}\n" + "="*60)

# ---------------------------------------------------------------
# 1) 人口：縣市總人口、65+、75+（資料年 2025/5 民國114年5月，村里單一年齡彙總）
# ---------------------------------------------------------------
log("STEP1 人口單一年齡 (77132)")
# 優先使用排程下載的最新檔；否則退回既有的年月檔
_latest = os.path.join(RAW, "77132_pop_single_age_latest.csv")
if os.path.exists(_latest):
    pop_path = _latest
else:
    _cands = sorted(glob.glob(os.path.join(RAW, "77132_pop_single_age*.csv")))
    pop_path = _cands[-1] if _cands else _latest
print("使用人口檔:", os.path.basename(pop_path))
pop = pd.read_csv(pop_path)
POP_YEAR = "latest"
pop["縣市"] = pop["區域別"].astype(str).str[:3]
pop = pop[pop["縣市"].isin(COUNTIES)].copy()

# 年齡欄：'N歲-男/女' 與 '100歲以上-男/女'
age_age = {}   # age -> [男欄,女欄]
for c in pop.columns:
    m = re.match(r"^(\d+)歲-(男|女)$", str(c))
    if m:
        age_age.setdefault(int(m.group(1)), []).append(c)
cols_100 = [c for c in pop.columns if str(c).startswith("100歲以上")]

def ge_cols(lo):
    cs = []
    for a, lst in age_age.items():
        if a >= lo:
            cs += lst
    return cs + cols_100

cols_65 = ge_cols(65)
cols_75 = ge_cols(75)
for c in ["人口數"] + cols_65 + cols_75:
    pop[c] = pd.to_numeric(pop[c], errors="coerce")

g = pop.groupby("縣市")
pop_df = pd.DataFrame({
    "總人口": g["人口數"].sum().astype(int),
    "老年人口_65歲以上": g[cols_65].sum().sum(axis=1).astype(int),
    "高齡人口_75歲以上": g[cols_75].sum().sum(axis=1).astype(int),
}).reset_index()
pop_df["老年人口比例%"] = (pop_df["老年人口_65歲以上"] / pop_df["總人口"] * 100).round(2)
pop_df["高齡人口比例%"] = (pop_df["高齡人口_75歲以上"] / pop_df["總人口"] * 100).round(2)
print("人口資料年:", POP_YEAR, "| 縣市數:", len(pop_df))
print(pop_df.head().to_string())

# ---------------------------------------------------------------
# 2) 供給：老人福利機構數 + 核定床數（8572）
# ---------------------------------------------------------------
log("STEP2 老人福利機構 (8572)")
inst_rec = []
for f in glob.glob(os.path.join(RAW, "elderly_institutions_8572", "*.csv")):
    county = os.path.splitext(os.path.basename(f))[0]
    try:
        d = pd.read_csv(f, encoding="big5", on_bad_lines="skip")
    except Exception as e:
        print("讀取失敗", county, e); continue
    bed_col = [c for c in d.columns if "床數" in str(c)]
    beds = pd.to_numeric(d[bed_col[0]], errors="coerce").sum() if bed_col else np.nan
    inst_rec.append({"縣市": county, "機構數": len(d), "核定床數": int(beds) if pd.notna(beds) else 0})
inst_df = pd.DataFrame(inst_rec)
print(inst_df.sort_values("機構數", ascending=False).head().to_string())

# ---------------------------------------------------------------
# 3) 身心障礙者人數（按年齡及縣市，使用最近完整年度分頁）
# ---------------------------------------------------------------
log("STEP3 身心障礙者人數")
dis_path = os.path.join(RAW, "disability_by_age_county.xls")
xls = pd.ExcelFile(dis_path)
# 找出名稱為純年份(4碼)的最近分頁
year_sheets = [s for s in xls.sheet_names if re.fullmatch(r"\d{4}", str(s))]
year_sheets_sorted = sorted(year_sheets, key=lambda x: int(x), reverse=True)
print("可用年度分頁:", year_sheets_sorted)
dis_df = None
for sh in year_sheets_sorted:
    raw = pd.read_excel(xls, sheet_name=sh, header=None)
    # 找含 "65" 的標題列以定位欄位
    rows = []
    for _, row in raw.iterrows():
        cell0 = str(row[0])
        county_match = next((c for c in COUNTIES if c in cell0 or cell0 in c), None)
        # 也比對去掉省市字樣
        if county_match is None:
            for c in COUNTIES:
                if c.replace("臺","台") in cell0 or c[:-1] in cell0 and len(c)>2:
                    county_match = c; break
        if county_match:
            nums = pd.to_numeric(row[1:], errors="coerce").dropna()
            if len(nums) >= 2:
                total = nums.iloc[0]
                p65 = nums.iloc[-1]  # 最後一欄為 65歲以上
                rows.append({"縣市": county_match, "身障總人數": int(total), "身障65歲以上": int(p65)})
    if rows:
        dis_df = pd.DataFrame(rows).drop_duplicates("縣市")
        dis_df["身障資料年"] = sh
        print(f"使用分頁 {sh}，取得 {len(dis_df)} 縣市")
        print(dis_df.head().to_string())
        break
if dis_df is None:
    print("WARN 無法解析身障縣市資料"); dis_df = pd.DataFrame(columns=["縣市","身障總人數","身障65歲以上","身障資料年"])

# ---------------------------------------------------------------
# 4) 合併主表 + 供需指標
# ---------------------------------------------------------------
log("STEP4 合併主表 + 供需指標")
m = pop_df.merge(inst_df, on="縣市", how="left").merge(dis_df, on="縣市", how="left")
m["每千名老人機構數"] = (m["機構數"] / (m["老年人口_65歲以上"]/1000)).round(3)
m["每千名老人核定床數"] = (m["核定床數"] / (m["老年人口_65歲以上"]/1000)).round(2)
# 缺口指標：床數供給相對全國中位數的落差（負值=不足）
median_bed = m["每千名老人核定床數"].median()
m["床數供需指數_對中位數%"] = ((m["每千名老人核定床數"]/median_bed - 1)*100).round(1)
m["供給不足缺口排名"] = m["每千名老人核定床數"].rank(ascending=True).astype(int)
m = m.sort_values("每千名老人核定床數")
m.to_csv(os.path.join(OUT, "county_master.csv"), index=False, encoding="utf-8-sig")
print(m.to_string())
print("\n>> 已輸出 county_master.csv")

# ---------------------------------------------------------------
# 5) 各縣市老化指數時間序列 + 簡易線性預測（未來5年）
# ---------------------------------------------------------------
log("STEP5 老化指數趨勢 + 預測")
ag = pd.ExcelFile(os.path.join(RAW, "ris_aging_index_by_county.xls"))
print("老化指數檔分頁:", ag.sheet_names)
# 版面：縣市為列、年份(民國NN年底)為欄；標題列 index=2，資料自 index=3
idx_sheet = ag.sheet_names[2]
ti = pd.read_excel(ag, sheet_name=idx_sheet, header=2)
ti = ti.rename(columns={ti.columns[0]: "縣市"})
ti["縣市"] = ti["縣市"].astype(str).str.replace("　", "", regex=False).str.strip()
ti = ti[ti["縣市"].isin(COUNTIES)].copy()
print("可用縣市列:", len(ti))
year_cols = [c for c in ti.columns if re.search(r"\d+年", str(c))]
ti_long = ti.melt(id_vars=["縣市"], value_vars=year_cols, var_name="年", value_name="老化指數")
ti_long["年_西元"] = ti_long["年"].astype(str).str.extract(r"(\d+)").astype(float) + 1911
long = ti_long.dropna(subset=["年_西元"])[["年_西元", "縣市", "老化指數"]].copy()
long["年_西元"] = long["年_西元"].astype(int)
long["老化指數"] = pd.to_numeric(long["老化指數"], errors="coerce")
long = long.dropna(subset=["老化指數"])
long.to_csv(os.path.join(OUT, "aging_index_timeseries.csv"), index=False, encoding="utf-8-sig")
print(">> 已輸出 aging_index_timeseries.csv  (列數 %d)" % len(long))

# 線性預測未來5年（用最近10年）
fc = []
last_year = int(long["年_西元"].max())
for c, g in long.groupby("縣市"):
    g = g.sort_values("年_西元").tail(10)
    if len(g) < 4: continue
    x = g["年_西元"].values.astype(float); y = g["老化指數"].values.astype(float)
    a, b = np.polyfit(x, y, 1)
    for yr in range(last_year+1, last_year+6):
        fc.append({"縣市": c.strip(), "年_西元": yr, "老化指數_預測": round(a*yr+b, 1)})
fc_df = pd.DataFrame(fc)
fc_df.to_csv(os.path.join(OUT, "forecast_aging_index.csv"), index=False, encoding="utf-8-sig")
print(">> 已輸出 forecast_aging_index.csv  (最後實際年 %d → 預測至 %d)" % (last_year, last_year+5))
print(fc_df.head(10).to_string())

# ---------------------------------------------------------------
# 6) 需求預測：各縣市老年人口比率 → 預測 65+ 人口與 2030 床位缺口
# ---------------------------------------------------------------
log("STEP6 老年人口預測 + 2030 床位缺口")
# 老年人口比率分頁 (idx1)，版面同老化指數：縣市為列、年份(NN年底)為欄
rate = pd.read_excel(ag, sheet_name=ag.sheet_names[1], header=2)
rate = rate.rename(columns={rate.columns[0]: "縣市"})
rate["縣市"] = rate["縣市"].astype(str).str.replace("　", "", regex=False).str.strip()
rate = rate[rate["縣市"].isin(COUNTIES)].copy()
ycols = [c for c in rate.columns if re.search(r"\d+年", str(c))]
rlong = rate.melt(id_vars=["縣市"], value_vars=ycols, var_name="年", value_name="老年比率")
rlong["年_西元"] = rlong["年"].astype(str).str.extract(r"(\d+)").astype(float) + 1911
rlong["老年比率"] = pd.to_numeric(rlong["老年比率"], errors="coerce")
rlong = rlong.dropna(subset=["年_西元", "老年比率"])
rlong["年_西元"] = rlong["年_西元"].astype(int)

# 床位供給目標 = 現況全國中位數（每千名老人床數）；維持此服務水準所需床數
target_bed_per_1000 = m["每千名老人核定床數"].median()
tot = pop_df.set_index("縣市")["總人口"]      # 2025 總人口（預測期間假設不變，保守）
beds_now = m.set_index("縣市")["核定床數"]

drec = []
for c, g in rlong.groupby("縣市"):
    g = g.sort_values("年_西元").tail(10)
    a, b = np.polyfit(g["年_西元"].astype(float), g["老年比率"].astype(float), 1)
    total = tot.get(c, np.nan)
    p65_2030 = (a*2030 + b)/100 * total
    need_2030 = p65_2030/1000 * target_bed_per_1000
    drec.append({
        "縣市": c,
        "老年比率_2025%": round(a*2025+b, 2),
        "老年比率_2030預估%": round(a*2030+b, 2),
        "老年人口_2025": int(m.set_index('縣市').loc[c, '老年人口_65歲以上']),
        "老年人口_2030預估": int(p65_2030),
        "現有核定床數": int(beds_now.get(c, 0)),
        "2030維持中位服務所需床數": int(need_2030),
        "2030床位缺口": int(need_2030 - beds_now.get(c, 0)),
    })
dem = pd.DataFrame(drec).sort_values("2030床位缺口", ascending=False)
dem.to_csv(os.path.join(OUT, "forecast_bed_demand_2030.csv"), index=False, encoding="utf-8-sig")
print("床位目標(中位) = %.1f 床/千名老人 ; 假設總人口維持2025水準" % target_bed_per_1000)
print(dem.to_string(index=False))
print(">> 已輸出 forecast_bed_demand_2030.csv")

# ---------------------------------------------------------------
# 7) 真實供需缺口：整合長照服務涵蓋率(以失能推估需求為分母) + ABC 據點
#    並建立多維度脆弱度指數，修正「只看床位密度」的偏誤
# ---------------------------------------------------------------
log("STEP7 服務涵蓋率整合 + 多維度脆弱度指數")
cov_path = os.path.join(OUT, "ltc_coverage.csv")
res_path = os.path.join(OUT, "ltc_resources.csv")
if os.path.exists(cov_path):
    cov = pd.read_csv(cov_path)
    res = pd.read_csv(res_path) if os.path.exists(res_path) else None
    m2 = m.merge(cov, on="縣市", how="left")
    if res is not None:
        m2 = m2.merge(res[["縣市", "A整合中心_實際", "A達成率%", "B特約單位_實際", "C巷弄站_實際"]], on="縣市", how="left")

    # 多維度脆弱度（z-score，越高越需關注）
    def z(s, invert=False):
        s = pd.to_numeric(s, errors="coerce")
        zz = (s - s.mean()) / s.std(ddof=0)
        return -zz if invert else zz

    m2["風險_未滿足需求"] = z(m2["未滿足需求比例%"])              # 涵蓋率越低越危險（主軸）
    m2["風險_深度老化"] = z(m2["高齡人口比例%"])                  # 75+ 比例越高越危險
    m2["風險_整合資源不足"] = z(m2["A達成率%"], invert=True)        # A整合中心達成率越低越危險(偏鄉布建/人力困難)
    m2["脆弱度指數"] = (m2[["風險_未滿足需求", "風險_深度老化", "風險_整合資源不足"]].mean(axis=1)).round(3)
    m2["脆弱度排名"] = m2["脆弱度指數"].rank(ascending=False).astype(int)
    m2["涵蓋率缺口排名"] = m2["長照服務涵蓋率%"].rank(ascending=True).astype(int)

    m2 = m2.sort_values("脆弱度指數", ascending=False).reset_index(drop=True)
    m2.to_csv(os.path.join(OUT, "county_master.csv"), index=False, encoding="utf-8-sig")

    # 兩種觀點對照表：床位密度排名 vs 涵蓋率排名
    cmp = m2[["縣市", "長照服務涵蓋率%", "未滿足需求比例%", "每千名老人核定床數",
              "供給不足缺口排名", "涵蓋率缺口排名", "脆弱度排名"]].copy()
    cmp = cmp.rename(columns={"供給不足缺口排名": "床位密度缺口排名(舊)"})
    cmp.to_csv(os.path.join(OUT, "risk_comparison.csv"), index=False, encoding="utf-8-sig")
    print("以『長照服務涵蓋率』衡量，最未滿足(前8)：")
    print(m2.nsmallest(8, "長照服務涵蓋率%")[["縣市", "長照服務涵蓋率%", "每千名老人核定床數", "脆弱度排名"]].to_string(index=False))
    print(">> 已更新 county_master.csv（含涵蓋率/脆弱度）並輸出 risk_comparison.csv")
else:
    print("WARN 尚未產生 ltc_coverage.csv，請先執行 scripts/parse_ltc_pdfs.py")

log("完成")
