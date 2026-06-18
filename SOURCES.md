# 資料來源清單

所有資料皆取自政府公開平臺，採政府資料開放授權（多為 OGDL-Taiwan 1.0 / CC BY 4.0）。
下載日期：2026-06-18。

| # | 資料名稱 | 提供機關 | 來源 | 檔案 |
| --- | --- | --- | --- | --- |
| 1 | 村里戶數、單一年齡人口（新增區域代碼） | 內政部戶政司 | data.gov.tw dataset **77132**<br>https://data.gov.tw/dataset/77132 | `77132_pop_single_age_latest.csv`（每月更新，程式自動抓最新月份，彙總至縣市；分析主用） |
| 1b | 人口數單一年齡組─按性別、區域別分 | 內政部 | data.gov.tw dataset **14226**<br>https://data.gov.tw/dataset/14226 | `14226_population_single_age.csv`（2020/民國109，歷史對照用） |
| 2 | 各縣市老化指數（含老年比率、扶老/扶養比，歷年） | 內政部戶政司 | https://www.ris.gov.tw/app/portal/346 （人口統計資料 → 年齡結構） | `ris_aging_index_by_county.xls`（2010–2025） |
| 3 | 身心障礙者人數按年齡及縣市別分 | 衛生福利部統計處 | 身心障礙統計專區<br>https://dep.mohw.gov.tw/dos/cp-5224-62359-113.html | `disability_by_age_county.xls`（含 2015–2025 各年分頁） |
| 4 | 身心障礙者人數按類別及縣市別分 | 衛生福利部統計處 | 同上 | `disability_by_type_county.xls` |
| 5 | 全國老人福利機構名冊（含核定床數） | 衛生福利部社會及家庭署 | data.gov.tw dataset **8572**<br>https://data.gov.tw/dataset/8572 | `elderly_institutions_8572/`（22 縣市，Big5 編碼） |
| 6 | 長照十年計畫2.0－長照服務涵蓋率（各縣市，以失能推估需求為分母） | 衛生福利部長期照顧司 | 長照專區統計表 表(三)<br>https://1966.gov.tw/LTC/lp-6485-207.html | `ltc_coverage_rate.pdf`（113年；pdfplumber 解析） |
| 7 | 各縣市長照資源布建（A整合中心/B特約單位/C巷弄站 目標vs實際） | 衛生福利部長期照顧司 | 長照專區統計表 表(十六)<br>https://1966.gov.tw/LTC/lp-6485-207.html | `ltc_county_resources.pdf`（114/12/31；pdfplumber 解析） |

## 備註
- 內政部 data.gov.tw 資料可用 API 取得 distribution 下載連結：
  `https://data.gov.tw/api/v2/rest/dataset/{id}`（GET）。
- 國發會「人口推計」(dataset 6101，https://data.gov.tw/dataset/6101 ) 提供全國未來人口推估，
  但其下載端點 (pop-proj.ndc.gov.tw) 會擋程式化下載（HTTP 403）；
  本專題改以戶政司老化指數時間序列自建縣市別線性預測。如需 NDC 官方推估可手動下載。
- dataset 77132 含 101 個月份資源且未依時間排序；本專題以分段請求(curl Range)掃描各檔
  `statistic_yyymm` 取最新期別（**11505 = 民國114年5月**）全檔下載後彙總至縣市。
- 機構名冊原始檔為 **Big5 (CP950)** 編碼，讀取時需指定 `encoding="big5"`。
- 縣市界 geojson 取自 g0v `twgeojson`（COUNTYNAME 用「台」與「桃園縣」，程式已正規化為「臺」「桃園市」）。
- 衛福部身障 Excel 雖副檔名為 `.xls`，實際為 `.xlsx` (OOXML)，以 openpyxl 讀取。
