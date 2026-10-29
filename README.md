# Species123

臺灣物種圖誌：以 [TaiCOL 臺灣物種名錄](https://taicol.tw/) 為資料來源的公開物種網站（類似生物誌 biota）。
網址：<https://species123.naturedb.org>

版面參考 *Atlas of Life* 原型（MUSUBii CSS）：首頁、搜尋（分面篩選）、分類樹、物種頁（圖鑑／資料表／文章，預設圖鑑）、比較。

## 架構

- Flask + Jinja（伺服器端渲染），中文為主、可切換英文（`?lang=en`）
- SQLite 唯讀資料庫 `data/species123.sqlite`，由匯入程式從 TaiCOL API 建立
- [TBIA 生物多樣性資料庫共通查詢系統](https://tbiadata.tw/)的出現紀錄連結直接以 TaiCOL ID 查詢；物種頁的「標本」分頁以 [TBIA API](https://tbiadata.tw/zh-hant/api/doc)（`isCollection=true&hasMedia=image`）取得有影像的自然史典藏，臺灣典藏單位優先、最多 24 筆，快取於 `data/cache.sqlite`（30 天）
- 外部連結（GBIF、iNaturalist、eBird、xeno-canto、Wikidata）來自 [Wikidata](https://www.wikidata.org/)：以 TaiCOL ID（P12218）一次查詢取得；沒有 TaiCOL ID 的屬以下分類群，改以學名（P225）找 Wikidata 項目，須學名、階層（P105）與所屬科皆相同、項目本身沒有 TaiCOL ID，且只有一個符合，存於 `data/raw/wikidata.json`，`import_taicol.py wikidata` 可單獨更新。Wikidata 沒有的 GBIF、iNaturalist 連結，於物種頁以學名比對補上（須與 TaiCOL 有效名完全相同且同界），結果快取於 `data/cache.sqlite`；每個連結都標示依據（Wikidata／學名比對）
- 物種描述取自[維基百科](https://www.wikipedia.org/)（CC BY-SA 4.0）：經由該物種的 Wikidata 項目找到中文（臺灣正體）或英文條目，依頁面語言優先，取條目摘要，於物種頁瀏覽時抓取並快取 30 天；亞種、變種、品型沒有自己的條目時，改用所屬物種的條目並註明；沒有 Wikidata 項目的物種不顯示描述
- 維管束植物的生活型、氣候帶、全球分布範圍、分布地圖與 POWO／IPNI 連結取自 [WCVP 世界維管束植物名錄](https://powo.science.kew.org/about-wcvp)（Kew）：`scripts/import_wcvp.py` 讀 `data/wcvp/`（WCVP 下載的 `wcvp_names.csv`、`wcvp_distribution.csv`，加上 `scripts/match_wcvp.py` 以 [gnparser](https://github.com/gnames/gnparser) 標準化學名後產生的 TaiCOL→WCVP 對應表 `taicol-wcvp-mapping.csv`），產生 `data/raw/wcvp.json`，`build` 時載入；對應到 WCVP 異名者採其接受名並於物種頁註明。地圖底圖 `app/static/wgsrpd-l3.svg` 由 `scripts/build_wgsrpd_svg.py` 從 [WGSRPD](https://github.com/tdwg/wgsrpd) 第三級 GeoJSON 產生
- 植物連到[自然攝影中心典藏版](https://nc-archive.naturedb.org/)植物索引（小圖連大圖）的照片文章：`data/nc/nc_plant_checklist.csv`（從論壇備份整理的索引）於 `build` 時以學名對應 TaiCOL 植物有效名，對不到再比對 TaiCOL 異名，存於 `xref`（`source='nc'`）；原 `nc.naturedb.org/bbs/` 網址改連 `nc-archive.naturedb.org/bbs/`，由典藏版轉址到對應文章
- 文獻在物種頁即時向 TaiCOL 取得；照片取自 iNaturalist（僅 CC 授權照片，附作者標示）。兩者都快取於 `data/cache.sqlite`（30 天）
- MUSUBii 9.4.0 CSS（Docker build 時由 npm 取得），少量原生 JS（深淺色、比較清單、分類樹展開）

```
app/            Flask app (routes in __init__.py, SQL in queries.py, zh/en strings in i18n.py)
scripts/        import_taicol.py, match_wcvp.py, import_wcvp.py, build_wgsrpd_svg.py
data/           species123.sqlite, cache.sqlite, raw/ (API pages, wcvp.json), wcvp/ (WCVP files), nc/ (Nature Campus plant index) — not in git
```

## 執行

```sh
docker compose build

# 1. 匯入 TaiCOL（約 460 次 API 請求、20–30 分鐘；中斷後重跑會從斷點繼續）
docker compose run --rm app python scripts/import_taicol.py          # fetch + build
docker compose run --rm app python scripts/import_taicol.py build    # 只用 data/raw/ 重建資料庫

# 1b. WCVP（維管束植物）：WCVP 下載檔放 data/wcvp/，對應學名後匯入，再 build
docker compose run --rm app python scripts/match_wcvp.py names       # 待解析的學名清單
docker run --rm -i gnames/gognparser:latest -f compact -C -j 8 < data/wcvp/wcvp-names.txt > data/wcvp/wcvp-parsed.jsonl
docker run --rm -i gnames/gognparser:latest -f compact -C -j 8 < data/wcvp/taicol-names.txt > data/wcvp/taicol-parsed.jsonl
docker compose run --rm app python scripts/match_wcvp.py match       # → data/wcvp/taicol-wcvp-mapping.csv
docker compose run --rm app python scripts/import_wcvp.py            # → data/raw/wcvp.json
docker compose run --rm app python scripts/import_taicol.py build

# 2. 開發（flask --debug，原始碼即時重載）
docker compose up
# → http://localhost:8000

# 正式環境（gunicorn，不掛載原始碼）
docker compose -f compose.yml up -d

# 部署（linode：已有 Traefik，自動 HTTPS，https://species123.naturedb.org）
docker compose -f compose.yml -f compose.traefik.yml up -d --build
```

Google Analytics：在主機的 `.env`（不進 git）設定 `SPECIES123_GA_ID=G-XXXXXXXXXX` 後重啟；未設定則不載入追蹤碼。

更新資料：刪除 `data/raw/` 後重新執行匯入；新資料庫建好後才會原子替換舊檔，網站不需停機。

## 頁面

| 路徑 | 說明 |
|---|---|
| `/` | 首頁：搜尋、今日物種、圖鑑、常用類群、依界瀏覽、最近更新 |
| `/gallery`、`/gallery/<key>?show=taiwan\|endemic\|native\|alien\|all` | 圖鑑：依科排列的物種照片卡片，預設只列在臺灣的物種；圖鑑清單在 `app/galleries.py`，加一行即新增一本 |
| `/search?q=&kingdom=&rank=&endemic=&alien=&redlist=&protected=&under=&sort=&page=` | 搜尋與分面篩選；`under=<taxon_id>` 限定某分類群之下 |
| `/taxonomy?node=<taxon_id>` | 分類樹（下層延遲載入：`/taxonomy/children/<taxon_id>`） |
| `/taxon/<taxon_id>?layout=sheet\|article` | 物種／分類群頁（預設圖鑑版面；分頁 `#overview` `#photos` `#taxonomy` `#biology` `#refs` `#specimens`） |
| `/names`（POST `text`，`format=csv` 下載） | 學名擷取：貼上文字，找出學名並比對 TaiCOL 有效名，依科整理成名錄 |
| `/wcvp-taiwan?show=differs\|wcvp_absent&format=csv` | WCVP 臺灣狀態比對：TaiCOL 原生／外來與 WCVP 臺灣（TAI）分布紀錄不一致的種與種下分類群（栽培植物沒有 WCVP 紀錄不算不一致），可下載 CSV |
| `/compare?ids=a,b,c,d` | 最多 4 個分類群並列比較 |
| `/about` | 關於：網站如何使用開放資料（TaiCOL、Wikidata、iNaturalist、維基百科） |
