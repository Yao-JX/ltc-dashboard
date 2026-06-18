# -*- coding: utf-8 -*-
"""在 notebook 結論前插入『長照服務涵蓋率修正分析』章節，並更新結論。"""
import nbformat as nbf
from nbformat.v4 import new_markdown_cell, new_code_cell

NB = r"C:\Users\y\03-SQL_Demo\0618\長照供需分析.ipynb"
nb = nbf.read(NB, as_version=4)

md_intro = """## 十、修正分析：用「長照服務涵蓋率」檢視真實供需缺口

> **為什麼要修正？** 前面用「每千名老人核定床數」當供給指標有兩個結構性偏誤：
> 1. **沒算照護人力**——床位是死的，沒有照服員，床位再多也是空的（偏鄉常「有床無人顧」）。
> 2. **比率會騙人**——偏鄉老人絕對數少，只要一兩家機構，每千老人床數就很高，被誤判為「充足」。
>
> 衛福部長照 2.0 以 **失能推估需求人數** 為分母的「**長照服務涵蓋率**」是更貼近真實的供需指標：
> 分子為實際使用長照服務的人數（內含居家/社區/機構各式服務），間接反映人力是否到位。
> 涵蓋率越低 = 需求未被滿足越嚴重。"""

code_dl = """# 下載衛福部長照專區 PDF（涵蓋率、ABC據點），已存在則略過\n# !pip install pdfplumber\nimport pdfplumber\n_pdfs = {\n    'ltc_coverage_rate.pdf': 'https://www.mohw.gov.tw/dl-88608-9d7a650b-ac63-43cb-a469-7d1cb37a2d77.html',\n    'ltc_county_resources.pdf': 'https://www.mohw.gov.tw/dl-89795-52476cf8-4945-4713-9053-80ea95723d9d.html',\n}\nfor fn, url in _pdfs.items():\n    p = os.path.join(RAW, fn)\n    if not (os.path.exists(p) and os.path.getsize(p) > 1000):\n        with open(p, 'wb') as f:\n            f.write(get(url, {'Referer': 'https://1966.gov.tw/'}, timeout=120))\n    print(fn, '就緒')"""

code_parse = """# 解析 PDF → 涵蓋率 / ABC據點，並合併進主表\ndef _num(s): return float(s.replace(',', '').replace('%', ''))\n\ncov_rows = []\nwith pdfplumber.open(os.path.join(RAW, 'ltc_coverage_rate.pdf')) as pdf:\n    for pg in pdf.pages:\n        for ln in (pg.extract_text() or '').split('\\n'):\n            t = ln.split()\n            if len(t) >= 7 and ''.join(t[:-6]) in COUNTIES:\n                cov_rows.append({'縣市': ''.join(t[:-6]),\n                                 '長照推估需求人數': int(_num(t[-6])),\n                                 '長照服務涵蓋率%': round(_num(t[-1]), 2),\n                                 '未滿足需求比例%': round(100 - _num(t[-1]), 2)})\ncov = pd.DataFrame(cov_rows).drop_duplicates('縣市')\n\nres_rows = []\nwith pdfplumber.open(os.path.join(RAW, 'ltc_county_resources.pdf')) as pdf:\n    for pg in pdf.pages:\n        for ln in (pg.extract_text() or '').split('\\n'):\n            t = ln.split()\n            if len(t) >= 10 and ''.join(t[:-9]) in COUNTIES:\n                v = [_num(x) for x in t[-9:]]\n                res_rows.append({'縣市': ''.join(t[:-9]), 'A達成率%': round(v[2], 1),\n                                 'B特約單位_實際': int(v[4]), 'C巷弄站_實際': int(v[7])})\nres = pd.DataFrame(res_rows).drop_duplicates('縣市')\n\nm = m.merge(cov, on='縣市', how='left').merge(res, on='縣市', how='left')\n\ndef _z(s, invert=False):\n    s = pd.to_numeric(s, errors='coerce'); zz = (s - s.mean()) / s.std(ddof=0)\n    return -zz if invert else zz\nm['脆弱度指數'] = (pd.concat([_z(m['未滿足需求比例%']), _z(m['高齡人口比例%']),\n                          _z(m['A達成率%'], invert=True)], axis=1).mean(axis=1)).round(3)\nm['涵蓋率缺口排名'] = m['長照服務涵蓋率%'].rank(ascending=True).astype(int)\nm.to_csv(os.path.join(PROC, 'county_master.csv'), index=False, encoding='utf-8-sig')\nm[['縣市', '長照推估需求人數', '長照服務涵蓋率%', '未滿足需求比例%', '每千名老人核定床數', '脆弱度指數']].sort_values('長照服務涵蓋率%')"""

code_chart = """# 涵蓋率排名 + 涵蓋率地圖 + 新舊觀點對照\nd = m.sort_values('長照服務涵蓋率%')\nfig, ax = plt.subplots(figsize=(10, 8))\ncolors = ['#d62728' if v < 80 else ('#ff7f0e' if v < 100 else '#2ca02c') for v in d['長照服務涵蓋率%']]\nax.barh(d['縣市'], d['長照服務涵蓋率%'], color=colors)\nax.axvline(100, color='green', ls='--'); ax.axvline(80, color='red', ls=':')\nfor i, v in enumerate(d['長照服務涵蓋率%']):\n    ax.text(v + 1, i, f'{v:.0f}%', va='center', fontsize=9, fontproperties=FONT)\nax.set_title('各縣市長照服務涵蓋率（紅<80%＝未滿足高）', fontproperties=FONT, fontsize=14)\nfor lab in ax.get_yticklabels(): lab.set_fontproperties(FONT)\nplt.tight_layout(); plt.savefig(os.path.join(OUT, '08_coverage_rate_ranking.png'), dpi=130); plt.show()\n\ndraw_map('長照服務涵蓋率%', '各縣市長照服務涵蓋率（紅=未滿足高 綠=已滿足）', '09_map_coverage_rate.png', 'RdYlGn')\n\nfig, ax = plt.subplots(figsize=(9, 9))\nbed_rank = m['每千名老人核定床數'].rank(ascending=True).astype(int)\nax.scatter(bed_rank, m['涵蓋率缺口排名'], s=60, color='#1f77b4')\nfor i, r in m.reset_index(drop=True).iterrows():\n    ax.annotate(r['縣市'], (bed_rank.iloc[i], r['涵蓋率缺口排名']), fontsize=8,\n                xytext=(4, 2), textcoords='offset points', fontproperties=FONT)\nax.plot([1, 22], [1, 22], '--', color='gray')\nax.set_xlabel('床位密度缺口排名（舊，1=最不足）', fontproperties=FONT)\nax.set_ylabel('涵蓋率缺口排名（1=最未滿足）', fontproperties=FONT)\nax.set_title('兩種缺口觀點對照（偏離對角線=結論不同）', fontproperties=FONT, fontsize=14)\nplt.tight_layout(); plt.savefig(os.path.join(OUT, '10_rank_comparison.png'), dpi=130); plt.show()"""

md_disc = """### 修正後的發現（誠實校正）

用「長照服務涵蓋率」（以失能推估需求為分母）重新檢視，結論與「只看床位密度」**幾乎相反**：

| 觀點 | 最危險（前幾名） | 看似安全 |
| --- | --- | --- |
| 舊：每千名老人床位密度 | 臺中、新竹市、臺北、苗栗、桃園（都會） | 嘉義市、宜蘭、基隆、臺東 |
| 新：長照服務涵蓋率 | **連江 33%、金門 43%、臺北 58%、基隆 70%、新竹市 77%、桃園 78%** | **臺東 112%、花蓮 109%、嘉義縣 115%、屏東 106%** |

**三個重點：**

1. **離島最危險（你的直覺正確）**：連江 33.5%、金門 43.3% 涵蓋率全國墊底，正因人口少、難布建 A 整合中心（連江 A 達成率 0%、金門 40%）、難留照護人力——這正是「老人少但沒人顧」的寫照。舊的床位指標完全漏掉它們。

2. **東部、南部其實涵蓋良好（與直覺相反）**：臺東、花蓮、嘉義、屏東、南投涵蓋率都 >100%，因長照 2.0 在當地 ABC 據點布建積極（達成率常 200%~500%）、戶籍需求基數較小、且有跨縣市機構使用。**所以「南部/東部更危險」在這份資料上不成立。**

3. **真正高風險是「離島 + 北部都會圈」**：臺北 58%（第 3 低）、基隆 70%、桃園 78%、新北 80%、新竹市 77%——都會的缺口是真的，但成因是龐大需求 + 都會居民多用外勞/自費而非長照 2.0 給付，與我原本「床位太少」的解讀不同。

> **方法反省**：單一比率指標（尤其分母用老人數）很容易誤導；應以「**失能需求 vs 實際服務遞送**」的涵蓋率為主軸，並輔以深度老化、整合資源布建（A 達成率）等多維度脆弱度，才能避免把都會的稀釋效應或偏鄉的小基數效應誤判為供需結論。"""

# 找到結論 cell（含 "結論與政策建議"）並在其前插入
concl_idx = None
for i, c in enumerate(nb.cells):
    if c.cell_type == "markdown" and "結論與政策建議" in c.source:
        concl_idx = i
        break
assert concl_idx is not None, "找不到結論 cell"

new_cells = [
    new_markdown_cell(md_intro),
    new_code_cell(code_dl),
    new_code_cell(code_parse),
    new_code_cell(code_chart),
    new_markdown_cell(md_disc),
]
nb.cells[concl_idx:concl_idx] = new_cells

# 更新結論編號與內容
nb.cells[concl_idx + len(new_cells)].source = """## 十一、結論與政策建議（修正版）

**以「長照服務涵蓋率」(失能需求 vs 實際服務) 為主軸的真實供需缺口：**

- **最高風險 = 離島 + 北部都會圈**：連江(33%)、金門(43%)、臺北(58%)、基隆(70%)、新竹市(77%)、桃園(78%)、苗栗(78%)、新北(80%)。
- **離島**因規模小、布建難、人力難留，是結構性最弱環節（連江 A 整合中心達成率 0%）。
- **北部都會**缺口來自龐大需求與長照 2.0 給付使用率偏低。
- **東部、南部反而涵蓋良好**（臺東/花蓮/嘉義/屏東/南投 >100%），長照 2.0 布建已見成效。

**政策建議**：
1. **離島**：採在地培力 + 跨縣市支援 + 遠距/巡迴照護，補 A/C 據點與人力缺口。
2. **北部都會**：提升長照 2.0 給付服務使用率、銜接外勞與正式服務、擴居家/社區量能。
3. 資源配置應以「**涵蓋率**」與「**失能需求成長**」為依據，而非單純床位數。

**限制**：涵蓋率分母為戶籍失能推估、分子依實際服務地計算，跨縣市使用會使部分縣市 >100%；
床位數僅機構住宿式供給；本分析未能取得各縣市「照顧服務員實際在職人數」之開放資料，
以涵蓋率與 A 整合中心達成率作為人力到位的間接代理指標。"""

nbf.write(nb, NB)
print("已插入 %d 個 cell，結論已更新。總 cell 數 = %d" % (len(new_cells), len(nb.cells)))
