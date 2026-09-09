# 블루벨리 가구 디자인 · 26종

집에서 구입·배치하는 실제 투명 배경 픽셀 PNG입니다. 기존 5종에 종류별 4종씩 추가했습니다.
`furniture_sheet.png`는 종류별 한 줄, 각 5종으로 이름과 가격까지 확인하는 전체 목록입니다.

| 종류 | 파일 | 디자인 | 가격(코인) |
|---|---|---|---:|
| 침대 | bed.png | 기본 침대 | 3,000 |
| 침대 | bed_gingham.png | 딸기 체크 침대 | 3,600 |
| 침대 | bed_quilt.png | 들꽃 퀼트 침대 | 4,200 |
| 침대 | bed_cloud.png | 구름 침대 | 4,800 |
| 침대 | bed_canopy.png | 별빛 캐노피 침대 | 6,000 |
| 서랍 | drawer.png | 기본 서랍 | 500 |
| 서랍 | drawer_white.png | 크림 서랍장 | 650 |
| 서랍 | drawer_wicker.png | 라탄 서랍장 | 850 |
| 서랍 | drawer_apothecary.png | 씨앗 약장 | 1,100 |
| 서랍 | drawer_moon.png | 달빛 서랍장 | 1,400 |
| 책상 | desk.png | 기본 책상 | 1,000 |
| 책상 | desk_writing.png | 편지 책상 | 1,200 |
| 책상 | desk_round.png | 둥근 독서 책상 | 1,500 |
| 책상 | desk_studio.png | 화가의 책상 | 1,800 |
| 책상 | desk_botanist.png | 식물학자 책상 | 2,200 |
| 랜턴 | lantern.png | 기본 랜턴 | 300 |
| 랜턴 | lantern_camping.png | 숲속 캠핑 랜턴 | 400 |
| 랜턴 | lantern_paper.png | 한지 랜턴 | 550 |
| 랜턴 | lantern_star.png | 별 유리 랜턴 | 750 |
| 랜턴 | lantern_mushroom.png | 버섯 랜턴 | 900 |
| 화분 | flowerpot.png | 기본 화분 | 100 |
| 화분 | plant_monstera.png | 몬스테라 화분 | 250 |
| 화분 | plant_snake.png | 산세베리아 화분 | 180 |
| 화분 | plant_echeveria.png | 에케베리아 화분 | 150 |
| 화분 | plant_lavender.png | 라벤더 화분 | 300 |

## 식물 모티프

식물의 형태를 참고하여 픽셀로 직접 그렸으며 참고 사이트의 사진은 포함하지 않습니다.

- 몬스테라: 갈라진 넓은 잎과 굵은 잎맥. [RHS 형태 참고](https://www.rhs.org.uk/plants/types/houseplants/monsteras-and-more)
- 산세베리아: 곧게 자라는 칼 모양 잎, 노란 잎 가장자리와 가로무늬.
- 에케베리아: 겹겹의 로제트와 두꺼운 청록색 잎, 분홍 잎끝. [RHS 형태 참고](https://www.rhs.org.uk/plants/echeveria)
- 라벤더: 가는 회녹색 잎과 줄기 위의 보라색 꽃이삭. [RHS 형태 참고](https://www.rhs.org.uk/plants/lavender/growing-guide)

## 가격과 조작

기존 가격은 유지했습니다. 새 화분은 기본 스무디 몇 잔으로 살 수 있는 150~300코인,
랜턴은 400~900코인, 서랍은 650~1,400코인, 책상은 1,200~2,200코인입니다.
침대는 기존 3,000코인을 기준으로 3,600~6,000코인으로 올라가며 첫 텃밭(10,000)보다 저렴합니다.
옷장(`wardrobe.png`, 1,500코인)이 추가되어 총 26종입니다. 옷장은 집에 배치하면 의상·액세서리를 바꾸는 기능이 열립니다. 서랍 5종은 각각 5×5 보관함이며 집에서 V 또는 배치된 서랍 클릭으로 가방 물건을 넣고 꺼냅니다. 한 칸 최대 16개이며 낚싯대의 내구도와 보관한 물건도 저장됩니다. 나머지는 장식 가구이며 생산이나 수입 보너스는 없습니다. 디자인별 한 개씩 소유하며 가방 칸을 사용하지 않습니다.

집 위쪽 카테고리 탭 또는 PgUp/PgDn으로 종류를 바꿉니다. 숫자 1~5는 현재 보이는 상품에 대응합니다.
G 꾸미기, 바닥 클릭 배치, 방향키 이동, R 회전, X 보관이 모든 디자인에 적용됩니다.

가구 정보는 프로젝트의 `furniture_catalog.py`에서 공유합니다.
`python3 assets/generate_furniture_variants.py`로 가구만 재생성할 수 있습니다.
새 디자인은 48×40 원본을 정수 배율로 확대하며 기존 5종은 종전 디자인을 유지합니다.
