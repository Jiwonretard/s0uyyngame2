# 게임 자산

- `blueberry_morning.ogg`: 블루베리 밸리를 위해 새로 작곡하고 합성한 38.4초 반복 배경음악입니다. 참고 영상의 녹음·멜로디·오디오 샘플을 사용하지 않았습니다.
- `smoothie_sale.wav`: 사용자가 제공한 영상에서 추출한 스무디 판매 효과음입니다.

판매 효과음이 재생되는 동안 배경음악은 자동으로 작아지고, 효과음이 끝나면 원래 볼륨으로 부드럽게 돌아옵니다.

- `ingredient_milk_source.png`, `ingredient_blueberry_source.png`,
  `ingredient_ice_source.png`, `ingredient_honey_source.png`: 사용자가 제공한
  우유·블루베리·얼음·꿀 스크린샷입니다. 게임 실행 시 중앙 픽셀 아이콘만
  분리하고 배경을 투명 처리하여 재료 상점, 직접 제조 화면, 믹서 애니메이션에
  사용합니다.

## 물고기 픽셀 디자인

- `fish/carp.png`: 잉어
- `fish/crucian_carp.png`: 붕어
- `fish/bass.png`: 베스
- `fish/turtle.png`: 거북이
- `fish/fish_sheet.png`: 위 네 디자인을 순서대로 모은 확인용 시트

## 가구 픽셀 디자인

- `furniture/bed.png`: 침대
- `furniture/drawer.png`: 서랍
- `furniture/desk.png`: 책상
- `furniture/lantern.png`: 랜턴
- `furniture/flowerpot.png`: 화분
- `furniture/furniture_sheet.png`: 위 다섯 디자인을 순서대로 모은 확인용 시트

모든 물고기와 가구는 투명 배경 PNG이며 게임 안에서 실제로 불러와 사용합니다.
`generate_pixel_assets.py`를 실행하면 같은 원본 픽셀 디자인으로 개별 파일과 시트를
다시 만들 수 있습니다. 외부 게임의 그래픽은 포함하지 않았습니다.
