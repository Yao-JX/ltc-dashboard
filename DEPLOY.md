# 部署教學 — 讓所有人用公開網址開啟儀表板

使用 **Streamlit Community Cloud**（免費），完成後會得到一個像
`https://你的專案.streamlit.app` 的公開網址，任何人點開即可使用。

---

## 需要準備

1. 一個 **GitHub 帳號**（免費）：https://github.com
2. 電腦已安裝 **Git**：https://git-scm.com/downloads
   - 檢查：`git --version` 有顯示版本就 OK。

---

## 步驟一：把專案推上 GitHub

在專案資料夾開啟 CMD：

```cmd
cd C:\Users\y\03-SQL_Demo\0618

git init
git add .
git commit -m "長照供需分析儀表板"
git branch -M main
```

到 GitHub 點右上角 **+ → New repository**：
- Repository name：例如 `ltc-dashboard`
- 選 **Public**（公開，這樣別人才能用）
- **不要**勾 Add README（本機已有）
- 按 **Create repository**

回到 CMD，把下面 `<你的帳號>` 換成自己的：

```cmd
git remote add origin https://github.com/<你的帳號>/ltc-dashboard.git
git push -u origin main
```

> 第一次 push 會要求登入 GitHub（依畫面授權即可）。

---

## 步驟二：在 Streamlit Cloud 部署

1. 開啟 **https://share.streamlit.io** ，用 GitHub 帳號登入。
2. 按 **Create app → Deploy a public app from GitHub**。
3. 填寫：
   - **Repository**：`<你的帳號>/ltc-dashboard`
   - **Branch**：`main`
   - **Main file path**：`app.py`
4. 按 **Deploy**，等待 2–5 分鐘安裝套件。
5. 完成後會給你公開網址 `https://xxxx.streamlit.app` —— 把這個網址分享給任何人即可使用。

---

## 之後要更新內容

只要在本機改好，重新推上去，Streamlit Cloud 會**自動重新部署**：

```cmd
git add .
git commit -m "更新資料/圖表"
git push
```

---

## 部署必備檔案（已備妥，務必一起 push）

| 檔案 | 為何需要 |
|---|---|
| `app.py` | 主程式（Main file path） |
| `requirements.txt` | 雲端依此安裝套件 |
| `data/processed/*.csv` | App 讀取的資料表 |
| `assets/tw_counties.json` | 地圖檔 |
| `.streamlit/config.toml` | 介面設定 |

---

## 疑難排解

- **部署失敗、卡在安裝套件**：到 app 頁面右下角看 **Manage app → Logs**。
  多半是某套件裝不起來；可把 `requirements.txt` 精簡成 App 真正需要的：
  ```
  streamlit
  plotly
  pandas
  ```
  （`matplotlib / pdfplumber / xlrd / openpyxl` 只有跑 notebook 才需要，雲端 App 不必。）
- **App 顯示找不到檔案**：確認 `data/processed/` 與 `assets/` 有被 `git push` 上去
  （`git status` 看是否有未追蹤檔；`.gitignore` 並未忽略這兩個資料夾）。
- **想關閉/重啟**：在 https://share.streamlit.io 的 app 清單可 Reboot / Delete。
