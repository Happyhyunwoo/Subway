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

SQUARE_TYPES = {
    "홍대입구": "blue",  "강남": "blue",  "왕십리": "blue",
    "선릉":     "blue",  "시청": "blue",  "이대":   "blue",
    "신도림":   "red",   "사당": "red",   "동대문역사문화공원": "red",
    "구로디지털단지": "red",
    "을지로3가": "star", "잠실": "star",  "교대":   "star",
    "합정":     "star",  "성수": "star",
    "신림":     "trap",  "구의": "trap",
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

TRAP_EVENTS = [
    {"msg": "👿 먹보유령 등장! 붙잡혔습니다! 점수 -20점!", "score": -20, "binbou_attach": True},
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
    # ══════════════ 국어 (20문제) ══════════════
    {'category': '국어', 'question': "'봄, 여름, 가을' 다음 계절은 무엇일까요?",
     'options': ['봄', '여름', '겨울', '치킨'], 'answer': 2},
    {'category': '국어', 'question': '다음 중 과일 이름은 무엇일까요?',
     'options': ['바나나', '의자', '신발', '연필'], 'answer': 0},
    {'category': '국어', 'question': "'빠르다'와 비슷한 말은 무엇일까요?",
     'options': ['느리다', '무겁다', '신속하다', '뽀글뽀글'], 'answer': 2},
    {'category': '국어', 'question': '다음 중 탈것(이동수단) 이름은 무엇일까요?',
     'options': ['사자', '버스', '사과', '구름'], 'answer': 1},
    {'category': '국어', 'question': "'뜨겁다'의 반대말은 무엇일까요?",
     'options': ['차갑다', '무겁다', '높다', '맛있다'], 'answer': 0},
    {'category': '국어', 'question': "'웃다'와 반대 뜻의 말은 무엇일까요?",
     'options': ['달리다', '울다', '먹다', '방귀'], 'answer': 1},
    {'category': '국어', 'question': '다음 중 날씨를 나타내는 말은 무엇일까요?',
     'options': ['맑다', '자동차', '우유', '공책'], 'answer': 0},
    {'category': '국어', 'question': "'ㄱ, ㄴ, ㄷ' 다음 자음은 무엇일까요?",
     'options': ['ㅁ', 'ㄹ', 'ㅂ', 'ㅎ'], 'answer': 1},
    {'category': '국어', 'question': '다음 중 채소 이름은 무엇일까요?',
     'options': ['당근', '비행기', '지우개', '슬리퍼'], 'answer': 0},
    {'category': '국어', 'question': "'높다'의 반대말은 무엇일까요?",
     'options': ['멀다', '깊다', '낮다', '엉덩이'], 'answer': 2},
    {'category': '국어', 'question': '다음 중 가족을 부르는 말이 아닌 것은?',
     'options': ['엄마', '아빠', '할머니', '냉장고'], 'answer': 3},
    {'category': '국어', 'question': "'크다'와 반대 뜻의 말은 무엇일까요?",
     'options': ['작다', '길다', '넓다', '둥글다'], 'answer': 0},
    {'category': '국어', 'question': '다음 중 동물을 나타내는 말은 무엇일까요?',
     'options': ['토끼', '책상', '우산', '시계'], 'answer': 0},
    {'category': '국어', 'question': "'기쁘다'와 비슷한 뜻의 말은 무엇일까요?",
     'options': ['즐겁다', '춥다', '어둡다', '느리다'], 'answer': 0},
    {'category': '국어', 'question': '다음 중 장소를 나타내는 말은 무엇일까요?',
     'options': ['학교', '달리다', '예쁘다', '빨리'], 'answer': 0},
    {'category': '국어', 'question': "'사과를 먹었다.'에서 먹은 것은 무엇일까요?",
     'options': ['사과', '학교', '버스', '모자'], 'answer': 0},
    {'category': '국어', 'question': '다음 중 받침이 있는 글자는 무엇일까요?',
     'options': ['가', '나', '달', '오'], 'answer': 2},
    {'category': '국어', 'question': "'강아지가 멍멍 짖어요.'에서 동물은 무엇일까요?",
     'options': ['강아지', '멍멍', '짖어요', '구름'], 'answer': 0},
    {'category': '국어', 'question': '다음 중 문장을 끝낼 때 자주 쓰는 문장 부호는 무엇일까요?',
     'options': ['마침표(.)', '괄호(', '별표(*)', '더하기(+)'], 'answer': 0},
    {'category': '국어', 'question': "'위'의 반대말은 무엇일까요?",
     'options': ['아래', '옆', '앞', '밖'], 'answer': 0},

    # ══════════════ 상식 (20문제) ══════════════
    {'category': '상식', 'question': '1년은 몇 개월일까요?',
     'options': ['10개월', '11개월', '12개월', '13개월'], 'answer': 2},
    {'category': '상식', 'question': '무지개는 몇 가지 색으로 이루어져 있을까요?',
     'options': ['5가지', '6가지', '7가지', '100가지'], 'answer': 2},
    {'category': '상식', 'question': '병원에서 일하며 아픈 사람을 진료하는 사람은?',
     'options': ['소방관', '의사', '요리사', '우주인'], 'answer': 1},
    {'category': '상식', 'question': '쓰레기는 어디에 버려야 할까요?',
     'options': ['바닥', '강', '쓰레기통', '친구 가방'], 'answer': 2},
    {'category': '상식', 'question': '횡단보도를 건널 때 초록불이면 어떻게 해야 할까요?',
     'options': ['뛰어서 건넌다', '좌우를 살피고 건넌다', '그냥 앉아 있는다', '눈 감고 건넌다'], 'answer': 1},
    {'category': '상식', 'question': '우리나라 국기의 이름은 무엇일까요?',
     'options': ['성조기', '태극기', '오륜기', '무지개기'], 'answer': 1},
    {'category': '상식', 'question': '하루는 몇 시간일까요?',
     'options': ['12시간', '20시간', '24시간', '100시간'], 'answer': 2},
    {'category': '상식', 'question': '음식을 먹기 전에 해야 할 일은 무엇일까요?',
     'options': ['손 씻기', '노래 부르기', '점프하기', '숙제하기'], 'answer': 0},
    {'category': '상식', 'question': '도서관에서 지켜야 할 규칙은 무엇일까요?',
     'options': ['큰 소리로 노래한다', '조용히 한다', '뛰어다닌다', '라면을 끓여 먹는다'], 'answer': 1},
    {'category': '상식', 'question': '지구에서 가장 큰 바다는 무엇일까요?',
     'options': ['대서양', '인도양', '태평양', '목욕탕'], 'answer': 2},
    {'category': '상식', 'question': '서울 2호선 지하철의 대표 색깔은 무엇일까요?',
     'options': ['파란색', '초록색', '빨간색', '무지개색'], 'answer': 1},
    {'category': '상식', 'question': '감기에 걸렸을 때 진료를 받으러 가는 곳은?',
     'options': ['놀이공원', '수영장', '병원', '치킨집'], 'answer': 2},
    {'category': '상식', 'question': '불이 났을 때 도움을 요청하는 긴급 전화번호는 무엇일까요?',
     'options': ['112', '119', '120', '123'], 'answer': 1},
    {'category': '상식', 'question': '길을 잃었을 때 가장 안전한 행동은 무엇일까요?',
     'options': ['혼자 멀리 간다', '안전한 곳에서 경찰이나 직원에게 도움을 요청한다', '아무 차나 탄다', '숨는다'], 'answer': 1},
    {'category': '상식', 'question': '비가 많이 오는 날 밖에 나갈 때 필요한 것은 무엇일까요?',
     'options': ['우산', '선글라스만', '수영모', '베개'], 'answer': 0},
    {'category': '상식', 'question': '버스나 지하철에서 지켜야 할 예절로 알맞은 것은?',
     'options': ['큰 소리로 소리친다', '차례를 지켜 타고 내린다', '좌석 위에 선다', '문을 막는다'], 'answer': 1},
    {'category': '상식', 'question': '우리나라의 수도는 어디일까요?',
     'options': ['서울', '부산', '제주', '도쿄'], 'answer': 0},
    {'category': '상식', 'question': '양치질은 무엇을 깨끗하게 하기 위해 할까요?',
     'options': ['신발', '치아', '가방', '모자'], 'answer': 1},
    {'category': '상식', 'question': '겨울에 몸을 따뜻하게 하기 좋은 옷은 무엇일까요?',
     'options': ['두꺼운 외투', '수영복', '반팔 한 장', '슬리퍼만'], 'answer': 0},
    {'category': '상식', 'question': '신호등의 빨간불은 보통 무엇을 뜻할까요?',
     'options': ['멈춤', '출발', '춤추기', '달리기'], 'answer': 0},

    # ══════════════ 과학 (20문제) ══════════════
    {'category': '과학', 'question': '물이 얼면 무엇이 될까요?',
     'options': ['수증기', '얼음', '구름', '슬러시'], 'answer': 1},
    {'category': '과학', 'question': '낮과 밤이 생기는 가장 큰 이유는 무엇일까요?',
     'options': ['해가 자서', '지구가 자전해서', '달이 항상 해를 가려서', '구름 때문에'], 'answer': 1},
    {'category': '과학', 'question': '식물이 초록색으로 보이는 것과 가장 관련 있는 것은?',
     'options': ['물', '엽록소', '흙', '바람'], 'answer': 1},
    {'category': '과학', 'question': '물고기는 주로 무엇으로 숨을 쉴까요?',
     'options': ['코', '아가미', '날개', '귀'], 'answer': 1},
    {'category': '과학', 'question': '다음 중 곤충이 아닌 것은 무엇일까요?',
     'options': ['나비', '개미', '거미', '잠자리'], 'answer': 2},
    {'category': '과학', 'question': '달이 지구 주위를 한 바퀴 도는 데 걸리는 시간은 대략 얼마일까요?',
     'options': ['하루', '약 한 달', '약 일 년', '10년'], 'answer': 1},
    {'category': '과학', 'question': '다음 중 보통 가장 가벼운 것은?',
     'options': ['쇠공', '돌멩이', '솜뭉치', '벽돌'], 'answer': 2},
    {'category': '과학', 'question': '씨앗이 싹을 틔울 때 보통 먼저 나오는 부분은?',
     'options': ['꽃', '뿌리', '열매', '나무껍질'], 'answer': 1},
    {'category': '과학', 'question': '비가 오기 전 하늘에서 자주 볼 수 있는 것은?',
     'options': ['먹구름', '별똥별', '오로라', '달무지개만'], 'answer': 0},
    {'category': '과학', 'question': '우리 몸에서 피를 온몸으로 보내는 기관은?',
     'options': ['위', '폐', '심장', '콩팥'], 'answer': 2},
    {'category': '과학', 'question': '다음 중 포유류는 무엇일까요?',
     'options': ['독수리', '개구리', '고래', '뱀'], 'answer': 2},
    {'category': '과학', 'question': '소리는 무엇 같은 물질을 통해 전달될 수 있을까요?',
     'options': ['공기', '그림자', '생각', '숫자'], 'answer': 0},
    {'category': '과학', 'question': '태양은 무엇일까요?',
     'options': ['별', '행성', '위성', '구름'], 'answer': 0},
    {'category': '과학', 'question': '얼음이 따뜻해져 녹으면 무엇이 될까요?',
     'options': ['물', '돌', '나무', '모래'], 'answer': 0},
    {'category': '과학', 'question': '사람이 숨을 쉴 때 꼭 필요한 기체는 무엇일까요?',
     'options': ['산소', '초콜릿', '모래', '소금'], 'answer': 0},
    {'category': '과학', 'question': '자석에 잘 붙는 물질은 무엇일까요?',
     'options': ['철', '종이', '고무', '나무'], 'answer': 0},
    {'category': '과학', 'question': '식물이 자라는 데 도움이 되는 것은 무엇일까요?',
     'options': ['햇빛과 물', '플라스틱만', '소리만', '연필'], 'answer': 0},
    {'category': '과학', 'question': '우리 몸에서 숨을 쉬는 데 중요한 기관은 무엇일까요?',
     'options': ['폐', '발', '손톱', '머리카락'], 'answer': 0},
    {'category': '과학', 'question': '개구리는 어릴 때 무엇이라고 부를까요?',
     'options': ['올챙이', '송아지', '병아리', '애벌레'], 'answer': 0},
    {'category': '과학', 'question': '지구가 태양 주위를 도는 것을 무엇이라고 할까요?',
     'options': ['공전', '정지', '점프', '증발'], 'answer': 0},

    # ══════════════ 영어 (20문제) ══════════════
    {'category': '영어', 'question': "'red'는 무슨 색일까요?",
     'options': ['파랑', '노랑', '빨강', '투명'], 'answer': 2},
    {'category': '영어', 'question': "'banana'는 무엇일까요?",
     'options': ['사과', '바나나', '포도', '바나나우유'], 'answer': 1},
    {'category': '영어', 'question': "'school'은 어디일까요?",
     'options': ['집', '병원', '학교', '공원'], 'answer': 2},
    {'category': '영어', 'question': "'happy'는 무슨 뜻일까요?",
     'options': ['슬프다', '행복하다', '배고프다', '졸리다'], 'answer': 1},
    {'category': '영어', 'question': "'book'은 무엇일까요?",
     'options': ['책', '공책', '연필', '북극'], 'answer': 0},
    {'category': '영어', 'question': "'elephant'는 어떤 동물일까요?",
     'options': ['사자', '기린', '코끼리', '토끼'], 'answer': 2},
    {'category': '영어', 'question': "'run'은 무슨 뜻일까요?",
     'options': ['자다', '먹다', '달리다', '읽다'], 'answer': 2},
    {'category': '영어', 'question': "'cold'는 무슨 뜻일까요?",
     'options': ['뜨겁다', '춥다·차갑다', '달다', '밝다'], 'answer': 1},
    {'category': '영어', 'question': "'friend'는 무슨 뜻일까요?",
     'options': ['적', '친구', '가족', '선생님'], 'answer': 1},
    {'category': '영어', 'question': "'big'과 반대 뜻의 영어 단어는?",
     'options': ['tall', 'fast', 'small', 'pig'], 'answer': 2},
    {'category': '영어', 'question': "'rainbow'는 무엇일까요?",
     'options': ['구름', '번개', '무지개', '우산'], 'answer': 2},
    {'category': '영어', 'question': "'1, 2, 3'을 영어로 세면?",
     'options': ['one, two, three', 'uno, dos, tres', 'ichi, ni, san', 'han, dul, set'], 'answer': 0},
    {'category': '영어', 'question': "'dog'는 어떤 동물일까요?",
     'options': ['개', '고양이', '새', '물고기'], 'answer': 0},
    {'category': '영어', 'question': "'water'는 무엇일까요?",
     'options': ['물', '불', '바람', '흙'], 'answer': 0},
    {'category': '영어', 'question': "'green'은 무슨 색일까요?",
     'options': ['초록색', '보라색', '검은색', '하얀색'], 'answer': 0},
    {'category': '영어', 'question': "'thank you'는 어떤 뜻일까요?",
     'options': ['고마워요', '미안해요', '안녕히 주무세요', '배고파요'], 'answer': 0},
    {'category': '영어', 'question': "'cat'은 무엇일까요?",
     'options': ['고양이', '자동차', '모자', '컵'], 'answer': 0},
    {'category': '영어', 'question': "'apple'은 무엇일까요?",
     'options': ['사과', '딸기', '수박', '복숭아'], 'answer': 0},
    {'category': '영어', 'question': "'good morning'은 언제 주로 하는 인사일까요?",
     'options': ['아침', '한밤중', '식사 중에만', '비가 올 때만'], 'answer': 0},
    {'category': '영어', 'question': "'sit down'은 무슨 뜻일까요?",
     'options': ['앉으세요', '달리세요', '노래하세요', '문을 여세요'], 'answer': 0},

    # ══════════════ 수수께끼 (20문제) ══════════════
    {'category': '수수께끼', 'question': '먹을수록 커지고 물을 마실수록 작아지는 것은 무엇일까요?',
     'options': ['불', '구름', '나무', '풍선'], 'answer': 0},
    {'category': '수수께끼', 'question': '문은 문인데 사람이 드나들 수 없는 문은 무엇일까요?',
     'options': ['대문', '창문', '소문', '정문'], 'answer': 2},
    {'category': '수수께끼', 'question': '다리는 네 개지만 걸을 수 없는 것은 무엇일까요?',
     'options': ['강아지', '책상', '고양이', '사자'], 'answer': 1},
    {'category': '수수께끼', 'question': '이빨은 많지만 음식을 먹지 못하는 것은 무엇일까요?',
     'options': ['상어', '빗', '악어', '호랑이'], 'answer': 1},
    {'category': '수수께끼', 'question': '목은 있지만 머리가 없는 것은 무엇일까요?',
     'options': ['병', '기린', '사람', '거북이'], 'answer': 0},
    {'category': '수수께끼', 'question': '눈이 하나 있지만 볼 수 없는 것은 무엇일까요?',
     'options': ['외눈박이', '바늘', '망원경', '카메라'], 'answer': 1},
    {'category': '수수께끼', 'question': '손은 있지만 박수를 칠 수 없는 것은 무엇일까요?',
     'options': ['인형', '시계', '로봇', '장갑'], 'answer': 1},
    {'category': '수수께끼', 'question': '비가 올 때 활짝 펴지는 꽃은 무엇일까요?',
     'options': ['장미', '민들레', '우산', '해바라기'], 'answer': 2},
    {'category': '수수께끼', 'question': '항상 나를 따라오지만 잡을 수 없는 것은 무엇일까요?',
     'options': ['그림자', '강아지', '친구', '바람개비'], 'answer': 0},
    {'category': '수수께끼', 'question': '말하면 사라져 버리는 것은 무엇일까요?',
     'options': ['노래', '비밀', '메아리', '웃음'], 'answer': 1},
    {'category': '수수께끼', 'question': '글씨를 지울수록 점점 작아지는 것은 무엇일까요?',
     'options': ['연필', '공책', '지우개', '책상'], 'answer': 2},
    {'category': '수수께끼', 'question': '한 번 지나가면 다시 돌아오지 않는 것은 무엇일까요?',
     'options': ['시간', '기차', '공', '자동차'], 'answer': 0},
    {'category': '수수께끼', 'question': '많아질수록 앞이 잘 보이지 않는 것은 무엇일까요?',
     'options': ['햇빛', '어둠', '안경', '창문'], 'answer': 1},
    {'category': '수수께끼', 'question': '땅에서 태어나 하늘로 올라가 사라지는 것은 무엇일까요?',
     'options': ['연기', '돌', '나무', '강'], 'answer': 0},
    {'category': '수수께끼', 'question': '얼굴과 두 손은 있지만 입과 발이 없는 것은 무엇일까요?',
     'options': ['인형', '시계', '사진', '로봇'], 'answer': 1},
    {'category': '수수께끼', 'question': '아침에는 길고 한낮에는 짧아지는 것은 무엇일까요?',
     'options': ['그림자', '연필', '기차', '신발'], 'answer': 0},
    {'category': '수수께끼', 'question': '계속 돌지만 제자리에서 떠나지 않는 것은 무엇일까요?',
     'options': ['선풍기 날개', '자동차', '비행기', '강아지'], 'answer': 0},
    {'category': '수수께끼', 'question': '물을 먹으면 죽고, 나무를 먹으면 사는 것은 무엇일까요?',
     'options': ['불', '물고기', '구름', '얼음'], 'answer': 0},
    {'category': '수수께끼', 'question': '집은 집인데 사람이 살지 않고 책이 많이 사는 집은 무엇일까요?',
     'options': ['도서관', '아파트', '텐트', '놀이터'], 'answer': 0},
    {'category': '수수께끼', 'question': '발은 없지만 계속 흐르는 것은 무엇일까요?',
     'options': ['강물', '의자', '모자', '공책'], 'answer': 0},
]


# ═
#  게임 상태 초기화
# ═══════════════════════════════════════════════════
def init_game(keep_name=True):
    old_name = st.session_state.get("player_name", "플레이어")
    st.session_state.player_name       = old_name if keep_name else "플레이어"
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


if "position" not in st.session_state:
    init_game(keep_name=False)


def start_game():
    name = st.session_state.get("player_name", "플레이어")
    init_game(keep_name=True)
    st.session_state.player_name  = name
    st.session_state.game_phase   = "ready_to_roll"
    st.session_state.last_message = (
        f"🚃 {name}님, 출발! {GOAL_STATION}역을 향해 달립니다!\n"
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


def reset_binbou_after_catch():
    """붙잡힘 효과가 끝난 뒤 유령을 플레이어보다 6칸 뒤로 보냅니다."""
    st.session_state.binbou_pos = max(
        -8,
        st.session_state.position - BINBOU_RESET_DISTANCE,
    )
    st.session_state.binbou_attached = False


def move_binbou(steps):
    bp = st.session_state.binbou_pos + steps
    st.session_state.binbou_pos = max(-8, min(bp, GOAL_INDEX))
    # 실제 감점과 재배치는 resolve_binbou_contact()에서 한 번만 처리합니다.
    return sync_binbou_attachment(log_change=False)


def show_binbou_effect(message, penalty, effect_type="caught"):
    """먹보유령 효과를 점수, 로그, 보드 오버레이에 동시에 반영합니다."""
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


def resolve_binbou_contact(was_attached=False, trap_penalty_already_applied=False):
    """접촉 효과를 한 번 적용한 뒤 유령을 6칸 뒤에서 다시 출발시킵니다."""
    now_attached = sync_binbou_attachment(log_change=False)
    if not now_attached:
        # 이전 버전의 세션에 부착 상태가 남아 있더라도 지속시키지 않습니다.
        st.session_state.binbou_attached = False
        return None

    # 함정 칸의 -20점이 이미 적용된 경우에는 추가 감점을 하지 않습니다.
    if trap_penalty_already_applied:
        penalty = 0
        message = (
            "👿 먹보유령에게 붙잡혔습니다! 점수 -20점! "
            "먹보유령은 6칸 뒤에서 다시 따라옵니다."
        )
    else:
        penalty = 10
        message = (
            "👿 먹보유령에게 붙잡혔습니다! 점수 -10점! "
            "먹보유령은 6칸 뒤에서 다시 따라옵니다."
        )

    show_binbou_effect(message, penalty, "caught")
    reset_binbou_after_catch()
    return message


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
    trap_penalty_applied = False

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

    elif sq == "trap":
        ev = random.choice(TRAP_EVENTS)
        messages.append(ev["msg"])
        if ev.get("score"):
            st.session_state.score = max(0, st.session_state.score + ev["score"])
            trap_penalty_applied = True
        if ev.get("binbou_attach"):
            # 미등장 상태에서도 플레이어 위치에 유령을 즉시 소환합니다.
            st.session_state.binbou_pos = st.session_state.position
            sync_binbou_attachment(log_change=False)

    return "\n\n".join(messages) if messages else None, double_quiz, trap_penalty_applied


def move_forward():
    if st.session_state.game_phase != "ready_to_roll":
        return

    old_pos = st.session_state.position

    # 이전 실행에서 남은 부착 상태는 다음 턴으로 지속하지 않습니다.
    if st.session_state.binbou_attached:
        reset_binbou_after_catch()
    old_binbou_pos = st.session_state.binbou_pos

    dice = roll_dice_value(use_item=st.session_state.active_item == "double_move")
    landing_pos = min(old_pos + dice, GOAL_INDEX)

    st.session_state.binbou_effect = None
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
    ev_msg, double_quiz, trap_penalty_applied = apply_square_event(landing_station, landing_pos)

    # 칸 이벤트까지 적용된 시점의 유령 위치를 저장합니다.
    # 접촉이 일어나면 resolve_binbou_contact()가 이후 6칸 뒤로 재배치합니다.
    binbou_before_contact = st.session_state.binbou_pos
    contact_msg = resolve_binbou_contact(
        False,
        trap_penalty_already_applied=trap_penalty_applied,
    )

    final_pos = st.session_state.position
    final_station = STATIONS[final_pos]
    final_binbou_pos = st.session_state.binbou_pos

    # 플레이어 애니메이션 경로
    path_indices = build_path(old_pos, landing_pos)
    if final_pos != landing_pos:
        path_indices.extend(build_path(landing_pos, final_pos)[1:])

    # 먹보유령 애니메이션 경로: 이전 위치 → 추격/접촉 위치 → (잡았으면) 6칸 뒤 재배치
    binbou_path_indices = []
    if old_binbou_pos >= 0 and binbou_before_contact >= 0:
        binbou_path_indices = build_path(old_binbou_pos, binbou_before_contact)
    elif old_binbou_pos < 0 and binbou_before_contact >= 0:
        binbou_path_indices = [binbou_before_contact]

    binbou_reset_path_indices = []
    if (
        binbou_before_contact >= 0
        and final_binbou_pos >= 0
        and final_binbou_pos != binbou_before_contact
    ):
        binbou_reset_path_indices = build_path(binbou_before_contact, final_binbou_pos)

    did_win = final_pos >= GOAL_INDEX
    st.session_state.animation_event = {
        "position": final_pos,
        "binbou_pos": final_binbou_pos,
        "binbou_start_pos": old_binbou_pos,
        "binbou_path_indices": binbou_path_indices,
        "binbou_reset_path_indices": binbou_reset_path_indices,
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
    if contact_msg and (not ev_msg or contact_msg not in ev_msg):
        base_msg += f"\n\n{contact_msg}"
    if final_pos != landing_pos:
        base_msg += f"\n\n📌 현재 위치: **{final_station}**역"

    # 승리 판정은 칸 이벤트와 먹보유령 접촉 처리가 모두 끝난 뒤 수행합니다.
    if did_win:
        st.session_state.play_sound = "win"
        st.session_state.game_phase = "game_over"
        st.session_state.winner = True
        st.session_state.current_quiz = None
        st.session_state.quiz_queue = []
        st.session_state.last_message = (
            f"🎉 {st.session_state.player_name}님이 {GOAL_STATION}역에 도착했습니다!\n"
            f"총 {st.session_state.turns}턴 · 최종 점수: {st.session_state.score}점\n"
            f"목적지 도달: {st.session_state.dest_reached}회"
        )
        return

    if st.session_state.binbou_effect is None:
        st.session_state.play_sound = "dice"

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


def move_backward():
    if st.session_state.game_phase != "waiting_penalty_roll":
        return

    # 오답으로 중단된 연속 퀴즈와 추가 주사위는 다음 턴으로 넘기지 않습니다.
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

    st.session_state.binbou_effect = None
    dice = random.randint(1, 4)
    new_pos = max(0, old_pos - dice)
    st.session_state.position = new_pos
    st.session_state.last_dice_value = dice
    st.session_state.current_quiz = None
    st.session_state.correct_streak = 0

    move_binbou(dice)
    binbou_before_contact = st.session_state.binbou_pos
    contact_msg = resolve_binbou_contact(False)
    final_binbou_pos = st.session_state.binbou_pos

    binbou_path_indices = []
    if old_binbou_pos >= 0 and binbou_before_contact >= 0:
        binbou_path_indices = build_path(old_binbou_pos, binbou_before_contact)
    elif old_binbou_pos < 0 and binbou_before_contact >= 0:
        binbou_path_indices = [binbou_before_contact]

    binbou_reset_path_indices = []
    if (
        binbou_before_contact >= 0
        and final_binbou_pos >= 0
        and final_binbou_pos != binbou_before_contact
    ):
        binbou_reset_path_indices = build_path(binbou_before_contact, final_binbou_pos)

    st.session_state.animation_event = {
        "position": new_pos,
        "binbou_pos": final_binbou_pos,
        "binbou_start_pos": old_binbou_pos,
        "binbou_path_indices": binbou_path_indices,
        "binbou_reset_path_indices": binbou_reset_path_indices,
        "path_indices": build_path(old_pos, new_pos),
        "dice": dice,
        "win": False,
    }
    if contact_msg is None:
        st.session_state.play_sound = "wrong"
    add_event_log(f"😢 뒤로 -{dice}칸 → {STATIONS[new_pos]}역")
    st.session_state.game_phase = "ready_to_roll"
    st.session_state.last_message = (
        f"😢 뒤로 가기 주사위 **{dice}** → **{STATIONS[new_pos]}**역으로 후퇴!"
    )
    if contact_msg:
        st.session_state.last_message += f"\n\n{contact_msg}"
    st.session_state.last_message += "\n\n다시 주사위를 굴려 보세요."


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
        if streak >= 3:
            st.session_state.score += 5
            bonus_msg = f" 🔥 연속 {streak}정답 보너스 +5점!"
        st.session_state.current_quiz = None
        st.session_state.play_sound   = "correct"
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
#token-player{{background:radial-gradient(circle at 35% 35%,#7fff00,#2ecc71);box-shadow:0 0 14px 4px rgba(46,204,113,.9);animation:playerPulse 1.4s ease-in-out infinite}}
#token-binbou{{background:radial-gradient(circle at 35% 35%,#ff6b6b,#8e44ad);box-shadow:0 0 14px 4px rgba(142,68,173,.9);animation:binbouPulse 1s ease-in-out infinite;z-index:11}}
@keyframes playerPulse{{0%,100%{{box-shadow:0 0 10px 3px rgba(46,204,113,.8)}}50%{{box-shadow:0 0 24px 10px rgba(46,204,113,.3)}}}}
@keyframes binbouPulse{{0%,100%{{box-shadow:0 0 10px 3px rgba(255,0,100,.8)}}50%{{box-shadow:0 0 24px 10px rgba(255,0,100,.3)}}}}
.sdot{{position:absolute;width:11px;height:11px;border-radius:50%;transform:translate(-50%,-50%);z-index:5}}
.sdot-normal{{background:rgba(255,255,255,.12)}}
.sdot-blue{{background:rgba(52,152,219,.6);box-shadow:0 0 7px rgba(52,152,219,.8)}}
.sdot-red{{background:rgba(231,76,60,.6);box-shadow:0 0 7px rgba(231,76,60,.8)}}
.sdot-star{{background:rgba(241,196,15,.7);box-shadow:0 0 9px rgba(241,196,15,.9);width:14px;height:14px;animation:starGlow 1.8s ease-in-out infinite}}
.sdot-trap{{background:rgba(142,68,173,.7);box-shadow:0 0 7px rgba(142,68,173,.9)}}
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
      <div id="token-player" class="token">🚃</div>
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
      <div id="ghost-overlay">
        <div id="ghost-emoji">👿</div>
        <div id="ghost-txt">먹보유령에게 붙잡혔습니다!</div>
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

  document.getElementById('s-score').textContent=d.score||0;
  document.getElementById('s-turns').textContent=d.turns||0;
  document.getElementById('s-streak').textContent=d.streak||0;
  document.getElementById('s-dest').textContent=(d.destReached||0)+'회';
  document.getElementById('dest-name').textContent=d.destination||'-';
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

  if(d.playSound==='correct')runConfetti();
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

    if(hasMove&&ev.dice){{
      const startPt=d.points[d.stations[ev.path_indices[0]]];
      if(startPt)placeTokenAt(tokenPlayer,startPt.x,startPt.y);
      runDiceAnim(ev.dice,()=>{{
        animateToken(ev.path_indices,()=>{{
          runGhostSequence(ev,()=>{{
            if(d.binbou_pos>=0){{
              tokenBinbou.style.display='flex';
              const finalGhostPt=d.points[d.stations[d.binbou_pos]];
              if(finalGhostPt)placeTokenAt(tokenBinbou,finalGhostPt.x,finalGhostPt.y);
            }}
            showWinOverlay();
          }});
        }});
      }});
    }}else{{
      const pt=d.points[d.stations[d.position]];
      if(pt){{placeTokenAt(tokenPlayer,pt.x,pt.y);label.textContent=d.stations[d.position];label.style.left=pt.x+'%';label.style.top=pt.y+'%';label.style.display='block';}}
      if(d.binbou_pos>=0){{
        tokenBinbou.style.display='flex';
        const bpt=d.points[d.stations[d.binbou_pos]];
        if(bpt)placeTokenAt(tokenBinbou,bpt.x,bpt.y);
      }}
      if(d.binbouEffect)runGhostAnim(showWinOverlay);else showWinOverlay();
    }}
    const logEl=document.getElementById('event-log');
    (d.eventLog||[]).slice().reverse().forEach(msg=>{{const div=document.createElement('div');div.className='log-item';div.textContent=msg;logEl.appendChild(div);}});
    if(d.soundEnabled&&d.playSound){{
      try{{
        const actx=new(window.AudioContext||window.webkitAudioContext)();
        function beep(f,dur,type='sine',vol=0.25){{const o=actx.createOscillator(),g=actx.createGain();o.connect(g);g.connect(actx.destination);o.type=type;o.frequency.value=f;g.gain.setValueAtTime(vol,actx.currentTime);g.gain.exponentialRampToValueAtTime(.001,actx.currentTime+dur);o.start();o.stop(actx.currentTime+dur);}}
        if(d.playSound==='dice'){{beep(440,.1);setTimeout(()=>beep(660,.1),100);}}
        if(d.playSound==='correct'){{beep(523,.1);setTimeout(()=>beep(659,.1),100);setTimeout(()=>beep(784,.25),200);}}
        if(d.playSound==='wrong'){{beep(180,.35,'sawtooth',.2);}}
        if(d.playSound==='ghost'){{beep(150,.18,'sawtooth',.25);setTimeout(()=>beep(95,.45,'square',.2),140);}}
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

    st.session_state.play_sound      = None
    st.session_state.animation_event = None
    st.session_state.binbou_effect   = None
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
- 👿 먹보유령에게 잡히면 감점 후 유령은 6칸 뒤에서 다시 추격
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
        st.caption("💜 **함정 칸** — 먹보유령 소환! 잡힌 뒤에는 6칸 뒤에서 재추격")
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
elif phase == "waiting_penalty_roll":
    st.error(msg)
else:
    st.info(msg)

map_bytes, is_jpg = get_map_bytes()
render_board(map_bytes, is_jpg)
