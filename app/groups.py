"""Common groups (常用類群): everyday categories mapped onto TaiCOL taxa by taxon_id.

A group is every taxon under any of its roots; 魚類 is not a single clade in TaiCOL,
so it lists several roots.
"""

GROUPS = [
    # key, zh, en, TaiCOL root taxon_ids
    ('birds', '鳥類', 'Birds', ['t0000650']),                       # Aves
    ('amphibians', '兩棲類', 'Amphibians', ['t0000464']),           # Amphibia
    ('reptiles', '爬蟲類', 'Reptiles', ['t0000545']),               # Reptilia
    ('mammals', '哺乳類', 'Mammals', ['t0000517']),                 # Mammalia
    ('arachnids', '蛛形綱', 'Arachnids', ['t0000468']),             # Arachnida
    ('insects', '昆蟲', 'Insects', ['t0000512']),                   # Insecta
    ('plants', '植物', 'Plants', ['t0000003']),                     # Plantae
    ('fishes', '魚類', 'Fishes', ['t0000203', 't0000204', 't0000205', 't0000522', 't0122974']),
    # Actinopterygii, Chondrichthyes, Sarcopterygii, Myxini, Petromyzonti
]
BY_KEY = {k: (zh, en, roots) for k, zh, en, roots in GROUPS}


def label(key, lang):
    zh, en, _ = BY_KEY.get(key, (key, key, []))
    return zh if lang == 'zh' else en
