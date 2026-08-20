import base64
import json
import random
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="지하철 2호선 게임",
    page_icon="🚃",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_DIR = Path(__file__).parent

STATIONS = [
    "성수", "뚝섬", "한양대", "왕십리", "상왕십리", "신당", "동대문역사문화공원",
    "을지로4가", "을지로3가", "을지로입구", "시청", "충정로", "아현", "이대",
    "신촌", "홍대입구", "합정", "당산", "영등포구청", "문래", "신도림", "대림",
    "구로디지털단지", "신대방", "신림", "봉천", "서울대입구", "낙성대", "사당",
    "방배", "서초", "교대", "강남", "역삼", "선릉", "삼성", "종합운동장",
    "신천", "잠실", "잠실나루", "강변", "구의", "건대입구"
]
GOAL_STATION = "건대입구"
GOAL_INDEX   = len(STATIONS) - 1
BINBOU_RESET_DISTANCE = 6

ORIGINAL_WIDTH  = 1874
ORIGINAL_HEIGHT = 1510

STATION_PIXELS = {
    # 첨부된 1874×1510 노선도 이미지 기준 좌표
    # 성수 → 뚝섬 → ... → 건대입구 순서로 실제 2호선 진행 경로를 따라갑니다.
    "성수":          (1559,  522),
    "뚝섬":          (1523,  409),
    "한양대":        (1456,  358),
    "왕십리":        (1372,  342),
    "상왕십리":      (1265,  342),
    "신당":          (1163,  342),
    "동대문역사문화공원": (1063, 342),
    "을지로4가":     (946,   342),
    "을지로3가":     (842,   342),
    "을지로입구":    (740,   343),
    "시청":          (645,   343),
    "충정로":        (544,   343),
    "아현":          (454,   362),
    "이대":          (426,   394),
    "신촌":          (366,   475),
    "홍대입구":      (361,   561),
    "합정":          (361,   642),
    "당산":          (361,   731),
    "영등포구청":    (361,   815),
    "문래":          (362,   895),
    "신도림":        (361,   975),
    "대림":          (361,  1073),
    "구로디지털단지": (381, 1160),
    "신대방":        (438,  1223),
    "신림":          (521,  1253),
    "봉천":          (611,  1253),
    "서울대입구":    (698,  1253),
    "낙성대":        (788,  1253),
    "사당":          (881,  1253),
    "방배":          (970,  1253),
    "서초":          (1060, 1253),
    "교대":          (1153, 1253),
    "강남":          (1240, 1253),
    "역삼":          (1333, 1253),
    "선릉":          (1423, 1253),
    "삼성":          (1507, 1204),
    "종합운동장":    (1551, 1137),
    "신천":          (1559, 1051),
    "잠실":          (1559,  961),
    "잠실나루":      (1559,  874),
    "강변":          (1559,  787),
    "구의":          (1560,  698),
    "건대입구":      (1559,  610),
}

STATION_POINTS = {
    name: {"x": x / ORIGINAL_WIDTH * 100, "y": y / ORIGINAL_HEIGHT * 100}
    for name, (x, y) in STATION_PIXELS.items()
}

TRAIN_TYPES = {
    "KTX":  {"name": "KTX",   "emoji": "🚄", "color": "#2f80ed", "glow": "rgba(47,128,237,.85)"},
    "SRT":  {"name": "SRT",   "emoji": "🚅", "color": "#8e44ad", "glow": "rgba(142,68,173,.85)"},
    "신칸센": {"name": "신칸센", "emoji": "🚆", "color": "#e74c3c", "glow": "rgba(231,76,60,.85)"},
}

SQUARE_TYPES = {
    "홍대입구": "blue",  "강남": "blue",  "왕십리": "blue",
    "선릉":     "blue",  "시청": "blue",  "이대":   "blue",
    "신도림":   "red",   "사당": "red",   "동대문역사문화공원": "red",
    "구로디지털단지": "red",
    "을지로3가": "star", "잠실": "star",  "교대":   "star",
    "합정":     "star",  "성수": "star",
    "신림":     "trap",  "구의": "trap",
    # 어린이가 한 바퀴를 도는 동안 여러 번 만날 수 있도록 일반 역 5곳을 보물상자로 지정합니다.
    "아현": "treasure", "문래": "treasure", "봉천": "treasure",
    "역삼": "treasure", "잠실나루": "treasure",
}

BLUE_EVENTS = [
    {"msg": "🎵 이벤트 발생! 다음 주사위 +2 보너스 획득!", "bonus_dice": 2},
    {"msg": "💰 행운! 점수 +20점!", "score": 20},
    {"msg": "🎁 아이템 카드 획득! 다음 이동 2배 카드!", "item": "double_move"},
    {"msg": "⚡ 급행열차! 주사위를 한 번 더 굴립니다!", "extra_roll": True},
    {"msg": "🌟 럭키! 먹보유령이 3칸 뒤로 물러납니다!", "push_binbou": 3},
    {"msg": "🎶 축제! 점수 +15점 + 추가 주사위!", "score": 15, "extra_roll": True},
]

RED_EVENTS = [
    {"msg": "💸 사건 발생! 점수 -10점!", "score": -10},
    {"msg": "🚧 공사 중! 2칸 후퇴!", "move": -2},
    {"msg": "😈 먹보유령 접근! 먹보유령이 5칸 앞으로 이동!", "push_binbou": -5},
    {"msg": "⛔ 운행 중단! 이번 턴 퀴즈 2문제!", "double_quiz": True},
    {"msg": "🌧️ 폭우! 1칸 뒤로 이동!", "move": -1},
]

TREASURE_EVENTS = [
    {"msg": "💰 황금 동전 발견! 점수 +30점!", "score": 30},
    {"msg": "🃏 반짝이는 아이템 카드 발견!", "random_item": True},
    {"msg": "🧿 유령 밀어내기 부적! 먹보유령이 5칸 뒤로!", "push_binbou": 5},
    {"msg": "⚡ 터보 티켓 발견! 다음 주사위 +3!", "bonus_dice": 3},
    {"msg": "🌈 대박 보물! 점수 +20점 + 아이템 카드!", "score": 20, "random_item": True},
]

TRAP_EVENTS = [
    {"msg": "👿 먹보유령 함정! 탈출 미니게임에 도전하세요!", "binbou_attach": True, "ghost_penalty": 20},
]

ITEMS = {
    "double_move":  {"name": "🚄 2배 이동 카드", "desc": "이번 주사위 결과를 2배로!"},
    "shield":       {"name": "🛡️ 방어 카드",    "desc": "빨간 칸 이벤트를 1회 무효화"},
    "skip_penalty": {"name": "✨ 면제 카드",     "desc": "뒤로 가기 주사위 면제"},
    "score_up":     {"name": "💎 점수 2배 카드", "desc": "다음 정답 점수 2배"},
}

DEST_CANDIDATES = ["강남", "홍대입구", "왕십리", "선릉", "시청", "을지로입구", "합정", "교대"]
QUIZ_CATEGORIES = ["국어", "상식", "과학", "영어", "수수께끼"]

QUIZZES = [
    # ══════════════ 국어 (20문제 · 8세 수준) ══════════════
    {'category': '국어', 'question': "'조용하다'와 반대되는 뜻의 말은 무엇일까요?",
     'options': ['시끄럽다', '깨끗하다', '따뜻하다', '가볍다'], 'answer': 0},
    {'category': '국어', 'question': "'튼튼하다'와 뜻이 가장 비슷한 말은 무엇일까요?",
     'options': ['건강하다', '느리다', '약하다', '작다'], 'answer': 0},
    {'category': '국어', 'question': "'민수가 운동장에서 공을 찼습니다.'에서 공을 찬 사람은 누구일까요?",
     'options': ['운동장', '공', '민수', '선생님'], 'answer': 2},
    {'category': '국어', 'question': "'비가 많이 와서 우산을 썼습니다.'에서 우산을 쓴 까닭은 무엇일까요?",
     'options': ['날씨가 더워서', '바람이 없어서', '해가 떠서', '비가 많이 와서'], 'answer': 3},
    {'category': '국어', 'question': '다음 낱말을 가나다순으로 놓았을 때 가장 먼저 오는 것은 무엇일까요?',
     'options': ['나무', '다람쥐', '바다', '강아지'], 'answer': 3},
    {'category': '국어', 'question': "'새빨간 사과가 탁자 위에 있습니다.'에서 사과의 색을 나타내는 말은 무엇일까요?",
     'options': ['있습니다', '사과', '새빨간', '탁자'], 'answer': 2},
    {'category': '국어', 'question': "'시냇물이 졸졸 흐릅니다.'에서 물 흐르는 소리를 흉내 낸 말은 무엇일까요?",
     'options': ['시냇물', '졸졸', '흐릅니다', '맑은'], 'answer': 1},
    {'category': '국어', 'question': "'별이 반짝반짝 빛납니다.'에서 빛나는 모습을 나타내는 말은 무엇일까요?",
     'options': ['별이', '빛납니다', '하늘', '반짝반짝'], 'answer': 3},
    {'category': '국어', 'question': '다음 중 물어보는 문장의 끝에 알맞은 문장 부호는 무엇일까요?',
     'options': ['마침표(.)', '물음표(?)', '느낌표(!)', '쉼표(,)'], 'answer': 1},
    {'category': '국어', 'question': '다음 중 띄어쓰기가 바르게 된 문장은 무엇일까요?',
     'options': ['나는 학교에 갑니다.', '나는학교에 갑니다.', '나는 학교에갑니다.', '나는학교에갑니다.'], 'answer': 0},
    {'category': '국어', 'question': "'거친'과 반대되는 뜻의 말은 무엇일까요?",
     'options': ['높은', '부드러운', '무거운', '빠른'], 'answer': 1},
    {'category': '국어', 'question': "'고양이가 사뿐사뿐 걸어왔습니다.'에서 고양이가 걸어온 모습으로 알맞은 것은 무엇일까요?",
     'options': ['아주 시끄럽게', '세게 뛰면서', '가볍고 조심스럽게', '매우 빠르게'], 'answer': 2},
    {'category': '국어', 'question': '책을 읽은 뒤 내용과 생각, 느낌을 적은 글을 무엇이라고 할까요?',
     'options': ['독후감', '광고', '일기', '편지'], 'answer': 0},
    {'category': '국어', 'question': '다음 중 일이 일어난 순서가 가장 자연스러운 것은 무엇일까요?',
     'options': ['세수함 → 학교에 감 → 잠에서 깸', '학교에 감 → 세수함 → 잠에서 깸', '잠에서 깸 → 세수함 → 학교에 감', '학교에 감 → 잠에서 깸 → 세수함'], 'answer': 2},
    {'category': '국어', 'question': "'강아지가 꼬리를 흔들며 반갑게 달려왔습니다.'에서 강아지의 기분으로 가장 알맞은 것은 무엇일까요?",
     'options': ['졸리다', '반갑다', '화나다', '무섭다'], 'answer': 1},
    {'category': '국어', 'question': "'형제'라는 말과 가장 관계가 깊은 것은 무엇일까요?",
     'options': ['형과 동생', '사과와 배', '친구와 이웃', '선생님과 학생'], 'answer': 0},
    {'category': '국어', 'question': '다음 중 움직임을 나타내는 말은 무엇일까요?',
     'options': ['교실', '달리다', '파랗다', '연필'], 'answer': 1},
    {'category': '국어', 'question': "'아기가 새근새근 잡니다.'에서 '새근새근'이 나타내는 모습은 무엇일까요?",
     'options': ['큰 소리로 우는 모습', '크게 웃는 모습', '빨리 달리는 모습', '편안하게 자는 모습'], 'answer': 3},
    {'category': '국어', 'question': '다음 중 높임말을 사용한 문장은 무엇일까요?',
     'options': ['할머니가 밥을 먹어.', '할머니, 빨리 먹어.', '할머니께서 진지를 드세요.', '할머니가 밥 먹자.'], 'answer': 2},
    {'category': '국어', 'question': "'운동장에는 친구들이 많았습니다. 그래서 우리는 교실에서 놀았습니다.'에서 '그래서'는 앞뒤 내용을 어떻게 이어 줄까요?",
     'options': ['시간이 아주 오래 지났음을 나타낸다', '사람의 이름을 나타낸다', '서로 반대되는 내용을 나타낸다', '앞의 일 때문에 뒤의 일이 생겼음을 나타낸다'], 'answer': 3},

    # ══════════════ 상식 (20문제 · 8세 수준) ══════════════
    {'category': '상식', 'question': '한글을 만들도록 한 조선의 왕은 누구일까요?',
     'options': ['김구', '정약용', '이순신', '세종대왕'], 'answer': 3},
    {'category': '상식', 'question': '대한민국에서 가장 큰 섬은 어디일까요?',
     'options': ['강화도', '제주도', '울릉도', '거제도'], 'answer': 1},
    {'category': '상식', 'question': '대한민국을 상징하는 꽃은 무엇일까요?',
     'options': ['장미', '튤립', '무궁화', '해바라기'], 'answer': 2},
    {'category': '상식', 'question': '우리나라에서 돈을 셀 때 쓰는 기본 단위는 무엇일까요?',
     'options': ['달러', '유로', '엔', '원'], 'answer': 3},
    {'category': '상식', 'question': '학교 근처에서 자동차가 특히 천천히 다녀야 하는 곳을 무엇이라고 할까요?',
     'options': ['고속도로', '어린이 보호구역', '터널', '주차장'], 'answer': 1},
    {'category': '상식', 'question': '횡단보도 신호가 빨간불일 때 해야 할 행동은 무엇일까요?',
     'options': ['뛰어서 건넌다', '멈추어 기다린다', '도로 한가운데에서 기다린다', '차가 없으면 바로 건넌다'], 'answer': 1},
    {'category': '상식', 'question': '위험한 일을 당했을 때 경찰에 도움을 요청하는 전화번호는 무엇일까요?',
     'options': ['110', '119', '112', '120'], 'answer': 2},
    {'category': '상식', 'question': '지진이 나서 실내가 흔들릴 때 먼저 하기 좋은 행동은 무엇일까요?',
     'options': ['튼튼한 탁자 아래에서 머리를 보호한다', '엘리베이터를 타고 내려간다', '창문 가까이 선다', '밖으로 무조건 뛰어간다'], 'answer': 0},
    {'category': '상식', 'question': '설날에 어른께 새해 인사를 드리는 것을 무엇이라고 할까요?',
     'options': ['응원', '산책', '절약', '세배'], 'answer': 3},
    {'category': '상식', 'question': '추석에 자주 만들어 먹는 전통 음식은 무엇일까요?',
     'options': ['송편', '피자', '햄버거', '스파게티'], 'answer': 0},
    {'category': '상식', 'question': '지도에서 파란색으로 표시하는 경우가 가장 많은 것은 무엇일까요?',
     'options': ['철길과 다리', '산과 들', '바다와 강', '도로와 건물'], 'answer': 2},
    {'category': '상식', 'question': '나침반에서 N은 어느 방향을 뜻할까요?',
     'options': ['남쪽', '동쪽', '북쪽', '서쪽'], 'answer': 2},
    {'category': '상식', 'question': '편지나 소포를 보내고 받을 수 있는 곳은 어디일까요?',
     'options': ['미술관', '우체국', '도서관', '체육관'], 'answer': 1},
    {'category': '상식', 'question': '박물관에서 전시품을 볼 때 알맞은 행동은 무엇일까요?',
     'options': ['정해진 규칙을 지키며 관람한다', '큰 소리로 장난친다', '전시실에서 뛰어다닌다', '전시품을 마음대로 만진다'], 'answer': 0},
    {'category': '상식', 'question': '빌린 도서관 책은 어떻게 해야 할까요?',
     'options': ['친구에게 그냥 준다', '책에 낙서를 해서 돌려준다', '정해진 날짜 안에 돌려준다', '집에 계속 보관한다'], 'answer': 2},
    {'category': '상식', 'question': '서울을 가로질러 흐르는 큰 강의 이름은 무엇일까요?',
     'options': ['한강', '낙동강', '금강', '섬진강'], 'answer': 0},
    {'category': '상식', 'question': '올림픽을 상징하는 오륜기는 고리가 몇 개일까요?',
     'options': ['4개', '3개', '6개', '5개'], 'answer': 3},
    {'category': '상식', 'question': '다 쓴 건전지는 보통 어떻게 버리는 것이 알맞을까요?',
     'options': ['길에 버린다', '물에 흘려보낸다', '일반 종이 상자에 넣는다', '폐건전지 수거함에 넣는다'], 'answer': 3},
    {'category': '상식', 'question': '식당이나 공공장소에서 줄을 서 있을 때 알맞은 행동은 무엇일까요?',
     'options': ['차례를 기다린다', '줄을 마음대로 바꾼다', '앞사람을 밀고 들어간다', '큰 소리로 새치기한다'], 'answer': 0},
    {'category': '상식', 'question': '우리나라 전통 집을 부르는 말은 무엇일까요?',
     'options': ['이글루', '한옥', '성곽', '티피'], 'answer': 1},

    # ══════════════ 과학 (20문제 · 8세 수준) ══════════════
    {'category': '과학', 'question': '젖은 빨래가 햇볕에 마르는 것은 물이 주로 무엇으로 변하기 때문일까요?',
     'options': ['모래', '수증기', '얼음', '소금'], 'answer': 1},
    {'category': '과학', 'question': '차가운 컵 겉면에 물방울이 맺히는 까닭으로 가장 알맞은 것은 무엇일까요?',
     'options': ['공기 중 수증기가 물방울로 변해서', '컵 안의 물이 컵을 뚫고 나와서', '빛이 물로 변해서', '유리가 녹아서'], 'answer': 0},
    {'category': '과학', 'question': '손전등을 물체의 왼쪽에서 비추면 그림자는 주로 어느 쪽에 생길까요?',
     'options': ['물체 안쪽', '물체의 오른쪽', '물체의 위쪽만', '물체의 왼쪽'], 'answer': 1},
    {'category': '과학', 'question': '소리가 나는 물체에서 공통으로 관찰할 수 있는 현상은 무엇일까요?',
     'options': ['떨림', '얼어붙음', '사라짐', '빛남'], 'answer': 0},
    {'category': '과학', 'question': '자석에는 서로 다른 두 극이 있습니다. 무엇과 무엇일까요?',
     'options': ['N극과 S극', '밝은극과 어두운극', '위극과 아래극', '동극과 서극'], 'answer': 0},
    {'category': '과학', 'question': '다음 중 전기가 비교적 잘 통하는 물질은 무엇일까요?',
     'options': ['나무', '구리', '플라스틱', '고무'], 'answer': 1},
    {'category': '과학', 'question': '해는 어느 쪽 하늘에서 떠오를까요?',
     'options': ['북쪽', '남쪽', '서쪽', '동쪽'], 'answer': 3},
    {'category': '과학', 'question': '달이 밤하늘에서 밝게 보이는 가장 큰 까닭은 무엇일까요?',
     'options': ['지구의 불빛을 만들기 때문에', '별빛을 모두 모으기 때문에', '달이 불타고 있기 때문에', '태양빛을 반사하기 때문에'], 'answer': 3},
    {'category': '과학', 'question': '곤충의 다리는 몇 개일까요?',
     'options': ['4개', '6개', '10개', '8개'], 'answer': 1},
    {'category': '과학', 'question': '거미의 다리는 몇 개일까요?',
     'options': ['8개', '12개', '6개', '4개'], 'answer': 0},
    {'category': '과학', 'question': '민들레 씨앗이 멀리 퍼지는 데 가장 큰 도움을 주는 것은 무엇일까요?',
     'options': ['그림자', '돌멩이', '자석', '바람'], 'answer': 3},
    {'category': '과학', 'question': '식물의 뿌리가 하는 일로 가장 알맞은 것은 무엇일까요?',
     'options': ['소리를 만든다', '꽃잎을 날린다', '빛을 낸다', '흙에서 물을 흡수한다'], 'answer': 3},
    {'category': '과학', 'question': '새의 몸을 덮고 있는 것은 무엇일까요?',
     'options': ['털실', '나무껍질', '깃털', '비늘만'], 'answer': 2},
    {'category': '과학', 'question': '고래가 숨을 쉬기 위해 물 위로 올라오는 까닭은 무엇일까요?',
     'options': ['햇빛을 먹어야 하기 때문에', '아가미로만 숨 쉬기 때문에', '폐로 공기를 마셔야 하기 때문에', '물을 마셔야 하기 때문에'], 'answer': 2},
    {'category': '과학', 'question': '포유류의 새끼가 어릴 때 주로 먹는 것은 무엇일까요?',
     'options': ['모래', '돌가루', '나뭇잎만', '어미의 젖'], 'answer': 3},
    {'category': '과학', 'question': '냄새를 맡는 데 가장 중요한 감각 기관은 무엇일까요?',
     'options': ['손', '발', '코', '귀'], 'answer': 2},
    {'category': '과학', 'question': '우리 몸의 뼈가 하는 일로 알맞은 것은 무엇일까요?',
     'options': ['몸을 지탱하고 중요한 기관을 보호한다', '음식을 소화한다', '소리를 직접 만든다', '피를 몸 밖으로 보낸다'], 'answer': 0},
    {'category': '과학', 'question': '기온을 재는 데 사용하는 도구는 무엇일까요?',
     'options': ['자', '온도계', '나침반', '저울'], 'answer': 1},
    {'category': '과학', 'question': '구름 속 작은 물방울이 커지고 무거워져 땅으로 떨어지는 현상은 무엇일까요?',
     'options': ['바람', '서리', '비', '안개'], 'answer': 2},
    {'category': '과학', 'question': '다음 중 빛을 가장 잘 통과시키는 물질은 무엇일까요?',
     'options': ['벽돌', '철판', '맑은 유리', '두꺼운 나무판'], 'answer': 2},

    # ══════════════ 영어 (20문제 · 8세 수준) ══════════════
    {'category': '영어', 'question': "'I am eight years old.'의 뜻으로 알맞은 것은 무엇일까요?",
     'options': ['나는 여덟 권을 읽습니다.', '나는 여덟 살입니다.', '나는 여덟 명을 만납니다.', '나는 여덟 시에 잡니다.'], 'answer': 1},
    {'category': '영어', 'question': "'What is your name?'에 가장 알맞은 대답은 무엇일까요?",
     'options': ['Good night.', 'I am hungry.', 'It is a pencil.', 'My name is Mina.'], 'answer': 3},
    {'category': '영어', 'question': "'Open the door.'의 뜻은 무엇일까요?",
     'options': ['문을 여세요.', '의자에 앉으세요.', '문을 닫으세요.', '창문을 닦으세요.'], 'answer': 0},
    {'category': '영어', 'question': "'Please be quiet.'의 뜻으로 알맞은 것은 무엇일까요?",
     'options': ['노래를 불러 주세요.', '조용히 해 주세요.', '문을 열어 주세요.', '빨리 달려 주세요.'], 'answer': 1},
    {'category': '영어', 'question': "'I have two pencils.'의 뜻은 무엇일까요?",
     'options': ['나는 연필을 사지 않습니다.', '나는 연필을 두 번 깎습니다.', '나는 연필 두 자루가 있습니다.', '나는 연필을 잃어버렸습니다.'], 'answer': 2},
    {'category': '영어', 'question': "'She is my sister.'의 뜻은 무엇일까요?",
     'options': ['그녀는 나의 여자 형제입니다.', '그녀는 나의 선생님입니다.', '그녀는 나의 이웃집입니다.', '그녀는 나의 의사입니다.'], 'answer': 0},
    {'category': '영어', 'question': "'The cat is under the table.'에서 고양이는 어디에 있을까요?",
     'options': ['문 밖', '탁자 옆의 의자 위', '탁자 아래', '탁자 위'], 'answer': 2},
    {'category': '영어', 'question': "'Monday'는 무슨 요일일까요?",
     'options': ['토요일', '화요일', '월요일', '일요일'], 'answer': 2},
    {'category': '영어', 'question': "'Sunday'는 무슨 요일일까요?",
     'options': ['토요일', '일요일', '금요일', '수요일'], 'answer': 1},
    {'category': '영어', 'question': "'breakfast'의 뜻은 무엇일까요?",
     'options': ['간식 시간', '아침 식사', '점심 식사', '저녁 식사'], 'answer': 1},
    {'category': '영어', 'question': "'hungry'의 뜻으로 알맞은 것은 무엇일까요?",
     'options': ['목마른', '신나는', '피곤한', '배고픈'], 'answer': 3},
    {'category': '영어', 'question': "'beautiful'의 뜻으로 가장 알맞은 것은 무엇일까요?",
     'options': ['시끄러운', '좁은', '차가운', '아름다운'], 'answer': 3},
    {'category': '영어', 'question': "'teacher'는 누구일까요?",
     'options': ['학생', '요리사', '선생님', '경찰관'], 'answer': 2},
    {'category': '영어', 'question': "'library'는 어떤 장소일까요?",
     'options': ['병원', '도서관', '공항', '시장'], 'answer': 1},
    {'category': '영어', 'question': "'How are you?'에 자연스럽게 대답한 것은 무엇일까요?",
     'options': ['My book is blue.', 'Open the window.', 'It is Monday.', "I'm fine, thank you."], 'answer': 3},
    {'category': '영어', 'question': "'Can I have some water?'의 뜻으로 가장 알맞은 것은 무엇일까요?",
     'options': ['창문을 열어도 되나요?', '수영해도 되나요?', '물 좀 주실 수 있나요?', '물을 버려도 되나요?'], 'answer': 2},
    {'category': '영어', 'question': "'children'은 어떤 뜻일까요?",
     'options': ['아이들', '부모님', '선생님들', '동물들'], 'answer': 0},
    {'category': '영어', 'question': "'up'과 반대되는 뜻의 영어 단어는 무엇일까요?",
     'options': ['down', 'left', 'open', 'near'], 'answer': 0},
    {'category': '영어', 'question': "'There are three birds in the tree.'의 뜻으로 알맞은 것은 무엇일까요?",
     'options': ['나무에 새 세 마리가 있습니다.', '새가 나무 아래에서 잡니다.', '나무가 세 그루 있습니다.', '나무에 사과 세 개가 있습니다.'], 'answer': 0},
    {'category': '영어', 'question': "'Let's play together.'의 뜻은 무엇일까요?",
     'options': ['조용히 자자.', '혼자 공부하자.', '이제 집에 가자.', '같이 놀자.'], 'answer': 3},

    # ══════════════ 수수께끼 (20문제 · 8세 수준) ══════════════
    {'category': '수수께끼', 'question': "누르면 '딩동' 소리가 나서 집 안 사람에게 손님이 왔음을 알려 주는 것은 무엇일까요?",
     'options': ['우산', '손전등', '초인종', '연필깎이'], 'answer': 2},
    {'category': '수수께끼', 'question': '먹을 수는 없지만 누구나 해마다 한 살씩 더 먹는 것은 무엇일까요?',
     'options': ['밥', '나이', '사탕', '약'], 'answer': 1},
    {'category': '수수께끼', 'question': '하늘에 떠다니며 모양이 계속 바뀌고, 때로는 비나 눈을 내리는 것은 무엇일까요?',
     'options': ['구름', '비행기', '풍선', '연'], 'answer': 0},
    {'category': '수수께끼', 'question': '밤하늘에서 볼 수 있고, 날마다 보이는 모양이 조금씩 달라지는 것은 무엇일까요?',
     'options': ['무지개', '신호등', '가로등', '달'], 'answer': 3},
    {'category': '수수께끼', 'question': '추운 날 밖에서 숨을 내쉴 때 하얗게 보이는 것은 무엇일까요?',
     'options': ['입김', '구름 조각', '연기통', '눈사람'], 'answer': 0},
    {'category': '수수께끼', 'question': '한쪽 끝은 뾰족하고, 종이에 글씨나 그림을 그릴 수 있는 것은 무엇일까요?',
     'options': ['젓가락', '연필', '칫솔', '숟가락'], 'answer': 1},
    {'category': '수수께끼', 'question': '내가 움직이면 똑같이 움직이지만, 거울 밖으로 나오지는 못하는 것은 무엇일까요?',
     'options': ['텔레비전 리모컨', '거울 속 내 모습', '사진 속 산', '책 속 글자'], 'answer': 1},
    {'category': '수수께끼', 'question': '문을 열고 밖으로 나가지 않아도 바깥을 볼 수 있게 해 주는 것은 무엇일까요?',
     'options': ['책상', '창문', '서랍', '옷장'], 'answer': 1},
    {'category': '수수께끼', 'question': '비가 그친 뒤 햇빛이 비칠 때 하늘에 여러 색의 띠로 나타나기도 하는 것은 무엇일까요?',
     'options': ['무지개', '별자리', '번개', '안개'], 'answer': 0},
    {'category': '수수께끼', 'question': '몸은 둥글고 발은 없지만, 발로 차면 멀리 굴러가는 것은 무엇일까요?',
     'options': ['상자', '책', '공', '연필'], 'answer': 2},
    {'category': '수수께끼', 'question': '겨울에 눈으로 만들고, 따뜻한 햇볕이 비치면 점점 작아지는 사람은 누구일까요?',
     'options': ['우주인', '소방관', '눈사람', '요리사'], 'answer': 2},
    {'category': '수수께끼', 'question': '아침이 되면 큰 소리로 울려 잠든 사람을 깨우는 물건은 무엇일까요?',
     'options': ['냉장고', '우산', '가위', '알람시계'], 'answer': 3},
    {'category': '수수께끼', 'question': '말은 하지 못하지만 많은 글과 이야기를 품고 있는 것은 무엇일까요?',
     'options': ['책', '모자', '신발', '컵'], 'answer': 0},
    {'category': '수수께끼', 'question': '비 오는 날 자동차 앞유리에서 좌우로 움직이며 물을 닦아 주는 것은 무엇일까요?',
     'options': ['와이퍼', '핸들', '안전벨트', '타이어'], 'answer': 0},
    {'category': '수수께끼', 'question': '누구나 하나씩 가지고 있지만, 자기보다 다른 사람들이 더 자주 불러 주는 것은 무엇일까요?',
     'options': ['신발', '생일', '이름', '가방'], 'answer': 2},
    {'category': '수수께끼', 'question': "학교에 갈 때 등에 메고 책과 필통을 넣어 다니는 '작은 집'은 무엇일까요?",
     'options': ['서랍', '냉장고', '우체통', '가방'], 'answer': 3},
    {'category': '수수께끼', 'question': '버튼을 누르면 어두운 곳을 밝게 비춰 주지만 햇빛은 아닌 것은 무엇일까요?',
     'options': ['우산', '시계', '거울', '손전등'], 'answer': 3},
    {'category': '수수께끼', 'question': '계속 숫자를 보여 주지만 계산 문제를 풀지는 않고, 시간을 알려 주는 것은 무엇일까요?',
     'options': ['계산기', '시계', '달력', '자'], 'answer': 1},
    {'category': '수수께끼', 'question': '눈이 많이 내린 뒤 땅을 덮고 있다가 날씨가 따뜻해지면 녹아 사라지는 하얀 것은 무엇일까요?',
     'options': ['모래', '종이', '눈', '소금'], 'answer': 2},
    {'category': '수수께끼', 'question': '비가 올 때 펼쳐서 머리 위에 들고 다니며 몸이 젖는 것을 막아 주는 것은 무엇일까요?',
     'options': ['수건', '부채', '돗자리', '우산'], 'answer': 3},
]


# ═══════════════════════════════════════════════════
#  게임 상태 초기화
# ═══════════════════════════════════════════════════
def init_game(keep_name=True):
    old_name = st.session_state.get("player_name", "플레이어")
    old_train = st.session_state.get("selected_train", "KTX")
    if old_train not in TRAIN_TYPES:
        old_train = "KTX"
    st.session_state.player_name       = old_name if keep_name else "플레이어"
    st.session_state.selected_train    = old_train
    st.session_state.position          = 0
    st.session_state.binbou_pos        = -8
    st.session_state.binbou_attached   = False
    st.session_state.binbou_effect     = None
    st.session_state.game_phase        = "start"
    st.session_state.current_quiz      = None
    st.session_state.quiz_queue        = []
    st.session_state.used_quiz_indices = []
    st.session_state.last_dice_value   = None
    st.session_state.last_message      = "왼쪽 사이드바에서 게임을 시작하세요."
    st.session_state.winner            = False
    st.session_state.quiz_key          = 0
    st.session_state.animation_event   = None
    st.session_state.play_sound        = None
    st.session_state.score             = 0
    st.session_state.turns             = 0
    st.session_state.correct_streak    = 0
    st.session_state.extra_roll        = False
    st.session_state.bonus_dice        = 0
    st.session_state.hand_items        = []
    st.session_state.active_item       = None
    st.session_state.shield_active     = False
    st.session_state.score_x2         = False
    st.session_state.destination       = random.choice(DEST_CANDIDATES)
    st.session_state.dest_reached      = 0
    st.session_state.event_log         = []
    st.session_state.ghost_game        = None
    st.session_state.treasure_effect   = None
    st.session_state.celebration_event = None


if "position" not in st.session_state:
    init_game(keep_name=False)


def start_game():
    name = st.session_state.get("player_name", "플레이어")
    train_key = st.session_state.get("selected_train", "KTX")
    init_game(keep_name=True)
    st.session_state.player_name   = name
    st.session_state.selected_train = train_key if train_key in TRAIN_TYPES else "KTX"
    train = TRAIN_TYPES[st.session_state.selected_train]
    st.session_state.game_phase   = "ready_to_roll"
    st.session_state.last_message = (
        f"{train['emoji']} {name}님의 {train['name']} 출발! {GOAL_STATION}역을 향해 달립니다!\n"
        f"🎯 현재 목적지: {st.session_state.destination}"
    )


def get_map_bytes():
    for fname in ["line2_map.png", "line2_map(1).png", "line2_map-3.jpg"]:
        p = APP_DIR / fname
        if p.exists():
            return p.read_bytes(), fname.endswith(".jpg")
    st.error("노선도 이미지 파일이 없습니다. line2_map.png 파일을 같은 폴더에 놓아 주세요.")
    st.stop()


def selected_categories():
    cats = st.session_state.get("selected_categories", QUIZ_CATEGORIES)
    return cats or QUIZ_CATEGORIES


def get_random_quiz():
    categories = selected_categories()
    candidate = [i for i, q in enumerate(QUIZZES) if q["category"] in categories]
    if not candidate:
        candidate = list(range(len(QUIZZES)))
    used = set(st.session_state.used_quiz_indices)
    available = [i for i in candidate if i not in used]
    if not available:
        st.session_state.used_quiz_indices = []
        available = candidate[:]
    idx = random.choice(available)
    st.session_state.used_quiz_indices.append(idx)
    quiz = QUIZZES[idx].copy()
    quiz["quiz_id"] = idx
    return quiz


def add_event_log(msg):
    log = st.session_state.event_log
    log.append(msg)
    if len(log) > 6:
        st.session_state.event_log = log[-6:]


def add_item(item_key):
    """아이템을 손패에 추가하고 성공 여부를 반환합니다."""
    hand = st.session_state.hand_items
    if len(hand) >= 3:
        add_event_log("🎒 아이템 보관함이 가득 찼습니다!")
        return False
    hand.append(item_key)
    add_event_log(f"🃏 아이템 획득: {ITEMS[item_key]['name']}")
    return True


def roll_dice_value(use_item=False):
    streak = st.session_state.get("correct_streak", 0)
    bonus = st.session_state.get("bonus_dice", 0)
    dice = random.randint(1, 6)
    if streak >= 3 and random.random() < 0.2:
        dice = max(dice, random.randint(1, 6))
    if use_item or st.session_state.active_item == "double_move":
        dice = min(dice * 2, 12)
        st.session_state.active_item = None
        add_event_log("🚄 2배 이동 카드 사용!")
    dice = min(dice + bonus, 12)
    if bonus > 0:
        add_event_log(f"⚡ 주사위 보너스 +{bonus} 적용!")
    st.session_state.bonus_dice = 0
    return dice


def build_path(start_pos, end_pos):
    """두 역 사이의 인덱스 경로를 양방향으로 생성합니다."""
    step = 1 if end_pos >= start_pos else -1
    return list(range(start_pos, end_pos + step, step))


def sync_binbou_attachment(log_change=True):
    """현재 위치를 기준으로 유령의 접촉 여부를 임시로 표시합니다."""
    was_attached = st.session_state.binbou_attached
    bp = st.session_state.binbou_pos
    now_attached = bp >= 0 and bp >= st.session_state.position

    # 접촉 순간에는 같은 역에 표시합니다. 접촉 효과 처리 후 6칸 뒤로 재배치됩니다.
    if now_attached:
        st.session_state.binbou_pos = st.session_state.position

    st.session_state.binbou_attached = now_attached
    if log_change and now_attached and not was_attached:
        add_event_log("👿 먹보유령이 플레이어를 붙잡았습니다!")
    return now_attached


def reset_binbou_after_catch(distance=BINBOU_RESET_DISTANCE):
    """먹보유령을 플레이어 뒤쪽으로 재배치합니다."""
    distance = max(1, int(distance))
    st.session_state.binbou_pos = max(-8, st.session_state.position - distance)
    st.session_state.binbou_attached = False


def move_binbou(steps):
    bp = st.session_state.binbou_pos + steps
    st.session_state.binbou_pos = max(-8, min(bp, GOAL_INDEX))
    return sync_binbou_attachment(log_change=False)


def show_binbou_effect(message, penalty, effect_type="caught"):
    """먹보유령 결과를 점수, 로그, 보드 오버레이에 반영합니다."""
    penalty = max(0, int(penalty))
    if penalty:
        st.session_state.score = max(0, st.session_state.score - penalty)
    st.session_state.binbou_effect = {
        "id": random.randint(100000, 999999),
        "type": effect_type,
        "message": message,
        "penalty": penalty,
    }
    st.session_state.play_sound = "ghost"
    add_event_log(message)


def begin_ghost_minigame(penalty, resume):
    """유령 접촉 시 즉시 감점하지 않고 3문 탈출 미니게임을 시작합니다."""
    penalty = max(0, int(penalty))
    st.session_state.binbou_pos = st.session_state.position
    st.session_state.binbou_attached = True
    st.session_state.ghost_game = {
        "id": random.randint(100000, 999999),
        # 세 문 중 한 문만 먹보유령 문입니다. 즉, 탈출 성공 확률은 2/3입니다.
        "danger_door": random.randrange(3),
        "penalty": penalty,
        "resume": resume,
    }
    st.session_state.game_phase = "ghost_minigame"
    st.session_state.binbou_effect = {
        "id": random.randint(100000, 999999),
        "type": "challenge",
        "message": "👿 먹보유령에게 잡혔어요! 3개의 문 중 안전한 문을 골라 탈출하세요!",
        "penalty": 0,
    }
    st.session_state.play_sound = "ghost"
    st.session_state.last_message = (
        resume.get("base_msg", "")
        + "\n\n👿 **먹보유령 탈출 미니게임!** 세 문 중 하나를 골라 보세요. "
          "두 문은 안전하고 한 문에만 먹보유령이 숨어 있어요!"
    )
    add_event_log("🚪 먹보유령 탈출 미니게임 시작!")


def continue_after_forward(base_msg, double_quiz, did_win):
    """이동·이벤트·유령 처리가 끝난 뒤 승리 또는 퀴즈 단계로 이어갑니다."""
    if did_win:
        st.session_state.play_sound = "win" if st.session_state.play_sound in (None, "dice") else st.session_state.play_sound
        st.session_state.game_phase = "game_over"
        st.session_state.winner = True
        st.session_state.current_quiz = None
        st.session_state.quiz_queue = []
        st.session_state.last_message = (
            base_msg
            + f"\n\n🎉 {st.session_state.player_name}님이 {GOAL_STATION}역에 도착했습니다!"
            + f"\n총 {st.session_state.turns}턴 · 최종 점수: {st.session_state.score}점"
            + f"\n목적지 도달: {st.session_state.dest_reached}회"
        )
        return

    if double_quiz:
        st.session_state.quiz_queue = [get_random_quiz(), get_random_quiz()]
        st.session_state.current_quiz = st.session_state.quiz_queue.pop(0)
        st.session_state.game_phase = "answering_quiz"
        base_msg += "\n\n📝 퀴즈 2문제 도전!"
    else:
        st.session_state.quiz_queue = []
        st.session_state.current_quiz = get_random_quiz()
        st.session_state.game_phase = "answering_quiz"
        base_msg += "\n\n📝 사이드바에서 퀴즈를 풀어 보세요!"

    st.session_state.last_message = base_msg
    st.session_state.quiz_key += 1


def resolve_ghost_minigame(choice_index):
    """3문 미니게임 결과를 처리한 뒤 원래 게임 흐름으로 복귀합니다."""
    game = st.session_state.get("ghost_game")
    if not game:
        return

    choice_index = int(choice_index)
    danger_door = int(game["danger_door"])
    penalty = int(game.get("penalty", 10))
    resume = game.get("resume", {})
    ghost_start = st.session_state.position
    success = choice_index != danger_door

    if success:
        result_msg = (
            f"💨 {choice_index + 1}번 문 탈출 성공! 먹보유령을 따돌렸어요! "
            "먹보유령이 8칸 뒤로 물러납니다."
        )
        show_binbou_effect(result_msg, 0, "escaped")
        st.session_state.play_sound = "escape"
        reset_binbou_after_catch(distance=8)
    else:
        result_msg = (
            f"😵 {choice_index + 1}번 문에 먹보유령이 숨어 있었어요! 점수 -{penalty}점! "
            "먹보유령은 6칸 뒤에서 다시 따라옵니다."
        )
        show_binbou_effect(result_msg, penalty, "caught")
        reset_binbou_after_catch(distance=BINBOU_RESET_DISTANCE)

    final_ghost = st.session_state.binbou_pos
    reset_path = build_path(ghost_start, final_ghost) if final_ghost >= 0 else []
    did_win = bool(resume.get("did_win", False))
    st.session_state.animation_event = {
        "position": st.session_state.position,
        "binbou_pos": final_ghost,
        "binbou_start_pos": ghost_start,
        "binbou_path_indices": [],
        "binbou_reset_path_indices": reset_path,
        "path_indices": [st.session_state.position],
        "dice": None,
        "win": did_win,
    }
    st.session_state.ghost_game = None

    base_msg = resume.get("base_msg", "") + f"\n\n{result_msg}"
    if resume.get("kind") == "forward":
        continue_after_forward(base_msg, bool(resume.get("double_quiz", False)), did_win)
    else:
        st.session_state.game_phase = "ready_to_roll"
        st.session_state.last_message = base_msg + "\n\n다시 주사위를 굴려 보세요."


def apply_destination_reward(station_name, messages):
    """칸 종류와 무관하게 목적지 도착 보상을 적용합니다."""
    if station_name != st.session_state.destination:
        return

    st.session_state.score += 50
    st.session_state.dest_reached += 1
    add_event_log(f"🎯 목적지 {station_name} 도달! +50점!")
    messages.append(f"🎯 목적지 {station_name}에 도착! +50점 획득!")

    candidates = [d for d in DEST_CANDIDATES if d != station_name]
    if candidates:
        st.session_state.destination = random.choice(candidates)
        messages.append(f"📌 새 목적지: {st.session_state.destination}")


def apply_square_event(station_name, pos):
    sq = SQUARE_TYPES.get(station_name, "normal")
    messages = []
    double_quiz = False
    ghost_penalty = 10

    # 목적지 도착은 칸 종류와 독립적으로 판정합니다.
    reached_destination = station_name == st.session_state.destination
    apply_destination_reward(station_name, messages)

    if sq == "blue":
        ev = random.choice(BLUE_EVENTS)
        messages.append(ev["msg"])
        if ev.get("score"):
            st.session_state.score += ev["score"]
        if ev.get("extra_roll"):
            st.session_state.extra_roll = True
        if ev.get("bonus_dice"):
            st.session_state.bonus_dice += ev["bonus_dice"]
        if ev.get("item") and not add_item(ev["item"]):
            messages[-1] = "🎒 아이템 보관함이 가득 차 카드를 받지 못했습니다."
        if ev.get("push_binbou", 0) > 0:
            move_binbou(-ev["push_binbou"])
            messages.append(f"📍 먹보유령 {ev['push_binbou']}칸 후퇴!")

    elif sq == "red":
        if st.session_state.shield_active:
            st.session_state.shield_active = False
            messages.append("🛡️ 방어 카드로 빨간 칸 이벤트 무효화!")
            add_event_log("🛡️ 방어 카드 발동!")
        else:
            ev = random.choice(RED_EVENTS)
            messages.append(ev["msg"])
            if ev.get("score"):
                st.session_state.score = max(0, st.session_state.score + ev["score"])
            if ev.get("move"):
                new_pos = max(0, min(pos + ev["move"], GOAL_INDEX))
                st.session_state.position = new_pos
                sync_binbou_attachment(log_change=False)
                messages.append(f"📍 → {STATIONS[new_pos]}역으로 이동!")
            if ev.get("double_quiz"):
                double_quiz = True
            if ev.get("push_binbou", 0) < 0:
                move_binbou(-ev["push_binbou"])

    elif sq == "star":
        if not reached_destination:
            messages.append(f"⭐ 목적지 카드 칸! 현재 목적지: {st.session_state.destination}")
        if random.random() < 0.4:
            item = random.choice(list(ITEMS.keys()))
            if add_item(item):
                messages.append(f"🃏 보너스 아이템: {ITEMS[item]['name']}!")
            else:
                messages.append("🎒 보관함이 가득 차 보너스 아이템을 받지 못했습니다.")

    elif sq == "treasure":
        ev = random.choice(TREASURE_EVENTS)
        treasure_msg = ev["msg"]
        if ev.get("score"):
            st.session_state.score += int(ev["score"])
        if ev.get("bonus_dice"):
            st.session_state.bonus_dice += int(ev["bonus_dice"])
        if ev.get("push_binbou", 0) > 0:
            move_binbou(-int(ev["push_binbou"]))
        if ev.get("random_item"):
            item = random.choice(list(ITEMS.keys()))
            if add_item(item):
                treasure_msg += f" 획득 아이템: {ITEMS[item]['name']}"
            else:
                treasure_msg += " 하지만 아이템 보관함이 가득 찼어요."
        messages.append(f"🎁 보물상자 OPEN! {treasure_msg}")
        st.session_state.treasure_effect = {
            "id": random.randint(100000, 999999),
            "message": treasure_msg,
        }
        st.session_state.play_sound = "treasure"
        add_event_log(f"🎁 {station_name}역 보물상자: {treasure_msg}")

    elif sq == "trap":
        ev = random.choice(TRAP_EVENTS)
        messages.append(ev["msg"])
        ghost_penalty = int(ev.get("ghost_penalty", 20))
        if ev.get("binbou_attach"):
            # 함정에서는 유령을 즉시 플레이어 위치로 소환하고 미니게임을 시작합니다.
            st.session_state.binbou_pos = st.session_state.position
            sync_binbou_attachment(log_change=False)

    return "\n\n".join(messages) if messages else None, double_quiz, ghost_penalty


def move_forward():
    if st.session_state.game_phase != "ready_to_roll":
        return

    old_pos = st.session_state.position
    if st.session_state.binbou_attached:
        reset_binbou_after_catch()
    old_binbou_pos = st.session_state.binbou_pos

    st.session_state.play_sound = None
    st.session_state.binbou_effect = None
    st.session_state.treasure_effect = None

    dice = roll_dice_value(use_item=st.session_state.active_item == "double_move")
    landing_pos = min(old_pos + dice, GOAL_INDEX)
    st.session_state.position = landing_pos
    st.session_state.last_dice_value = dice
    st.session_state.turns += 1

    # 플레이어가 이동한 뒤 유령이 실제 경로를 따라 추격합니다.
    if st.session_state.binbou_pos >= 0:
        ghost_steps = min(9, dice + random.randint(0, 3))
        move_binbou(ghost_steps)
    elif st.session_state.turns >= 5:
        st.session_state.binbou_pos = max(0, landing_pos - 8)
        sync_binbou_attachment(log_change=False)
        add_event_log("👿 먹보유령이 등장했습니다!")

    landing_station = STATIONS[landing_pos]
    ev_msg, double_quiz, ghost_penalty = apply_square_event(landing_station, landing_pos)

    # 칸 이벤트까지 처리한 뒤 실제 접촉 여부를 확인합니다. 감점은 미니게임 결과 뒤에 적용합니다.
    touching_ghost = sync_binbou_attachment(log_change=False)
    binbou_before_contact = st.session_state.binbou_pos

    final_pos = st.session_state.position
    final_station = STATIONS[final_pos]
    final_binbou_pos = st.session_state.binbou_pos

    path_indices = build_path(old_pos, landing_pos)
    if final_pos != landing_pos:
        path_indices.extend(build_path(landing_pos, final_pos)[1:])

    binbou_path_indices = []
    if old_binbou_pos >= 0 and binbou_before_contact >= 0:
        binbou_path_indices = build_path(old_binbou_pos, binbou_before_contact)
    elif old_binbou_pos < 0 and binbou_before_contact >= 0:
        binbou_path_indices = [binbou_before_contact]

    did_win = final_pos >= GOAL_INDEX
    st.session_state.animation_event = {
        "position": final_pos,
        "binbou_pos": final_binbou_pos,
        "binbou_start_pos": old_binbou_pos,
        "binbou_path_indices": binbou_path_indices,
        "binbou_reset_path_indices": [],
        "path_indices": path_indices,
        "dice": dice,
        "win": did_win,
    }

    add_event_log(f"📍 {landing_station}역 도착 (주사위 {dice})")
    base_msg = (
        f"🎲 주사위 **{dice}** → **{landing_station}**역 도착!\n"
        f"({landing_pos + 1}/{len(STATIONS)}역 · 점수: {st.session_state.score})"
    )
    if ev_msg:
        base_msg += f"\n\n{ev_msg}"
    if final_pos != landing_pos:
        base_msg += f"\n\n📌 현재 위치: **{final_station}**역"

    # 유령에게 잡혔다면 승리·퀴즈보다 먼저 미니게임을 해결합니다.
    if touching_ghost:
        begin_ghost_minigame(
            ghost_penalty,
            {
                "kind": "forward",
                "base_msg": base_msg,
                "double_quiz": double_quiz,
                "did_win": did_win,
            },
        )
        return

    if st.session_state.play_sound is None:
        st.session_state.play_sound = "dice"
    continue_after_forward(base_msg, double_quiz, did_win)


def move_backward():
    if st.session_state.game_phase != "waiting_penalty_roll":
        return

    st.session_state.quiz_queue = []
    st.session_state.extra_roll = False

    if "skip_penalty" in st.session_state.hand_items:
        st.session_state.hand_items.remove("skip_penalty")
        st.session_state.game_phase = "ready_to_roll"
        st.session_state.last_message = "✨ 면제 카드 사용! 뒤로 가기 주사위 면제!\n\n다시 주사위를 굴려 보세요."
        add_event_log("✨ 면제 카드 발동!")
        return

    old_pos = st.session_state.position
    if st.session_state.binbou_attached:
        reset_binbou_after_catch()
    old_binbou_pos = st.session_state.binbou_pos

    st.session_state.play_sound = None
    st.session_state.binbou_effect = None
    dice = random.randint(1, 4)
    new_pos = max(0, old_pos - dice)
    st.session_state.position = new_pos
    st.session_state.last_dice_value = dice
    st.session_state.current_quiz = None
    st.session_state.correct_streak = 0

    move_binbou(dice)
    touching_ghost = sync_binbou_attachment(log_change=False)
    binbou_before_contact = st.session_state.binbou_pos

    binbou_path_indices = []
    if old_binbou_pos >= 0 and binbou_before_contact >= 0:
        binbou_path_indices = build_path(old_binbou_pos, binbou_before_contact)
    elif old_binbou_pos < 0 and binbou_before_contact >= 0:
        binbou_path_indices = [binbou_before_contact]

    st.session_state.animation_event = {
        "position": new_pos,
        "binbou_pos": st.session_state.binbou_pos,
        "binbou_start_pos": old_binbou_pos,
        "binbou_path_indices": binbou_path_indices,
        "binbou_reset_path_indices": [],
        "path_indices": build_path(old_pos, new_pos),
        "dice": dice,
        "win": False,
    }
    add_event_log(f"😢 뒤로 -{dice}칸 → {STATIONS[new_pos]}역")
    base_msg = f"😢 뒤로 가기 주사위 **{dice}** → **{STATIONS[new_pos]}**역으로 후퇴!"

    if touching_ghost:
        begin_ghost_minigame(
            10,
            {"kind": "backward", "base_msg": base_msg, "did_win": False},
        )
        return

    st.session_state.play_sound = "wrong"
    st.session_state.game_phase = "ready_to_roll"
    st.session_state.last_message = base_msg + "\n\n다시 주사위를 굴려 보세요."


def submit_answer(answer):
    quiz = st.session_state.current_quiz
    if quiz is None:
        return
    correct  = quiz["options"][quiz["answer"]]
    score_x2 = st.session_state.score_x2
    if answer == correct:
        gained = 20 if score_x2 else 10
        st.session_state.score          += gained
        st.session_state.correct_streak += 1
        if score_x2:
            st.session_state.score_x2 = False
        streak    = st.session_state.correct_streak
        bonus_msg = ""
        st.session_state.celebration_event = None
        if streak >= 3:
            st.session_state.score += 5
            bonus_msg = f" 🔥 연속 {streak}정답 보너스 +5점!"
            st.session_state.celebration_event = {
                "id": random.randint(100000, 999999),
                "streak": streak,
                "message": f"🔥 {streak}연속 정답! 대단해요!",
            }
            st.session_state.play_sound = "streak"
        else:
            st.session_state.play_sound = "correct"
        st.session_state.current_quiz = None
        add_event_log(f"✅ 정답! +{gained}점{bonus_msg}")

        if st.session_state.quiz_queue:
            st.session_state.current_quiz = st.session_state.quiz_queue.pop(0)
            st.session_state.game_phase   = "answering_quiz"
            st.session_state.last_message = f"✅ 정답! (+{gained}점{bonus_msg})\n\n📝 다음 퀴즈!"
        elif st.session_state.extra_roll:
            st.session_state.extra_roll  = False
            st.session_state.game_phase  = "ready_to_roll"
            st.session_state.last_message = f"✅ 정답! (+{gained}점{bonus_msg})\n\n🎲 보너스 주사위 발동!"
        else:
            st.session_state.game_phase  = "ready_to_roll"
            st.session_state.last_message = f"✅ 정답! (+{gained}점{bonus_msg})\n\n주사위를 굴려 보세요."
        st.session_state.quiz_key += 1
    else:
        st.session_state.correct_streak = 0
        st.session_state.celebration_event = None
        st.session_state.play_sound = "wrong"
        st.session_state.game_phase = "waiting_penalty_roll"
        st.session_state.last_message = (
            f"❌ 정답은 **'{correct}'** 입니다.\n\n"
            f"사이드바에서 뒤로 가기 주사위를 굴려 주세요!"
        )
        st.session_state.current_quiz = None
        st.session_state.quiz_queue = []
        st.session_state.extra_roll = False
        add_event_log(f"❌ 오답! 정답: {correct}")



def render_board(map_bytes, is_jpg):
    img_mime  = "jpeg" if is_jpg else "png"
    image_b64 = base64.b64encode(map_bytes).decode("ascii")

    payload = {
        "image":           f"data:image/{img_mime};base64,{image_b64}",
        "stations":        STATIONS,
        "points":          STATION_POINTS,
        "position":        st.session_state.position,
        "binbou_pos":      st.session_state.binbou_pos,
        "binbou_attached": st.session_state.binbou_attached,
        "binbouEffect":    st.session_state.get("binbou_effect"),
        "goal_index":      GOAL_INDEX,
        "playerName":      st.session_state.player_name,
        "trainKey":        st.session_state.get("selected_train", "KTX"),
        "train":           TRAIN_TYPES.get(st.session_state.get("selected_train", "KTX"), TRAIN_TYPES["KTX"]),
        "destination":     st.session_state.destination,
        "lastDice":        st.session_state.last_dice_value,
        "phase":           st.session_state.game_phase,
        "winner":          st.session_state.winner,
        "score":           st.session_state.score,
        "turns":           st.session_state.turns,
        "streak":          st.session_state.correct_streak,
        "destReached":     st.session_state.dest_reached,
        "squareTypes":     SQUARE_TYPES,
        "soundEnabled":    st.session_state.get("sound_enabled", True),
        "playSound":       st.session_state.get("play_sound"),
        "event":           st.session_state.animation_event,
        "eventLog":        st.session_state.event_log,
        "treasureEffect":  st.session_state.get("treasure_effect"),
        "celebrationEffect": st.session_state.get("celebration_event"),
    }
    pj = json.dumps(payload, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#1a0a2e;font-family:'Noto Sans KR',sans-serif;overflow:hidden}}
#wrap{{display:flex;gap:10px;padding:8px;height:100vh}}
#board-col{{flex:1;min-width:0}}
#right-col{{width:200px;display:flex;flex-direction:column;gap:8px}}
#board-container{{position:relative;width:100%;aspect-ratio:{ORIGINAL_WIDTH}/{ORIGINAL_HEIGHT};border-radius:14px;overflow:hidden;box-shadow:0 0 40px rgba(100,0,255,0.4);border:2px solid #6c3fc5}}
#board-img{{position:absolute;inset:0;width:100%;height:100%;object-fit:fill}}
.token{{position:absolute;width:34px;height:34px;border-radius:50%;border:3px solid #fff;display:flex;align-items:center;justify-content:center;font-size:18px;z-index:12;pointer-events:none;transform:translate(-50%,-50%)}}
#token-player{{background:radial-gradient(circle at 35% 35%,#8fd3ff,#2f80ed);box-shadow:0 0 14px 4px rgba(47,128,237,.9);animation:playerPulse 1.4s ease-in-out infinite}}
#token-binbou{{background:radial-gradient(circle at 35% 35%,#ff6b6b,#8e44ad);box-shadow:0 0 14px 4px rgba(142,68,173,.9);animation:binbouPulse 1s ease-in-out infinite;z-index:11}}
@keyframes playerPulse{{0%,100%{{box-shadow:0 0 10px 3px rgba(46,204,113,.8)}}50%{{box-shadow:0 0 24px 10px rgba(46,204,113,.3)}}}}
@keyframes binbouPulse{{0%,100%{{box-shadow:0 0 10px 3px rgba(255,0,100,.8)}}50%{{box-shadow:0 0 24px 10px rgba(255,0,100,.3)}}}}
.sdot{{position:absolute;width:11px;height:11px;border-radius:50%;transform:translate(-50%,-50%);z-index:5}}
.sdot-normal{{background:rgba(255,255,255,.12)}}
.sdot-blue{{background:rgba(52,152,219,.6);box-shadow:0 0 7px rgba(52,152,219,.8)}}
.sdot-red{{background:rgba(231,76,60,.6);box-shadow:0 0 7px rgba(231,76,60,.8)}}
.sdot-star{{background:rgba(241,196,15,.7);box-shadow:0 0 9px rgba(241,196,15,.9);width:14px;height:14px;animation:starGlow 1.8s ease-in-out infinite}}
.sdot-trap{{background:rgba(142,68,173,.7);box-shadow:0 0 7px rgba(142,68,173,.9)}}
.sdot-treasure{{background:#ff9f1c;box-shadow:0 0 10px 3px rgba(255,159,28,.75);width:15px;height:15px;animation:treasureDot 1.2s ease-in-out infinite}}
@keyframes treasureDot{{0%,100%{{transform:translate(-50%,-50%) scale(1) rotate(0)}}50%{{transform:translate(-50%,-50%) scale(1.35) rotate(12deg)}}}}
.sdot-goal{{background:#00ff88;box-shadow:0 0 14px 5px rgba(0,255,136,.8);width:18px;height:18px;animation:goalGlow 1s ease-in-out infinite}}
.sdot-active{{outline:3px solid #fff;outline-offset:2px}}
@keyframes starGlow{{0%,100%{{transform:translate(-50%,-50%) scale(1)}}50%{{transform:translate(-50%,-50%) scale(1.5)}}}}
@keyframes goalGlow{{0%,100%{{box-shadow:0 0 10px 4px rgba(0,255,136,.8)}}50%{{box-shadow:0 0 22px 10px rgba(0,255,136,.4)}}}}
.slabel{{position:absolute;transform:translate(-50%,-215%);background:rgba(10,0,30,.9);color:#2ecc71;padding:2px 7px;border-radius:5px;font-size:11px;white-space:nowrap;z-index:16;pointer-events:none;border:1px solid #2ecc71;animation:labelPop .35s ease-out}}
@keyframes labelPop{{0%{{opacity:0;transform:translate(-50%,-185%) scale(.8)}}100%{{opacity:1;transform:translate(-50%,-215%) scale(1)}}}}
.pbar-wrap{{position:absolute;bottom:0;left:0;right:0;height:7px;background:rgba(255,255,255,.1);z-index:20}}
.pbar{{height:100%;background:linear-gradient(90deg,#2ecc71,#f1c40f,#e74c3c);transition:width .7s ease}}
#dest-banner{{position:absolute;top:10px;left:10px;background:rgba(0,0,0,.8);border:2px solid #f1c40f;border-radius:10px;padding:5px 10px;color:#f1c40f;font-size:12px;font-weight:700;z-index:20}}
#dice-overlay{{display:none;position:absolute;inset:0;background:rgba(0,0,0,.55);align-items:center;justify-content:center;z-index:40;border-radius:14px;flex-direction:column;gap:12px}}
#dice-overlay.show{{display:flex}}
#dice-canvas{{width:120px;height:120px;border-radius:18px;box-shadow:0 0 40px rgba(241,196,15,.7)}}
#dice-result-txt{{color:#f1c40f;font-size:2.2em;font-weight:900;text-shadow:0 0 14px rgba(241,196,15,.9);opacity:0;transition:opacity .3s}}
#dice-result-txt.show{{opacity:1}}
#confetti-canvas{{display:none;position:absolute;inset:0;z-index:45;pointer-events:none;border-radius:14px}}
#confetti-canvas.show{{display:block}}
#wrong-overlay{{display:none;position:absolute;inset:0;background:rgba(0,0,0,.6);align-items:center;justify-content:center;flex-direction:column;gap:10px;z-index:45;border-radius:14px}}
#wrong-overlay.show{{display:flex;animation:wrongShake .4s ease}}
@keyframes wrongShake{{0%{{transform:translateX(0)}}15%{{transform:translateX(-10px)}}30%{{transform:translateX(10px)}}45%{{transform:translateX(-8px)}}60%{{transform:translateX(8px)}}75%{{transform:translateX(-4px)}}90%{{transform:translateX(4px)}}100%{{transform:translateX(0)}}}}
#ghost-overlay{{display:none;position:absolute;inset:0;background:rgba(30,0,45,.78);align-items:center;justify-content:center;flex-direction:column;gap:10px;z-index:48;border-radius:14px;text-align:center;padding:20px}}
#ghost-overlay.show{{display:flex;animation:ghostFlash .55s ease}}
#ghost-emoji{{font-size:6.5em;animation:ghostCatch .65s ease-out}}
#ghost-txt{{color:#ff8cff;font-size:1.55em;font-weight:900;text-shadow:0 0 16px rgba(255,70,255,.9)}}
#treasure-overlay{{display:none;position:absolute;inset:0;background:rgba(22,8,0,.74);align-items:center;justify-content:center;flex-direction:column;gap:10px;z-index:47;border-radius:14px;text-align:center;padding:20px}}
#treasure-overlay.show{{display:flex;animation:treasureFlash .45s ease}}
#treasure-emoji{{font-size:7em;animation:treasureOpen .8s cubic-bezier(.2,.8,.2,1)}}
#treasure-txt{{color:#ffd166;font-size:1.45em;font-weight:900;text-shadow:0 0 16px rgba(255,190,50,.85);max-width:80%}}
@keyframes treasureOpen{{0%{{transform:scale(.3) rotate(-15deg);opacity:.2}}45%{{transform:scale(1.25) rotate(10deg)}}75%{{transform:scale(.92) rotate(-4deg)}}100%{{transform:scale(1);opacity:1}}}}
@keyframes treasureFlash{{0%{{background:rgba(255,205,60,.12)}}100%{{background:rgba(22,8,0,.74)}}}}
#streak-overlay{{display:none;position:absolute;inset:0;align-items:center;justify-content:center;flex-direction:column;z-index:49;pointer-events:none;text-align:center;background:radial-gradient(circle,rgba(255,217,61,.28),rgba(20,0,50,.45) 60%,rgba(20,0,50,.15))}}
#streak-overlay.show{{display:flex;animation:streakFlash 1.8s ease both}}
#streak-main{{font-size:2.4em;font-weight:900;color:#fff3a3;text-shadow:0 0 12px #ff8c00,0 0 28px #ff3d00;animation:streakPop .7s cubic-bezier(.2,1.5,.4,1)}}
#streak-stars{{font-size:2.2em;letter-spacing:12px;animation:starSpin 1.2s linear infinite}}
@keyframes streakPop{{0%{{transform:scale(.2) rotate(-12deg);opacity:0}}70%{{transform:scale(1.2) rotate(4deg)}}100%{{transform:scale(1);opacity:1}}}}
@keyframes streakFlash{{0%{{opacity:0}}15%{{opacity:1}}80%{{opacity:1}}100%{{opacity:0}}}}
@keyframes starSpin{{0%{{transform:rotate(-5deg) scale(.9)}}50%{{transform:rotate(5deg) scale(1.15)}}100%{{transform:rotate(-5deg) scale(.9)}}}}
@keyframes ghostFlash{{0%{{background:rgba(255,0,100,.15)}}40%{{background:rgba(60,0,90,.92)}}100%{{background:rgba(30,0,45,.78)}}}}
@keyframes ghostCatch{{0%{{transform:scale(.2) rotate(-20deg);opacity:0}}60%{{transform:scale(1.35) rotate(8deg)}}100%{{transform:scale(1);opacity:1}}}}
#wrong-emoji{{font-size:6em;animation:wrongBounce .5s ease-out}}
@keyframes wrongBounce{{0%{{transform:scale(.2);opacity:0}}60%{{transform:scale(1.2)}}100%{{transform:scale(1);opacity:1}}}}
#wrong-txt{{color:#ff6b6b;font-size:1.4em;font-weight:900;text-shadow:0 0 12px rgba(255,100,100,.8)}}
#win-overlay{{display:none;position:absolute;inset:0;background:rgba(0,0,0,.85);align-items:center;justify-content:center;flex-direction:column;z-index:50;border-radius:14px}}
#win-overlay.show{{display:flex}}
.win-txt{{color:#f1c40f;font-size:2.6em;font-weight:900;text-align:center;animation:winPop .6s ease-out;text-shadow:0 0 20px rgba(241,196,15,.8)}}
@keyframes winPop{{0%{{transform:scale(.3) rotate(-20deg);opacity:0}}100%{{transform:scale(1) rotate(0);opacity:1}}}}
.panel{{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.15);border-radius:10px;padding:8px;color:#fff}}
.panel-title{{font-size:11px;font-weight:700;color:#aaa;margin-bottom:6px;letter-spacing:.5px}}
.stat-row{{display:flex;justify-content:space-between;font-size:12px;margin-bottom:3px}}
.stat-val{{font-weight:700;color:#f1c40f}}
.log-item{{font-size:10px;color:#ccc;padding:2px 0;border-bottom:1px solid rgba(255,255,255,.05)}}
.legend-row{{display:flex;align-items:center;gap:5px;font-size:10px;color:#ccc;margin-bottom:3px}}
.legend-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
</style></head>
<body>
<div id="wrap">
  <div id="board-col">
    <div id="board-container">
      <img id="board-img" src="" alt="노선도">
      <div id="token-player" class="token">🚄</div>
      <div id="token-binbou" class="token" style="display:none">👿</div>
      <div id="station-label" class="slabel" style="display:none"></div>
      <div id="dest-banner">🎯 목적지: <span id="dest-name">-</span></div>
      <div class="pbar-wrap"><div class="pbar" id="progress-bar" style="width:0%"></div></div>
      <div id="dice-overlay">
        <canvas id="dice-canvas" width="240" height="240"></canvas>
        <div id="dice-result-txt"></div>
      </div>
      <canvas id="confetti-canvas"></canvas>
      <div id="wrong-overlay">
        <div id="wrong-emoji">😢</div>
        <div id="wrong-txt">아쉬워요...</div>
      </div>
      <div id="treasure-overlay">
        <div id="treasure-emoji">🎁</div>
        <div id="treasure-txt">보물상자 발견!</div>
      </div>
      <div id="ghost-overlay">
        <div id="ghost-emoji">👿</div>
        <div id="ghost-txt">먹보유령에게 붙잡혔습니다!</div>
      </div>
      <div id="streak-overlay">
        <div id="streak-stars">✨ ⭐ ✨</div>
        <div id="streak-main">연속 정답!</div>
      </div>
      <div id="win-overlay">
        <div class="win-txt">🎉 건대입구 도착! 🎉</div>
        <div style="color:#fff;margin-top:14px;font-size:1.2em" id="win-details"></div>
      </div>
    </div>
  </div>
  <div id="right-col">
    <div class="panel">
      <div class="panel-title">📊 현황</div>
      <div class="stat-row"><span>점수</span><span class="stat-val" id="s-score">0</span></div>
      <div class="stat-row"><span>턴</span><span class="stat-val" id="s-turns">0</span></div>
      <div class="stat-row"><span>스트릭</span><span class="stat-val" id="s-streak">0</span></div>
      <div class="stat-row"><span>목적지</span><span class="stat-val" id="s-dest">0회</span></div>
      <div class="stat-row"><span>열차</span><span class="stat-val" id="s-train">KTX</span></div>
    </div>
    <div class="panel">
      <div class="panel-title">👿 먹보유령 거리</div>
      <div id="binbou-gauge-wrap" style="background:rgba(255,255,255,.08);border-radius:6px;height:16px;overflow:hidden">
        <div id="binbou-gauge" style="height:100%;background:linear-gradient(90deg,#8e44ad,#e74c3c);transition:width .5s;width:0%"></div>
      </div>
      <div style="font-size:10px;color:#ccc;margin-top:3px" id="binbou-txt">미등장</div>
    </div>
    <div class="panel" style="flex:1;overflow:hidden">
      <div class="panel-title">📋 이벤트 로그</div>
      <div id="event-log"></div>
    </div>
    <div class="panel">
      <div class="panel-title">🗺️ 칸 범례</div>
      <div class="legend-row"><div class="legend-dot" style="background:#3498db"></div><span>파란칸 (보너스)</span></div>
      <div class="legend-row"><div class="legend-dot" style="background:#e74c3c"></div><span>빨간칸 (패널티)</span></div>
      <div class="legend-row"><div class="legend-dot" style="background:#f1c40f"></div><span>별칸 (목적지)</span></div>
      <div class="legend-row"><div class="legend-dot" style="background:#8e44ad"></div><span>함정칸</span></div>
      <div class="legend-row"><div class="legend-dot" style="background:#ff9f1c"></div><span>보물상자칸</span></div>
      <div class="legend-row"><div class="legend-dot" style="background:#00ff88"></div><span>도착역</span></div>
    </div>
  </div>
</div>
<script id="data-script" type="application/json">{pj}</script>
<script>
(function(){{
  const d=JSON.parse(document.getElementById('data-script').textContent);
  const container=document.getElementById('board-container');
  const boardImg=document.getElementById('board-img');
  const tokenPlayer=document.getElementById('token-player');
  const tokenBinbou=document.getElementById('token-binbou');
  const label=document.getElementById('station-label');
  const pbar=document.getElementById('progress-bar');
  const winOverlay=document.getElementById('win-overlay');
  const diceOverlay=document.getElementById('dice-overlay');
  const diceCanvas=document.getElementById('dice-canvas');
  const diceResultTxt=document.getElementById('dice-result-txt');
  const ctx2d=diceCanvas.getContext('2d');
  const confettiCanvas=document.getElementById('confetti-canvas');
  const wrongOverlay=document.getElementById('wrong-overlay');
  const ghostOverlay=document.getElementById('ghost-overlay');
  const ghostTxt=document.getElementById('ghost-txt');
  const treasureOverlay=document.getElementById('treasure-overlay');
  const treasureTxt=document.getElementById('treasure-txt');
  const streakOverlay=document.getElementById('streak-overlay');
  const streakMain=document.getElementById('streak-main');

  document.getElementById('s-score').textContent=d.score||0;
  document.getElementById('s-turns').textContent=d.turns||0;
  document.getElementById('s-streak').textContent=d.streak||0;
  document.getElementById('s-dest').textContent=(d.destReached||0)+'회';
  document.getElementById('s-train').textContent=(d.train&&d.train.name)||d.trainKey||'KTX';
  document.getElementById('dest-name').textContent=d.destination||'-';
  if(d.train){{
    tokenPlayer.textContent=d.train.emoji||'🚄';
    tokenPlayer.style.background='radial-gradient(circle at 35% 35%,#ffffff,'+(d.train.color||'#2f80ed')+')';
    tokenPlayer.style.boxShadow='0 0 14px 4px '+(d.train.glow||'rgba(47,128,237,.85)');
    tokenPlayer.title=(d.train.name||'열차')+' · '+(d.playerName||'플레이어');
  }}
  const pct=d.stations.length>1?(d.position/(d.stations.length-1)*100).toFixed(1):0;
  pbar.style.width=pct+'%';

  const bp=d.binbou_pos,pp=d.position;
  if(bp>=0){{
    const dist=Math.max(0,pp-bp);
    document.getElementById('binbou-gauge').style.width=Math.max(0,100-dist*10)+'%';
    document.getElementById('binbou-txt').textContent=d.binbou_attached?'👿 밀착 중!':dist+'칸 뒤';
  }}

  function placeTokenAt(el,xPct,yPct){{
    el.style.left=xPct+'%';
    el.style.top=yPct+'%';
  }}

  function drawDots(){{
    d.stations.forEach((name,i)=>{{
      const pt=d.points[name];if(!pt)return;
      const dot=document.createElement('div');
      let cls='sdot ';
      if(i===d.goal_index)cls+='sdot-goal';
      else if(d.squareTypes[name])cls+='sdot-'+d.squareTypes[name];
      else cls+='sdot-normal';
      if(i===d.position)cls+=' sdot-active';
      dot.className=cls;
      dot.style.left=pt.x+'%';
      dot.style.top=pt.y+'%';
      dot.title=name;
      container.appendChild(dot);
    }});
  }}

  const DICE_DOTS={{1:[[.5,.5]],2:[[.25,.25],[.75,.75]],3:[[.25,.25],[.5,.5],[.75,.75]],4:[[.25,.25],[.75,.25],[.25,.75],[.75,.75]],5:[[.25,.25],[.75,.25],[.5,.5],[.25,.75],[.75,.75]],6:[[.25,.2],[.75,.2],[.25,.5],[.75,.5],[.25,.8],[.75,.8]]}};
  function drawDiceFace(val,angle){{
    const W=240,H=240,R=26;ctx2d.clearRect(0,0,W,H);ctx2d.save();ctx2d.translate(W/2,H/2);ctx2d.rotate(angle);
    const g=ctx2d.createLinearGradient(-W/2,-H/2,W/2,H/2);g.addColorStop(0,'#fffde7');g.addColorStop(1,'#fff9c4');
    ctx2d.beginPath();ctx2d.roundRect(-W/2+10,-H/2+10,W-20,H-20,R);ctx2d.fillStyle=g;ctx2d.fill();
    ctx2d.shadowColor='rgba(241,196,15,.8)';ctx2d.shadowBlur=18;ctx2d.strokeStyle='#f39c12';ctx2d.lineWidth=4;ctx2d.stroke();ctx2d.shadowBlur=0;
    const dots=DICE_DOTS[val]||DICE_DOTS[1],area=W-40;
    dots.forEach(([fx,fy])=>{{ctx2d.beginPath();ctx2d.arc(-W/2+20+area*fx,-H/2+20+area*fy,14,0,Math.PI*2);ctx2d.fillStyle='#c0392b';ctx2d.fill();}});
    ctx2d.restore();
  }}
  function easeOut3(t){{return 1-(1-t)*(1-t)*(1-t);}}
  function runDiceAnim(finalVal,onDone){{
    diceOverlay.classList.add('show');diceResultTxt.classList.remove('show');diceResultTxt.textContent='';
    const TOTAL=900,t0=performance.now();
    function frame(now){{
      const elapsed=now-t0,p=Math.min(elapsed/TOTAL,1),e=easeOut3(p);
      const showVal=p>0.75?finalVal:(Math.floor(Math.random()*6)+1);
      drawDiceFace(showVal,(1-e)*(elapsed/TOTAL)*Math.PI*4);
      if(p<1)setTimeout(()=>requestAnimationFrame(frame),60+e*180);
      else{{drawDiceFace(finalVal,0);diceResultTxt.textContent=finalVal+'칸 이동!';diceResultTxt.classList.add('show');setTimeout(()=>{{diceOverlay.classList.remove('show');diceResultTxt.classList.remove('show');onDone();}},600);}}
    }}
    requestAnimationFrame(frame);
  }}

  function easeInOut5(t){{return t<0.5?16*t*t*t*t*t:1-Math.pow(-2*t+2,5)/2;}}
  function catmullRom(p0,p1,p2,p3,t){{const t2=t*t,t3=t2*t;return 0.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t2+(-p0+3*p1-3*p2+p3)*t3);}}
  function buildSpline(pathIndices){{
    const pts=pathIndices.map(i=>d.points[d.stations[i]]).filter(Boolean);
    if(pts.length<2)return pts;
    const f=pts[0],l=pts[pts.length-1];
    return [{{x:2*f.x-pts[1].x,y:2*f.y-pts[1].y}},...pts,{{x:2*l.x-pts[pts.length-2].x,y:2*l.y-pts[pts.length-2].y}}];
  }}
  function sampleSpline(ctrl,totalSamples){{
    const segs=ctrl.length-3,result=[];
    for(let s=0;s<segs;s++){{
      const p0=ctrl[s],p1=ctrl[s+1],p2=ctrl[s+2],p3=ctrl[s+3];
      const n=Math.max(4,Math.round(totalSamples/segs));
      for(let i=0;i<n;i++){{const t=i/n;result.push({{x:catmullRom(p0.x,p1.x,p2.x,p3.x,t),y:catmullRom(p0.y,p1.y,p2.y,p3.y,t)}});}}
    }}
    const last=ctrl[ctrl.length-2];result.push({{x:last.x,y:last.y}});return result;
  }}
  function animateToken(pathIndices,doneCallback){{
    if(!pathIndices||pathIndices.length<2){{
      const pt=d.points[d.stations[d.position]];
      if(pt)placeTokenAt(tokenPlayer,pt.x,pt.y);
      doneCallback&&doneCallback();return;
    }}
    const ctrl=buildSpline(pathIndices);
    const SAMPLES=Math.max(60,pathIndices.length*20);
    const curve=sampleSpline(ctrl,SAMPLES);
    const finalName=d.stations[pathIndices[pathIndices.length-1]];
    const TOTAL_MS=Math.min(pathIndices.length*220,2000);
    const t0=performance.now();
    function frame(now){{
      const elapsed=now-t0,rawT=Math.min(elapsed/TOTAL_MS,1),eased=easeInOut5(rawT);
      const idx=Math.min(Math.floor(eased*(curve.length-1)),curve.length-1);
      const pt=curve[idx];
      placeTokenAt(tokenPlayer,pt.x,pt.y);
      if(rawT>0.8){{
        const fp=d.points[finalName];
        if(fp){{label.textContent=finalName;label.style.left=fp.x+'%';label.style.top=fp.y+'%';label.style.display='block';}}
      }}
      if(rawT<1)requestAnimationFrame(frame);
      else{{
        const snap=d.points[finalName];
        if(snap){{placeTokenAt(tokenPlayer,snap.x,snap.y);label.textContent=finalName;label.style.left=snap.x+'%';label.style.top=snap.y+'%';label.style.display='block';}}
        doneCallback&&doneCallback();
      }}
    }}
    requestAnimationFrame(frame);
  }}

  function runConfetti(){{
    const canvas=confettiCanvas;
    canvas.width=container.offsetWidth||800;canvas.height=container.offsetHeight||550;
    canvas.classList.add('show');
    const ctx=canvas.getContext('2d');
    const COLORS=['#f1c40f','#2ecc71','#3498db','#e74c3c','#9b59b6','#1abc9c','#e67e22','#ff69b4','#fff'];
    const SHAPES=['rect','circle','star'];
    const particles=Array.from({{length:120}},()=>{{
      const cx=canvas.width/2;
      return {{x:cx+(Math.random()-.5)*40,y:canvas.height*.45,vx:(Math.random()-.5)*9,vy:-(Math.random()*10+4),size:Math.random()*10+4,color:COLORS[Math.floor(Math.random()*COLORS.length)],shape:SHAPES[Math.floor(Math.random()*SHAPES.length)],rotation:Math.random()*360,rotSpeed:(Math.random()-.5)*12,gravity:.28,drag:.98,life:1,decay:Math.random()*.012+.008}};
    }});
    function drawStar(ctx,x,y,r,rot){{ctx.save();ctx.translate(x,y);ctx.rotate(rot*Math.PI/180);ctx.beginPath();for(let i=0;i<5;i++){{const a=((i*72)-90)*Math.PI/180,b=((i*72+36)-90)*Math.PI/180;i===0?ctx.moveTo(Math.cos(a)*r,Math.sin(a)*r):ctx.lineTo(Math.cos(a)*r,Math.sin(a)*r);ctx.lineTo(Math.cos(b)*r*.45,Math.sin(b)*r*.45);}}ctx.closePath();ctx.fill();ctx.restore();}}
    let raf;
    function tick(){{
      ctx.clearRect(0,0,canvas.width,canvas.height);let alive=false;
      particles.forEach(p=>{{
        p.vy+=p.gravity;p.vx*=p.drag;p.vy*=p.drag;p.x+=p.vx;p.y+=p.vy;p.rotation+=p.rotSpeed;p.life-=p.decay;
        if(p.life<=0)return;alive=true;
        ctx.globalAlpha=Math.max(0,p.life);ctx.fillStyle=p.color;
        if(p.shape==='rect'){{ctx.save();ctx.translate(p.x,p.y);ctx.rotate(p.rotation*Math.PI/180);ctx.fillRect(-p.size/2,-p.size/4,p.size,p.size/2);ctx.restore();}}
        else if(p.shape==='circle'){{ctx.beginPath();ctx.arc(p.x,p.y,p.size/2,0,Math.PI*2);ctx.fill();}}
        else{{ctx.save();ctx.fillStyle=p.color;drawStar(ctx,p.x,p.y,p.size/1.5,p.rotation);ctx.restore();}}
      }});
      ctx.globalAlpha=1;
      if(alive)raf=requestAnimationFrame(tick);else{{canvas.classList.remove('show');cancelAnimationFrame(raf);}}
    }}
    raf=requestAnimationFrame(tick);
    setTimeout(()=>{{canvas.classList.remove('show');cancelAnimationFrame(raf);}},2800);
  }}

  function runWrongAnim(){{wrongOverlay.classList.add('show');setTimeout(()=>wrongOverlay.classList.remove('show'),1800);}}
  function runTreasureAnim(onDone){{
    const effect=d.treasureEffect||{{}};
    treasureTxt.textContent=effect.message||'반짝이는 보물을 발견했어요!';
    treasureOverlay.classList.add('show');
    setTimeout(()=>{{treasureOverlay.classList.remove('show');onDone&&onDone();}},1900);
  }}
  function runStreakCelebration(){{
    const effect=d.celebrationEffect||{{}};
    streakMain.textContent=effect.message||'🔥 연속 정답! 대단해요!';
    streakOverlay.classList.add('show');
    runConfetti();
    setTimeout(()=>streakOverlay.classList.remove('show'),1850);
  }}
  function runGhostAnim(onDone){{
    const effect=d.binbouEffect||{{}};
    ghostTxt.textContent=effect.message||'먹보유령 효과 발생!';
    document.getElementById('ghost-emoji').textContent=effect.type==='escaped'?'💨':'👿';
    ghostOverlay.classList.add('show');
    setTimeout(()=>{{ghostOverlay.classList.remove('show');onDone&&onDone();}},2200);
  }}

  function animateGhostToken(pathIndices,doneCallback){{
    if(!pathIndices||pathIndices.length===0){{doneCallback&&doneCallback();return;}}
    tokenBinbou.style.display='flex';
    if(pathIndices.length===1){{
      const pt=d.points[d.stations[pathIndices[0]]];
      if(pt)placeTokenAt(tokenBinbou,pt.x,pt.y);
      doneCallback&&doneCallback();return;
    }}
    const ctrl=buildSpline(pathIndices);
    const curve=sampleSpline(ctrl,Math.max(40,pathIndices.length*16));
    const finalName=d.stations[pathIndices[pathIndices.length-1]];
    const totalMs=Math.min(pathIndices.length*170,1500);
    const t0=performance.now();
    function frame(now){{
      const rawT=Math.min((now-t0)/totalMs,1),eased=easeInOut5(rawT);
      const idx=Math.min(Math.floor(eased*(curve.length-1)),curve.length-1);
      const pt=curve[idx];
      placeTokenAt(tokenBinbou,pt.x,pt.y);
      if(rawT<1)requestAnimationFrame(frame);
      else{{
        const snap=d.points[finalName];
        if(snap)placeTokenAt(tokenBinbou,snap.x,snap.y);
        doneCallback&&doneCallback();
      }}
    }}
    requestAnimationFrame(frame);
  }}

  function showWinOverlay(){{
    if(!d.winner)return;
    winOverlay.classList.add('show');
    document.getElementById('win-details').textContent='총 '+(d.turns||0)+'턴 · '+(d.score||0)+'점 · 목적지 '+(d.destReached||0)+'회';
  }}

  function runGhostSequence(ev,onDone){{
    const chasePath=(ev&&ev.binbou_path_indices)||[];
    const resetPath=(ev&&ev.binbou_reset_path_indices)||[];
    const afterReset=()=>{{onDone&&onDone();}};
    const resetGhost=()=>{{
      if(resetPath.length>0)animateGhostToken(resetPath,afterReset);
      else afterReset();
    }};
    const afterChase=()=>{{
      if(d.binbouEffect)runGhostAnim(resetGhost);
      else resetGhost();
    }};
    if(chasePath.length>0)animateGhostToken(chasePath,afterChase);
    else afterChase();
  }}

  if(d.playSound==='wrong')runWrongAnim();

  function initBoard(){{
    drawDots();
    const ev=d.event,hasMove=ev&&ev.path_indices&&ev.path_indices.length>1;

    // 이동 이벤트가 있으면 유령은 '이동 전 위치'에서 시작합니다.
    const ghostStart=(ev&&Number.isInteger(ev.binbou_start_pos))?ev.binbou_start_pos:d.binbou_pos;
    if(ghostStart>=0){{
      tokenBinbou.style.display='flex';
      const bpt=d.points[d.stations[ghostStart]];
      if(bpt)placeTokenAt(tokenBinbou,bpt.x,bpt.y);
    }}else{{
      tokenBinbou.style.display='none';
    }}

    const finishBoardEffects=()=>{{
      if(d.binbou_pos>=0){{
        tokenBinbou.style.display='flex';
        const finalGhostPt=d.points[d.stations[d.binbou_pos]];
        if(finalGhostPt)placeTokenAt(tokenBinbou,finalGhostPt.x,finalGhostPt.y);
      }}
      showWinOverlay();
    }};
    const runAfterMove=()=>{{
      const afterTreasure=()=>runGhostSequence(ev,finishBoardEffects);
      if(d.treasureEffect)runTreasureAnim(afterTreasure);else afterTreasure();
    }};

    if(hasMove&&ev.dice){{
      const startPt=d.points[d.stations[ev.path_indices[0]]];
      if(startPt)placeTokenAt(tokenPlayer,startPt.x,startPt.y);
      runDiceAnim(ev.dice,()=>{{animateToken(ev.path_indices,runAfterMove);}});
    }}else{{
      const pt=d.points[d.stations[d.position]];
      if(pt){{placeTokenAt(tokenPlayer,pt.x,pt.y);label.textContent=d.stations[d.position];label.style.left=pt.x+'%';label.style.top=pt.y+'%';label.style.display='block';}}
      const hasGhostSequence=ev&&(((ev.binbou_path_indices||[]).length>0)||((ev.binbou_reset_path_indices||[]).length>0));
      if(hasGhostSequence){{
        runGhostSequence(ev,finishBoardEffects);
      }}else{{
        if(d.binbou_pos>=0){{
          tokenBinbou.style.display='flex';
          const bpt=d.points[d.stations[d.binbou_pos]];
          if(bpt)placeTokenAt(tokenBinbou,bpt.x,bpt.y);
        }}
        if(d.binbouEffect)runGhostAnim(showWinOverlay);else showWinOverlay();
      }}
      if(d.treasureEffect)runTreasureAnim();
    }}
    if(d.celebrationEffect)runStreakCelebration();
    const logEl=document.getElementById('event-log');
    (d.eventLog||[]).slice().reverse().forEach(msg=>{{const div=document.createElement('div');div.className='log-item';div.textContent=msg;logEl.appendChild(div);}});
    if(d.soundEnabled&&d.playSound){{
      try{{
        const actx=new(window.AudioContext||window.webkitAudioContext)();
        function beep(f,dur,type='sine',vol=0.25){{const o=actx.createOscillator(),g=actx.createGain();o.connect(g);g.connect(actx.destination);o.type=type;o.frequency.value=f;g.gain.setValueAtTime(vol,actx.currentTime);g.gain.exponentialRampToValueAtTime(.001,actx.currentTime+dur);o.start();o.stop(actx.currentTime+dur);}}
        if(d.playSound==='dice'){{beep(440,.1);setTimeout(()=>beep(660,.1),100);}}
        if(d.playSound==='correct'){{beep(523,.1);setTimeout(()=>beep(659,.1),100);setTimeout(()=>beep(784,.25),200);}}
        if(d.playSound==='streak'){{[523,659,784,988].forEach((f,i)=>setTimeout(()=>beep(f,.16,'sine',.22),i*90));}}
        if(d.playSound==='wrong'){{beep(180,.35,'sawtooth',.2);}}
        if(d.playSound==='ghost'){{beep(150,.18,'sawtooth',.25);setTimeout(()=>beep(95,.45,'square',.2),140);}}
        if(d.playSound==='escape'){{[392,523,659,784].forEach((f,i)=>setTimeout(()=>beep(f,.14,'sine',.2),i*80));}}
        if(d.playSound==='treasure'){{[659,784,988].forEach((f,i)=>setTimeout(()=>beep(f,.14,'triangle',.2),i*100));}}
        if(d.playSound==='win'){{[523,659,784,1047].forEach((f,i)=>setTimeout(()=>beep(f,.3),i*150));}}
      }}catch(e){{}}
    }}
  }}

  // 이미지 로드 후 보드 초기화
  boardImg.src=d.image;
  if(boardImg.complete){{initBoard();}}
  else{{boardImg.onload=initBoard;boardImg.onerror=()=>{{console.error('이미지 로드 실패');initBoard();}};}}
}})();
</script>
</body></html>"""

    st.session_state.play_sound        = None
    st.session_state.animation_event   = None
    st.session_state.binbou_effect     = None
    st.session_state.treasure_effect   = None
    st.session_state.celebration_event = None
    components.html(html, height=820, scrolling=False)


# ═══════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🚃 지하철 2호선 게임")
    st.caption("서울 2호선 · 1인용 · 성수 → 건대입구")

    st.session_state.player_name = st.text_input(
        "플레이어 이름",
        value=st.session_state.get("player_name", "플레이어"),
        key="name_input"
    )

    st.subheader("🚄 내 열차 선택")
    train_keys = list(TRAIN_TYPES.keys())
    if "train_selector" not in st.session_state or st.session_state.train_selector not in train_keys:
        st.session_state.train_selector = st.session_state.get("selected_train", "KTX")
    current_phase_for_train = st.session_state.get("game_phase", "start")
    chosen_train = st.radio(
        "함께 달릴 열차를 골라 주세요!",
        train_keys,
        key="train_selector",
        horizontal=True,
        format_func=lambda key: f"{TRAIN_TYPES[key]['emoji']} {key}",
        disabled=current_phase_for_train not in ("start", "game_over"),
    )
    st.session_state.selected_train = chosen_train

    st.markdown("---")
    st.subheader("📚 퀴즈 카테고리")
    all_cats = QUIZ_CATEGORIES
    if "selected_categories" not in st.session_state:
        st.session_state.selected_categories = all_cats[:]
    else:
        # 이전 버전 세션에 남아 있을 수 있는 더 이상 지원하지 않는 카테고리를 제거합니다.
        st.session_state.selected_categories = [
            c for c in st.session_state.selected_categories if c in all_cats
        ]
    for cat in all_cats:
        checked = cat in st.session_state.selected_categories
        if st.checkbox(cat, value=checked, key=f"cat_{cat}"):
            if cat not in st.session_state.selected_categories:
                st.session_state.selected_categories.append(cat)
        else:
            if cat in st.session_state.selected_categories:
                st.session_state.selected_categories.remove(cat)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎮 시작", use_container_width=True, type="primary"):
            start_game(); st.rerun()
    with col2:
        if st.button("🔄 리셋", use_container_width=True):
            init_game(keep_name=True); st.rerun()

    st.markdown("---")
    phase = st.session_state.game_phase

    hand = st.session_state.hand_items
    if hand:
        st.subheader("🃏 보유 아이템")
        for item_slot, item_key in enumerate(list(hand)):
            item = ITEMS[item_key]
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.caption(f"{item['name']}\n{item['desc']}")
            with col_b:
                if item_key == "skip_penalty":
                    st.caption("오답 시 자동 사용")
                    can_use = False
                elif item_key == "double_move":
                    can_use = phase == "ready_to_roll" and st.session_state.active_item is None
                elif item_key == "shield":
                    can_use = phase == "ready_to_roll" and not st.session_state.shield_active
                elif item_key == "score_up":
                    can_use = phase == "answering_quiz" and not st.session_state.score_x2
                else:
                    can_use = False

                if item_key != "skip_penalty":
                    if st.button(
                        "사용",
                        key=f"use_{item_slot}_{item_key}_{st.session_state.quiz_key}",
                        use_container_width=True,
                        disabled=not can_use,
                    ):
                        if item_key == "double_move":
                            st.session_state.active_item = "double_move"
                            st.session_state.hand_items.remove(item_key)
                            add_event_log("🚄 2배 이동 카드 준비!")
                        elif item_key == "shield":
                            st.session_state.shield_active = True
                            st.session_state.hand_items.remove(item_key)
                            add_event_log("🛡️ 방어 카드 준비!")
                        elif item_key == "score_up":
                            st.session_state.score_x2 = True
                            st.session_state.hand_items.remove(item_key)
                            add_event_log("💎 점수 2배 카드 준비!")
                        st.rerun()
        st.markdown("---")

    if phase == "ready_to_roll":
        st.subheader("🎲 주사위")
        streak = st.session_state.correct_streak
        if streak >= 3:
            st.success(f"🔥 연속 {streak}정답! 보너스 확률!")
        if st.session_state.active_item == "double_move":
            st.warning("🚄 2배 이동 활성화!")
        if st.session_state.bonus_dice > 0:
            st.info(f"⚡ 주사위 보너스 +{st.session_state.bonus_dice}")
        if st.button("🎲 주사위 굴리기!", use_container_width=True, type="primary"):
            move_forward(); st.rerun()

    elif phase == "ghost_minigame":
        game = st.session_state.get("ghost_game")
        st.subheader("👿 먹보유령 탈출 미니게임")
        st.warning("🚪 세 문 중 하나를 골라 주세요! 두 문은 안전하고, 한 문에만 먹보유령이 숨어 있어요.")
        if game:
            door_cols = st.columns(3)
            for door_idx, col in enumerate(door_cols):
                with col:
                    if st.button(
                        f"🚪 {door_idx + 1}번 문",
                        key=f"ghost_door_{game['id']}_{door_idx}",
                        use_container_width=True,
                        type="primary",
                    ):
                        resolve_ghost_minigame(door_idx)
                        st.rerun()
        st.caption("성공하면 감점 없이 탈출하고 먹보유령이 8칸 뒤로 물러납니다!")

    elif phase == "waiting_penalty_roll":
        st.subheader("😱 뒤로 가기 주사위")
        if "skip_penalty" in st.session_state.hand_items:
            st.success("✨ 면제 카드 보유! 자동 면제됩니다.")
        else:
            st.error("오답! 뒤로 가기 주사위 (최대 4칸 후퇴)")
        if st.button("🎲 뒤로 가기 주사위", use_container_width=True):
            move_backward(); st.rerun()

    elif phase == "answering_quiz":
        quiz = st.session_state.current_quiz
        if quiz:
            remaining = len(st.session_state.quiz_queue)
            title = "📝 퀴즈"
            if remaining > 0:
                title += f" (이후 {remaining}문제 더!)"
            st.subheader(title)
            if st.session_state.score_x2:
                st.warning("💎 점수 2배 활성화! 정답 시 20점!")
            cat_colors = {"국어": "🟢", "상식": "🟡", "과학": "🟠", "영어": "🔴", "수수께끼": "🟣"}
            icon = cat_colors.get(quiz['category'], '⚪')
            st.info(f"{icon} [{quiz['category']}]\n\n**{quiz['question']}**")
            for opt_idx, opt in enumerate(quiz["options"]):
                if st.button(opt, key=f"opt_{quiz['quiz_id']}_{opt_idx}_{st.session_state.quiz_key}", use_container_width=True):
                    submit_answer(opt); st.rerun()

    elif phase == "game_over":
        st.balloons()
        st.success("🎉 건대입구 도착! 게임 클리어!")
        st.metric("최종 점수",   st.session_state.score)
        st.metric("총 턴 수",    st.session_state.turns)
        st.metric("목적지 도달", f"{st.session_state.dest_reached}회")
        if st.button("🔄 다시 하기", use_container_width=True, type="primary"):
            init_game(keep_name=True); st.rerun()

    elif phase == "start":
        st.info("🎮 이름 입력 후 **시작** 버튼을 눌러 주세요!")
        st.markdown("""
**게임 방법**
- 🎲 주사위를 굴려 역 이동
- 📝 도착 역에서 퀴즈 풀기
- 🎯 목적지 카드 달성 시 +50점
- 👿 먹보유령에게 잡히면 3문 탈출 미니게임 도전
- 🎁 주황색 보물상자 칸에서 특별 보상 획득
- 🔥 3연속 이상 정답이면 축하 특수 효과 등장
- 🃏 아이템 카드를 전략적으로 활용!
- 🏁 건대입구역 도달이 목표!
""")

    st.markdown("---")
    if phase not in ("start",):
        pos   = st.session_state.position
        total = len(STATIONS)
        st.progress(pos / (total - 1) if total > 1 else 0)
        st.caption(f"📍 **{STATIONS[pos]}** ({pos+1}/{total})")
        st.caption(f"🎯 목적지: **{st.session_state.destination}**")

    with st.expander("🗺️ 칸 종류 설명"):
        st.caption("🔵 **파란 칸** — 보너스 (추가 주사위·점수·아이템)")
        st.caption("🔴 **빨간 칸** — 패널티 (후퇴·점수 감소·먹보유령)")
        st.caption("⭐ **별 칸** — 목적지 카드 (도달 시 +50점)")
        st.caption("💜 **함정 칸** — 먹보유령 소환! 탈출 미니게임에 도전")
        st.caption("🟠 **보물상자 칸** — 점수·아이템·주사위 보너스 등 특별 보상")
        st.caption("🟢 **도착 칸** — 건대입구 (최종 목표)")


# ═══════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════
st.markdown(
    "<h2 style='margin-bottom:4px'>🚃 지하철 2호선 게임 — 서울 2호선</h2>"
    "<p style='color:#aaa;font-size:13px;margin-bottom:8px'>성수역 출발 → 건대입구역 도착 🏁</p>",
    unsafe_allow_html=True
)

msg   = st.session_state.last_message
phase = st.session_state.game_phase
if phase == "game_over":
    st.success(msg)
elif phase == "answering_quiz":
    st.warning(msg)
elif phase in ("waiting_penalty_roll", "ghost_minigame"):
    st.error(msg)
else:
    st.info(msg)

map_bytes, is_jpg = get_map_bytes()
render_board(map_bytes, is_jpg)
