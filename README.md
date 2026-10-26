# Species123

臺灣物種圖誌：以 [TaiCOL 臺灣物種名錄](https://taicol.tw/) 為資料來源的公開物種網站（類似生物誌 biota）。
網址：<https://species123.naturedb.org>

版面參考 *Atlas of Life* 原型（MUSUBii CSS）：首頁、搜尋（分面篩選）、分類樹、物種頁（圖鑑／資料表／文章，預設圖鑑）、比較。

## 架構

- Flask + Jinja（伺服器端渲染），中文為主、可切換英文（`?lang=en`）
- SQLite 唯讀資料庫 `data/species123.sqlite`，由匯入程式從 TaiCOL API 建立
- 文獻在物種頁即時向 TaiCOL 取得；照片取自 iNaturalist（僅 CC 授權照片，附作者標示）。兩者都快取於 `data/cache.sqlite`（30 天）
- MUSUBii 9.4.0 CSS（Docker build 時由 npm 取得），少量原生 JS（深淺色、比較清單、分類樹展開）

```
app/            Flask app (routes in __init__.py, SQL in queries.py, zh/en strings in i18n.py)
scripts/        import_taicol.py
data/           species123.sqlite, cache.sqlite, raw/ (API pages) — not in git
```

## 執行

```sh
docker compose build

# 1. 匯入 TaiCOL（約 460 次 API 請求、20–30 分鐘；中斷後重跑會從斷點繼續）
docker compose run --rm app python scripts/import_taicol.py          # fetch + build
docker compose run --rm app python scripts/import_taicol.py build    # 只用 data/raw/ 重建資料庫

# 2. 開發（flask --debug，原始碼即時重載）
docker compose up
# → http://localhost:8000

# 正式環境（gunicorn，不掛載原始碼）
docker compose -f compose.yml up -d
```

更新資料：刪除 `data/raw/` 後重新執行匯入；新資料庫建好後才會原子替換舊檔，網站不需停機。

## 頁面

| 路徑 | 說明 |
|---|---|
| `/` | 首頁：搜尋、依界瀏覽、最近更新 |
| `/search?q=&kingdom=&rank=&endemic=&alien=&redlist=&protected=&under=&sort=&page=` | 搜尋與分面篩選；`under=<taxon_id>` 限定某分類群之下 |
| `/taxonomy?node=<taxon_id>` | 分類樹（下層延遲載入：`/taxonomy/children/<taxon_id>`） |
| `/taxon/<taxon_id>?layout=sheet\|article` | 物種／分類群頁（預設圖鑑版面；分頁 `#overview` `#taxonomy` `#distribution` `#names` `#refs`） |
| `/names`（POST `text`，`format=csv` 下載） | 學名擷取：貼上文字，找出學名並比對 TaiCOL 有效名，依科整理成名錄 |
| `/compare?ids=a,b,c,d` | 最多 4 個分類群並列比較 |
