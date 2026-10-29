"""Field guide galleries (圖鑑): hand-picked taxa shown as photo cards, grouped by family.

Add a gallery by adding a line; the key is its URL, /gallery/<key>.
"""

GALLERIES = [
    # key, zh title, en title, TaiCOL root taxon_ids
    ('amphibians', '臺灣兩棲類圖鑑', 'Amphibians of Taiwan', ['t0000464']),  # Amphibia
    ('reptiles', '臺灣爬蟲類圖鑑', 'Reptiles of Taiwan', ['t0000545']),     # Reptilia (incl. turtles)
    ('sea-turtles', '臺灣海龜圖鑑', 'Sea turtles of Taiwan', ['t0124505']),  # Chelonioidea
]
BY_KEY = {k: (zh, en, roots) for k, zh, en, roots in GALLERIES}


def title(key, lang):
    zh, en, _ = BY_KEY[key]
    return zh if lang == 'zh' else en
