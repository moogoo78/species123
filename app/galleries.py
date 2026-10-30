"""Field guide galleries (圖鑑): hand-picked taxa shown as photo cards, grouped by family.

Add a gallery by adding a line; the key is its URL, /gallery/<key>.
"""

GALLERIES = [
    # key, zh title, en title, TaiCOL root taxon_ids
    ('amphibians', '臺灣兩棲類圖鑑', 'Amphibians of Taiwan', ['t0000464']),  # Amphibia
    ('reptiles', '臺灣爬蟲類圖鑑', 'Reptiles of Taiwan', ['t0000545']),     # Reptilia (incl. turtles)
    ('sea-turtles', '臺灣海龜圖鑑', 'Sea turtles of Taiwan', ['t0124505']),  # Chelonioidea
    ('odonata', '臺灣蜻蜓豆娘圖鑑', 'Dragonflies and damselflies of Taiwan', ['t0002023']),  # Odonata
    ('mammals', '臺灣哺乳類圖鑑', 'Mammals of Taiwan', ['t0000517']),  # Mammalia
    ('birds', '臺灣鳥類圖鑑', 'Birds of Taiwan', ['t0000650']),  # Aves
    # not one clade in TaiCOL: Actinopterygii, Chondrichthyes, Sarcopterygii, Myxini, Petromyzonti (as groups.py 魚類)
    ('fishes', '臺灣魚類圖鑑', 'Fishes of Taiwan', ['t0000203', 't0000204', 't0000205', 't0000522', 't0122974']),
]
BY_KEY = {k: (zh, en, roots) for k, zh, en, roots in GALLERIES}


def title(key, lang):
    zh, en, _ = BY_KEY[key]
    return zh if lang == 'zh' else en
