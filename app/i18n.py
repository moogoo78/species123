"""zh-TW (default) / English UI strings and TaiCOL code labels."""
import re

LANGS = ('zh', 'en')
DEFAULT_LANG = 'zh'

STRINGS = {
    'site_name': ('Species123', 'Species123'),
    'site_tagline': ('臺灣物種圖鑑', 'Field guide to Taiwan species'),
    'nav_search': ('搜尋', 'Search'),
    'nav_taxonomy': ('分類樹', 'Taxonomy'),
    'nav_compare': ('比較', 'Compare'),
    'nav_names': ('學名擷取', 'Name extractor'),
    'nav_gallery': ('圖鑑', 'Field guides'),
    'nav_tools': ('工具', 'Tools'),
    'nav_names_hint': ('貼上文字，找出學名並比對名錄', 'Paste text, find and check scientific names'),
    'nav_compare_hint': ('最多 4 個分類群並列比較', 'Compare up to 4 taxa side by side'),
    'galleries': ('圖鑑', 'Field guides'),
    'galleries_lead': ('依類群整理的物種照片圖鑑，照片來自 iNaturalist，名錄來自臺灣物種名錄。',
                       'Photo field guides by group: photos from iNaturalist, names from TaiCOL.'),
    'gallery_not_found_hint': ('沒有這本圖鑑，請從圖鑑列表選擇。', 'There is no such field guide — pick one from the list.'),
    'gallery_show_taiwan': ('在臺灣', 'In Taiwan'),
    'gallery_show_endemic': ('特有', 'Endemic'),
    'gallery_show_native': ('原生', 'Native'),
    'gallery_show_alien': ('外來', 'Alien'),
    'gallery_show_all': ('全部（含臺灣以外）', 'All (incl. outside Taiwan)'),
    'gallery_families': ('科', 'Families'),
    'gallery_count': ('{n} 種', '{n} species'),
    'gallery_view': ('在圖鑑中查看', 'View in field guide'),
    'gallery_no_photo': ('尚無照片', 'No photo yet'),
    'gallery_credit': ('名錄：臺灣物種名錄 TaiCOL · 照片：iNaturalist，依各照片授權', 'Names: TaiCOL · Photos: iNaturalist, under each photo’s licence'),
    'names_lead': ('貼上文章、報告或調查紀錄，自動找出其中的學名，比對 TaiCOL 有效名並整理成名錄。',
                   'Paste an article, report or survey notes: scientific names are picked out, matched to TaiCOL accepted names, and listed as a checklist.'),
    'names_placeholder': ('例：臺灣黑熊（Ursus thibetanus formosanus）常見於中高海拔森林，林下可見 Begonia formosana…',
                          'e.g. The Formosan black bear (Ursus thibetanus formosanus) lives in montane forest, where Begonia formosana grows…'),
    'names_btn': ('擷取學名', 'Extract names'),
    'names_csv': ('下載 CSV', 'Download CSV'),
    'names_summary': ('比對到 {n} 個分類群（{s} 個種與種下）', '{n} taxa matched ({s} species and below)'),
    'names_none': ('沒有找到可比對的學名', 'No matching scientific names found'),
    'names_none_hint': ('只會比對拉丁學名（如 Begonia formosana），且目前僅收錄 TaiCOL 有效名，異名無法比對。',
                        'Only Latin names (e.g. Begonia formosana) are matched, against TaiCOL accepted names only — synonyms are not recognised.'),
    'names_unmatched': ('未比對到的名稱', 'Names not matched'),
    'names_unmatched_hint': ('可能是異名、拼字差異或臺灣未記錄的物種。', 'Possibly a synonym, a spelling variant, or not recorded in Taiwan.'),
    'col_verbatim': ('原文', 'As written'),
    'col_count': ('次數', 'Count'),
    'higher_taxa': ('高階分類群', 'Higher taxa'),
    'partial_match': ('僅比對到上層', 'Matched at a higher rank'),
    'theme': ('切換深淺色', 'Toggle theme'),
    'menu': ('選單', 'Menu'),
    'lang_switch': ('EN', '中文'),
    'hero_badge': ('臺灣物種名錄 TaiCOL · {n} 個有效分類群', 'Taiwan Catalogue of Life · {n} accepted taxa'),
    'hero_lead': ('有效學名、中文名、分類階層、特有性與保育等級，資料來自臺灣物種名錄。',
                  'Accepted names, Chinese names, classification, endemism and conservation status from TaiCOL.'),
    'search_placeholder': ('水鴨腳、Begonia、臺灣黑熊、蘭科…', 'Begonia formosana, Ursus, Orchidaceae…'),
    'search_btn': ('搜尋', 'Search'),
    'browse_kingdom': ('依界瀏覽', 'Browse by kingdom'),
    'taxonomy_tree': ('分類樹', 'Taxonomy tree'),
    'species_count': ('{n} 種', '{n} species'),
    'daily': ('今日物種', 'Species of the day'),
    'daily_more': ('查看物種', 'View species'),
    'recent': ('最近更新', 'Recently revised'),
    'all_records': ('所有紀錄', 'All records'),
    'filters': ('篩選', 'Filters'),
    'f_group': ('常用類群', 'Common groups'),
    'common_groups': ('常用類群', 'Common groups'),
    'f_kingdom': ('界', 'Kingdom'),
    'f_rank': ('階層', 'Rank'),
    'f_endemic': ('特有性', 'Endemism'),
    'f_alien': ('原生／外來', 'Native / alien'),
    'f_redlist': ('臺灣紅皮書', 'Taiwan Red List'),
    'f_protected': ('保育類', 'Protected'),
    'endemic': ('臺灣特有', 'Endemic to Taiwan'),
    'not_endemic': ('非特有', 'Not endemic'),
    'n_results': ('{n} 筆分類群', '{n} taxa'),
    'n_results_for': ('「{q}」共 {n} 筆分類群', '{n} taxa for “{q}”'),
    'within': ('範圍：{name}', 'Within {name}'),
    'clear_all': ('清除全部', 'Clear all'),
    'select_up_to': ('最多選 4 筆', 'Select up to 4'),
    'n_selected': ('已選 {n} 筆', '{n} selected'),
    'compare_selected': ('比較所選', 'Compare selected'),
    'col_name': ('學名', 'Scientific name'),
    'col_common': ('中文名', 'Chinese name'),
    'col_family': ('科', 'Family'),
    'col_rank': ('階層', 'Rank'),
    'col_status': ('狀態', 'Status'),
    'col_updated': ('更新', 'Revised'),
    'no_results': ('沒有符合的分類群', 'No taxa match'),
    'no_results_hint': ('請檢查拼字，改用屬名或科名，或清除篩選條件。', 'Check the spelling, try a genus or family, or clear the filters.'),
    'prev': ('上一頁', 'Previous'),
    'next': ('下一頁', 'Next'),
    'page_of': ('第 {p} / {n} 頁', 'Page {p} of {n}'),
    'taxonomy_title': ('分類樹', 'Taxonomy'),
    'taxonomy_lead': ('由總界展開到種與種下分類群。', 'Expand ranks from superkingdom to species.'),
    'collapse_all': ('全部收合', 'Collapse all'),
    'children': ('下層分類群', 'Child taxa'),
    'unplaced': ('未歸類', 'Unplaced'),
    'unplaced_lead': ('臺灣物種名錄尚未提供這些分類群的上層分類（沒有上層分類群與界），待名錄補上後，下次匯入會自動歸位。',
                      'TaiCOL gives these taxa no higher classification yet (no parent and no kingdom); '
                      'they move into place on the next import once TaiCOL fills it in.'),
    'unplaced_note': ('臺灣物種名錄尚未提供此分類群的上層分類', 'TaiCOL has no higher classification for this taxon yet'),
    'more_children': ('還有 {n} 筆，請用「範圍內搜尋」', '{n} more — use “Search within”'),
    'search_within': ('範圍內搜尋', 'Search within'),
    'home': ('首頁', 'Home'),
    'layout_guide': ('圖鑑', 'Field guide'),
    'layout_sheet': ('資料表', 'Data sheet'),
    'distribution': ('分布', 'Distribution'),
    'biology': ('特徵與生態', 'Biology'),
    'photo_slot': ('照片', 'Photo'),
    'photos_credit': ('照片：iNaturalist，依各照片授權', 'Photos: iNaturalist, under each photo’s licence'),
    'more_photos': ('更多照片', 'More photos'),
    'photos': ('照片', 'Photos'),
    'layout_article': ('文章', 'Article'),
    'accepted': ('有效名', 'Accepted'),
    'add_compare': ('加入比較', 'Add to compare'),
    'in_compare': ('已在比較中', 'In comparison'),
    'cite': ('引用', 'Cite'),
    'copied': ('已複製', 'Copied'),
    'view_taicol': ('在 TaiCOL 檢視', 'View on TaiCOL'),
    'view_tbia': ('TBIA 出現紀錄', 'Records on TBIA'),
    'specimens': ('標本', 'Specimens'),
    'specimens_summary': ('TBIA 有 {total} 筆標本，其中 {img} 筆有影像', 'TBIA holds {total} specimens, {img} with images'),
    'specimens_shown': ('，顯示前 {n} 筆', '; showing the first {n}'),
    'specimens_all': ('在 TBIA 查看全部標本', 'All specimens on TBIA'),
    'specimens_no_image': ('這些標本都沒有影像。', 'None of them has an image.'),
    'specimen_image': ('原始影像', 'Full image'),
    'specimen_record': ('TBIA 紀錄', 'TBIA record'),
    'specimens_credit': ('標本資料：TBIA 臺灣生物多樣性資訊聯盟，影像依各典藏單位授權', 'Specimens: Taiwan Biodiversity Information Alliance (TBIA); images under each collection\'s licence'),
    'classification': ('分類', 'Classification'),
    'identifiers': ('識別碼', 'Identifiers'),
    'external_links': ('外部連結', 'External links'),
    'via_wikidata': ('Wikidata', 'Wikidata'),
    'via_taicol_id': ('TaiCOL ID', 'TaiCOL ID'),
    'via_name': ('學名比對', 'Name match'),
    'via_wikidata_name': ('Wikidata（學名比對）', 'Wikidata (name match)'),
    'via_wcvp': ('WCVP', 'WCVP'),
    'via_synonym': ('異名比對', 'Synonym match'),
    'nc_label': ('自然攝影中心', 'Nature Campus'),
    'via_note': ('連結依據：TaiCOL ID（TBIA）、Wikidata（以 TaiCOL ID 對應）、學名比對（與 TaiCOL 有效名完全相同；Wikidata 項目另須階層與科相同），'
                 'WCVP（POWO、IPNI，維管束植物），或異名比對（自然攝影中心植物索引的學名是 TaiCOL 異名）',
                 'Linked via the TaiCOL ID (TBIA), Wikidata (matched on the TaiCOL ID), a name match (identical to the TaiCOL accepted name; '
                 'for Wikidata items, also the same rank and family), WCVP (POWO and IPNI, vascular plants), '
                 'or a synonym match (the Nature Campus plant index uses a TaiCOL synonym)'),
    'key_facts': ('重點資訊', 'Key facts'),
    'description': ('描述', 'Description'),
    'desc_credit': ('內容取自維基百科', 'From Wikipedia'),
    'read_more': ('閱讀全文', 'Read more'),
    'desc_species': ('此分類群沒有自己的條目，以下為所屬物種 {name} 的描述', 'No article of its own; this describes its species, {name}'),
    'lang_zh': ('中文', 'Chinese'),
    'lang_en': ('英文', 'English'),
    'habitat_status': ('棲地與原生性', 'Habitat & status'),
    'common_names': ('俗名', 'Common names'),
    'literature': ('文獻', 'Literature'),
    'none_recorded': ('無紀錄。', 'None recorded.'),
    'refs_credit': ('文獻來源：臺灣物種名錄 TaiCOL', 'Literature: Taiwan Catalogue of Life (TaiCOL)'),
    'refs_unavailable': ('目前無法取得 TaiCOL 文獻資料。', 'Literature from TaiCOL is unavailable right now.'),
    'revised': ('TaiCOL 更新於 {d}', 'Revised on TaiCOL {d}'),
    'on_this_page': ('本頁內容', 'On this page'),
    'overview': ('概要', 'Overview'),
    'primary_name': ('中文名', 'Chinese name'),
    'alt_name': ('別名', 'Alternative name'),
    'fact_rank': ('階層', 'Rank'),
    'fact_author': ('命名者', 'Authority'),
    'fact_in_taiwan': ('臺灣有分布', 'Occurs in Taiwan'),
    'fact_endemic': ('特有性', 'Endemism'),
    'fact_alien': ('原生／外來', 'Native / alien'),
    'fact_alien_note': ('外來狀態備註', 'Alien status note'),
    'fact_habitat': ('棲地類型', 'Habitat type'),
    'fact_fossil': ('化石種', 'Fossil'),
    'fact_iucn': ('IUCN', 'IUCN'),
    'fact_redlist': ('臺灣紅皮書', 'Taiwan Red List'),
    'fact_cites': ('CITES', 'CITES'),
    'fact_protected': ('保育類', 'Protected'),
    'fact_species': ('所含種數', 'Species within'),
    'fact_lifeform': ('生活型', 'Life form'),
    'fact_climate': ('氣候帶', 'Climate'),
    'fact_range': ('全球分布範圍', 'World range'),
    'world_dist': ('全球分布', 'World distribution'),
    'dist_native': ('原生', 'Native'),
    'dist_introduced': ('引進', 'Introduced'),
    'dist_extinct': ('已滅絕', 'Extinct'),
    'dist_doubtful': ('存疑', 'Doubtful'),
    'dist_list': ('分布地區（{n}）', 'Regions ({n})'),
    'dist_note': ('以世界植物分布地理區（WGSRPD 第三級）標示，大致相當於國家或大國的省、州。',
                  'Shown by WGSRPD level-3 region ("botanical country"): roughly a country, or a state or province of a large one.'),
    'wcvp_box': ('WCVP 世界維管束植物名錄', 'World Checklist of Vascular Plants'),
    'wcvp_nav': ('WCVP', 'WCVP'),
    'wcvp_credit': ('資料來源：WCVP（英國皇家植物園邱園），以學名對應 TaiCOL 有效名',
                    'Source: WCVP (Royal Botanic Gardens, Kew), matched to the TaiCOL accepted name by name'),
    'wcvp_as': ('WCVP 採用的接受名為 {name}', 'WCVP accepts this as {name}'),
    'view_powo': ('在 POWO 檢視', 'View on POWO'),
    'fact_wcvp_taiwan': ('臺灣狀態', 'Status in Taiwan'),
    'wcvp_tai_absent': ('無臺灣紀錄', 'Not recorded in Taiwan'),
    'wct_note_differs': ('與 TaiCOL 不同：TaiCOL 列為「{s}」', 'Differs from TaiCOL, which lists it as {s}'),
    'wct_note_wcvp_absent': ('WCVP 沒有臺灣的分布紀錄，TaiCOL 列為「{s}」', 'WCVP has no Taiwan record; TaiCOL lists it as {s}'),
    'wct_see_all': ('所有不一致的植物', 'All mismatches'),
    'nav_wcvp_taiwan': ('WCVP 臺灣狀態比對', 'WCVP Taiwan status check'),
    'nav_wcvp_taiwan_hint': ('原生／外來與 WCVP 分布紀錄不一致的維管束植物', 'Plants whose native / alien status disagrees with WCVP'),
    'wct_lead': ('比對臺灣物種名錄的原生／外來狀態，與 WCVP 世界維管束植物名錄在臺灣（TAI）的分布紀錄。只列在臺灣、有 WCVP 分布資料的種與種下分類群。',
                 'TaiCOL\'s native / alien status compared with the Taiwan (TAI) record in the World Checklist of Vascular Plants. '
                 'Only species and infraspecific taxa in Taiwan that have WCVP distribution data are listed.'),
    'wct_caveat': ('WCVP 接受名與 TaiCOL 不同時，兩邊的分類群範圍可能不同，差異未必是錯誤。栽培植物在 WCVP 沒有臺灣紀錄屬正常，不列入。',
                   'Where WCVP accepts a different name, the two taxon concepts may differ, so a mismatch is not necessarily an error. '
                   'Cultivated plants without a WCVP Taiwan record are expected and not listed.'),
    'wct_differs': ('狀態不同', 'Status differs'),
    'wct_wcvp_absent': ('WCVP 無臺灣紀錄', 'No WCVP Taiwan record'),
    'wct_none': ('沒有不一致的植物。', 'No mismatches.'),
    'col_taicol_status': ('TaiCOL 原生／外來', 'TaiCOL status'),
    'col_wcvp_taiwan': ('WCVP 臺灣', 'WCVP Taiwan'),
    'col_wcvp_name': ('WCVP 接受名', 'WCVP accepted name'),
    'col_family': ('科', 'Family'),
    'yes': ('是', 'Yes'),
    'no': ('否', 'No'),
    'h_terrestrial': ('陸域', 'Terrestrial'),
    'h_freshwater': ('淡水', 'Freshwater'),
    'h_brackish': ('半鹹水', 'Brackish'),
    'h_marine': ('海洋', 'Marine'),
    'compare_title': ('比較', 'Compare'),
    'compare_summary': ('{n} / 4 個分類群 · 標示列為相異處', '{n} of 4 taxa · highlighted rows differ'),
    'compare_same_genus': ('皆屬 {g}', 'all in {g}'),
    'diff_only': ('只顯示相異', 'Differences only'),
    'compare_empty': ('尚未選擇分類群。從搜尋結果勾選，或在物種頁按「加入比較」。', 'Nothing to compare yet. Tick rows in search results, or use “Add to compare” on a species page.'),
    'add': ('加入', 'Add'),
    'remove': ('移除', 'Remove'),
    'g_taxonomy': ('分類', 'Taxonomy'),
    'g_names': ('名稱', 'Names'),
    'g_conservation': ('保育', 'Conservation'),
    'g_ecology': ('生態與分布', 'Ecology & distribution'),
    'about': ('關於', 'About'),
    'about_title': ('Species123 如何使用開放資料', 'How Species123 uses open data'),
    'about_source_code': ('原始碼', 'Source code'),
    'footer_source': ('資料來源：臺灣物種名錄 TaiCOL', 'Data: Taiwan Catalogue of Life (TaiCOL)'),
    'footer_version': ('資料版本 {d}', 'Data as of {d}'),
    'not_found': ('找不到這個分類群', 'Taxon not found'),
    'not_found_hint': ('它可能已被合併或更名，請試試搜尋。', 'It may have been merged or renamed — try searching.'),
    'no_data': ('尚未匯入資料', 'No data imported yet'),
    'no_data_hint': ('請執行 docker compose run --rm app python scripts/import_taicol.py', 'Run: docker compose run --rm app python scripts/import_taicol.py'),
}

RANKS = {
    'Superkingdom': '總界', 'Kingdom': '界', 'Subkingdom': '亞界', 'Infrakingdom': '下界',
    'Superdivision': '總部', 'Division': '部', 'Subdivision': '亞部', 'Infradivision': '下部',
    'Superphylum': '總門', 'Phylum': '門', 'Subphylum': '亞門', 'Infraphylum': '下門', 'Microphylum': '小門', 'Parvphylum': '小門',
    'Superclass': '總綱', 'Class': '綱', 'Subclass': '亞綱', 'Infraclass': '下綱', 'Parvclass': '小綱',
    'Superorder': '總目', 'Order': '目', 'Suborder': '亞目', 'Infraorder': '下目', 'Parvorder': '小目',
    'Section': '節', 'Subsection': '亞節', 'Superfamily': '總科', 'Epifamily': '領科', 'Family': '科', 'Subfamily': '亞科',
    'Supertribe': '總族', 'Tribe': '族', 'Subtribe': '亞族', 'Genus': '屬', 'Subgenus': '亞屬',
    'Section [botany]': '節', 'Subsection [botany]': '亞節', 'Series': '系', 'Subseries': '亞系',
    'Superspecies': '總種', 'Species': '種', 'Subspecies': '亞種', 'Nothosubspecies': '雜交亞種',
    'Variety': '變種', 'Subvariety': '亞變種', 'Nothovariety': '雜交變種', 'Form': '型', 'Subform': '亞型',
    'Special Form': '特別型', 'Race': '品種', 'Stirps': '種族', 'Morph': '形態型', 'Aberration': '異常個體', 'Hybrid Formula': '雜交組合',
}

REDLIST = {
    'NEX': ('滅絕', 'Extinct'), 'NEW': ('野外滅絕', 'Extinct in the wild'), 'NRE': ('區域滅絕', 'Regionally extinct'),
    'NCR': ('極危', 'Critically endangered'), 'NEN': ('瀕危', 'Endangered'), 'NVU': ('易危', 'Vulnerable'),
    'NNT': ('接近受脅', 'Near threatened'), 'NLC': ('暫無危機', 'Least concern'), 'NDD': ('資料不足', 'Data deficient'),
    'NA': ('不適用', 'Not applicable'), 'NE': ('未評估', 'Not evaluated'),
}
# some TaiCOL rows carry the code without the national "N" prefix
REDLIST.update({k[1:]: v for k, v in list(REDLIST.items()) if k.startswith('N') and len(k) == 3})

IUCN = {
    'EX': ('滅絕', 'Extinct'), 'EW': ('野外滅絕', 'Extinct in the wild'), 'CR': ('極危', 'Critically endangered'),
    'EN': ('瀕危', 'Endangered'), 'VU': ('易危', 'Vulnerable'), 'NT': ('接近受脅', 'Near threatened'),
    'LC': ('暫無危機', 'Least concern'), 'DD': ('資料不足', 'Data deficient'), 'NE': ('未評估', 'Not evaluated'),
    'LR/lc': ('低危／暫無危機', 'Lower risk / least concern'), 'LR/nt': ('低危／接近受脅', 'Lower risk / near threatened'),
    'LR/cd': ('低危／依賴保育', 'Lower risk / conservation dependent'),
}

ALIEN = {
    'native': ('原生', 'Native'), 'naturalized': ('歸化', 'Naturalized'), 'invasive': ('入侵', 'Invasive'),
    'cultured': ('栽培／養殖', 'Cultivated'), 'cultivated': ('栽培', 'Cultivated'), 'casual': ('偶發', 'Casual'),
}

# WCVP life form / climate terms (https://powo.science.kew.org/about-wcvp). Life forms are
# "[modifier ...] head", joined by " or " / ", "; zh puts the modifiers in front of the head too.
LIFEFORM_HEAD = {
    'perennial': '多年生草本', 'annual': '一年生草本', 'biennial': '二年生草本', 'tree': '喬木', 'shrub': '灌木',
    'subshrub': '亞灌木', 'geophyte': '地下芽植物', 'epiphyte': '附生植物', 'climber': '攀緣植物', 'liana': '木質藤本',
    'lithophyte': '石生植物', 'bamboo': '竹類', 'helophyte': '沼生植物', 'chamaephyte': '地表芽植物',
    'holoparasite': '全寄生植物', 'holomycotroph': '完全菌根營養植物', 'succulent': '多肉植物',
    'epiphytic': '附生植物', 'tuberous': '塊莖植物',
}
LIFEFORM_MOD = {
    'rhizomatous': '根莖', 'rhizome': '根莖', 'tuberous': '塊莖', 'bulbous': '鱗莖', 'pseudobulbous': '假球莖',
    'climbing': '攀緣', 'scrambling': '蔓生', 'succulent': '多肉', 'semisucculent': '半多肉', 'epiphytic': '附生',
    'lithophytic': '石生', 'hemiparasitic': '半寄生', 'holoparasitic': '全寄生', 'holomycotrophic': '完全菌根營養',
    'hemimycotrophic': '部分菌根營養', 'hemiepiphytic': '半附生', 'herbaceous': '草質', 'monocarpic': '一次開花',
    'semiaquatic': '半水生', 'caudex': '莖基膨大', 'lignotuber': '木質塊莖',
}
CLIMATE = {
    'temperate': '溫帶', 'wet tropical': '潮濕熱帶', 'subtropical': '亞熱帶', 'seasonally dry tropical': '季節性乾燥熱帶',
    'subalpine': '亞高山', 'subarctic': '亞北極', 'desert': '沙漠', 'dry shrubland': '乾燥灌叢',
    'montane tropical': '熱帶山地', 'tropical': '熱帶',
}


def _lifeform_zh(term):
    words = term.lower().split()
    head, mods = words[-1], words[:-1]
    water = head.startswith('hydro') and head != 'hydro'
    if water:
        head = head[5:]
    if head not in LIFEFORM_HEAD or any(m not in LIFEFORM_MOD for m in mods):
        return None
    return ('水生' if water else '') + ''.join(LIFEFORM_MOD[m] for m in mods) + LIFEFORM_HEAD[head]


def wcvp_terms(text, lang, kind):
    """WCVP life form (kind 'lifeform') or climate in zh; the whole text stays English when any part is unknown."""
    if not text or lang == 'en':
        return text or ''
    parts = re.split(r'\s*(,|\bor\b|\band\b)\s*', text.strip())  # term, separator, term, ...
    out = []
    for i, part in enumerate(parts):
        if i % 2:
            out.append({'or': '或', 'and': '及'}.get(part, '、'))
            continue
        zh = _lifeform_zh(part) if kind == 'lifeform' else CLIMATE.get(part.lower())
        if zh is None:
            return text
        out.append(zh)
    return ''.join(out)


PROTECTED = {
    'I': ('第一級（瀕臨絕種）', 'Class I (endangered)'), 'II': ('第二級（珍貴稀有）', 'Class II (rare and valuable)'),
    'III': ('第三級（其他應予保育）', 'Class III (other conservation-deserving)'),
    '1': ('第一級（瀕臨絕種）', 'Class I (endangered)'), '2': ('第二級（珍貴稀有）', 'Class II (rare and valuable)'),
    '3': ('第三級（其他應予保育）', 'Class III (other conservation-deserving)'),
}

# badge styles (MUSUBii classes) by severity
THREAT_BADGE = {
    'EX': 'is-plain is-danger', 'EW': 'is-plain is-danger', 'CR': 'is-plain is-danger', 'EN': 'is-outline is-danger',
    'VU': 'is-outline is-warning', 'NT': 'is-outline is-info', 'LC': 'is-outline is-success',
}
REDLIST_TO_IUCN = {'NEX': 'EX', 'NEW': 'EW', 'NRE': 'EX', 'NCR': 'CR', 'NEN': 'EN', 'NVU': 'VU', 'NNT': 'NT', 'NLC': 'LC',
                   'EX': 'EX', 'EW': 'EW', 'RE': 'EX', 'CR': 'CR', 'EN': 'EN', 'VU': 'VU', 'NT': 'NT', 'LC': 'LC'}


def make_t(lang):
    i = 0 if lang == 'zh' else 1

    def t(key, **kw):
        pair = STRINGS.get(key)
        s = pair[i] if pair else key
        return s.format(**kw) if kw else s

    def code(table, value):
        if value is None or value == '':
            return ''
        pair = table.get(value)
        return pair[i] if pair else value

    def rank(value):
        if not value:
            return ''
        return RANKS.get(value, value) if lang == 'zh' else value

    return t, code, rank
