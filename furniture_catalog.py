"""Shared furniture catalogue for purchases, room placement and pixel assets."""

# Stable keys keep existing furniture and saved room layouts compatible.
# New designs are cosmetic: price reflects size/detail, not production bonuses.
FURNITURE_CATALOG = {
    "bed": ("침대", 3000, "bed", (5, 3)),
    "drawer": ("서랍", 500, "drawer", (2, 2)),
    "desk": ("책상", 1000, "desk", (4, 2)),
    "lantern": ("랜턴", 300, "lantern", (2, 2)),
    "flowerpot": ("화분", 100, "flowerpot", (2, 2)),
    "bed_gingham": ("딸기 체크 침대", 3600, "bed", (5, 3)),
    "bed_quilt": ("들꽃 퀼트 침대", 4200, "bed", (5, 3)),
    "bed_cloud": ("구름 침대", 4800, "bed", (5, 3)),
    "bed_canopy": ("별빛 캐노피 침대", 6000, "bed", (5, 4)),
    "drawer_white": ("크림 서랍장", 650, "drawer", (2, 2)),
    "drawer_wicker": ("라탄 서랍장", 850, "drawer", (3, 2)),
    "drawer_apothecary": ("씨앗 약장", 1100, "drawer", (3, 3)),
    "drawer_moon": ("달빛 서랍장", 1400, "drawer", (2, 3)),
    "desk_writing": ("편지 책상", 1200, "desk", (4, 2)),
    "desk_round": ("둥근 독서 책상", 1500, "desk", (3, 3)),
    "desk_studio": ("화가의 책상", 1800, "desk", (4, 3)),
    "desk_botanist": ("식물학자 책상", 2200, "desk", (4, 3)),
    "lantern_camping": ("숲속 캠핑 랜턴", 400, "lantern", (2, 2)),
    "lantern_paper": ("한지 랜턴", 550, "lantern", (2, 2)),
    "lantern_star": ("별 유리 랜턴", 750, "lantern", (2, 2)),
    "lantern_mushroom": ("버섯 랜턴", 900, "lantern", (2, 2)),
    "plant_monstera": ("몬스테라 화분", 250, "flowerpot", (3, 3)),
    "plant_snake": ("산세베리아 화분", 180, "flowerpot", (2, 3)),
    "plant_echeveria": ("에케베리아 화분", 150, "flowerpot", (2, 2)),
    "plant_lavender": ("라벤더 화분", 300, "flowerpot", (2, 3)),
    "wardrobe": ("블루벨리 옷장", 1500, "wardrobe", (3, 4)),
}

FURNITURE_CATEGORY_LABELS = {
    "bed": "침대", "drawer": "서랍", "desk": "책상",
    "lantern": "랜턴", "flowerpot": "화분", "wardrobe": "옷장",
}
FURNITURE_CATEGORIES = {
    category: tuple(key for key, item in FURNITURE_CATALOG.items() if item[2] == category)
    for category in FURNITURE_CATEGORY_LABELS
}
FURNITURE_COSTS = {key: item[1] for key, item in FURNITURE_CATALOG.items()}
FURNITURE_LABELS = {key: item[0] for key, item in FURNITURE_CATALOG.items()}
FURNITURE_FOOTPRINTS = {key: item[3] for key, item in FURNITURE_CATALOG.items()}
