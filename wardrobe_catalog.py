"""The wardrobe's included cosmetics; stable IDs are stored in save files."""

OUTFITS = {
    "classic": ("보라 멜빵 원피스", (109, 68, 162), (255, 247, 232), "dress"),
    "blueberry": ("블루베리 원피스", (76, 66, 166), (183, 170, 226), "berry"),
    "whale": ("고래 세일러복", (67, 144, 184), (229, 247, 247), "sailor"),
    "strawberry": ("딸기 체크 원피스", (209, 100, 126), (255, 220, 211), "check"),
    "honey": ("꿀벌 앞치마", (223, 168, 65), (255, 245, 207), "apron"),
    "mint": ("민트 반바지 멜빵", (99, 169, 144), (247, 244, 217), "shorts"),
    "lavender": ("라벤더 카디건", (168, 126, 187), (245, 226, 238), "cardigan"),
    "cloud": ("구름 잠옷", (141, 186, 213), (246, 250, 247), "pajamas"),
    "starlight": ("별빛 코트", (59, 68, 113), (234, 202, 118), "coat"),
    "cream": ("크림 블라우스", (239, 225, 198), (149, 105, 85), "blouse"),
    "forest": ("숲속 작업복", (75, 124, 87), (218, 200, 155), "overalls"),
    "rose": ("장미 리본 드레스", (194, 112, 151), (255, 224, 233), "party"),
}
HEADBANDS = {"shark": "상어 머리띠", "none": "머리띠 없음", "blueberry": "블루베리 머리띠",
             "whale": "고래 머리띠", "ribbon": "분홍 리본", "flowers": "들꽃 화관", "star": "별 머리띠"}
SHOES = {"brown": ("갈색 구두", (85, 55, 43)), "white": ("흰 운동화", (242, 238, 220)),
         "blueberry": ("보라 메리제인", (91, 60, 137)), "whale": ("고래 물결 운동화", (70, 156, 183)),
         "boots": ("숲색 장화", (61, 105, 78)), "pink": ("분홍 구두", (217, 138, 163))}
HAIR_COLORS = {"black": ("흑발", (29, 24, 34)), "brown": ("초코 브라운", (85, 53, 42)),
               "chestnut": ("밤색", (138, 74, 47)), "blonde": ("꿀빛 금발", (218, 175, 92)),
               "silver": ("실버", (187, 190, 202)), "lavender": ("라벤더", (156, 116, 181))}
SOCKS = {"none": ("양말 없음", None), "white": ("흰 양말", (255, 245, 223)),
         "blueberry": ("보라 줄무늬", (194, 174, 225)), "whale": ("바다 줄무늬", (182, 229, 234)),
         "navy": ("남색 긴 양말", (66, 73, 113)), "lace": ("레이스 양말", (255, 227, 233))}
CATEGORIES = {"outfit": "의상", "headband": "머리띠", "shoes": "신발", "hair": "머리색", "socks": "양말"}
OPTIONS = {"outfit": OUTFITS, "headband": HEADBANDS, "shoes": SHOES, "hair": HAIR_COLORS, "socks": SOCKS}
DEFAULT_LOOK = {"outfit": "classic", "headband": "shark", "shoes": "brown", "hair": "black", "socks": "none"}
THEME_SETS = {
    "blueberry": {"outfit": "blueberry", "headband": "blueberry", "shoes": "blueberry", "socks": "blueberry"},
    "whale": {"outfit": "whale", "headband": "whale", "shoes": "whale", "socks": "whale"},
}


def normalized_appearance(raw):
    if not isinstance(raw, dict) or not raw:
        return {}
    return {category: raw.get(category) if isinstance(raw.get(category), str) and raw.get(category) in options else DEFAULT_LOOK[category]
            for category, options in OPTIONS.items()}


def option_label(category, key):
    entry = OPTIONS[category][key]
    return entry if isinstance(entry, str) else entry[0]
