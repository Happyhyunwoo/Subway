
import base64
import io
import math
import random
import time
import wave
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageDraw, ImageFont


st.set_page_config(
    page_title="서울 지하철 2호선 퀴즈 게임",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_DIR = Path(__file__).parent
DEFAULT_MAP_PATHS = [
    APP_DIR / "line2_map.png",
    APP_DIR / "line2_map_pretty_ui.png",
]


# ============================================================
# Route data
# ============================================================
STATIONS = [
    "성수", "뚝섬", "한양대", "왕십리", "상왕십리", "신당", "동대문역사문화공원",
    "을지로4가", "을지로3가", "을지로입구", "시청", "충정로", "아현", "이대",
    "신촌", "홍대입구", "합정", "당산", "영등포구청", "문래", "신도림", "대림",
    "구로디지털단지", "신대방", "신림", "봉천", "서울대입구", "낙성대", "사당",
    "방배", "서초", "교대", "강남", "역삼", "선릉", "삼성", "종합운동장", "신천", "잠실"
]

ORIGINAL_WIDTH = 1366
ORIGINAL_HEIGHT = 917

STATION_PIXELS = {
    "성수": (1147, 385),
    "뚝섬": (1099, 320),
    "한양대": (1045, 292),
    "왕십리": (1007, 247),
    "상왕십리": (928, 247),
    "신당": (854, 228),
    "동대문역사문화공원": (781, 247),
    "을지로4가": (694, 247),
    "을지로3가": (615, 247),
    "을지로입구": (540, 246),
    "시청": (474, 246),
    "충정로": (399, 247),
    "아현": (324, 247),
    "이대": (291, 289),
    "신촌": (264, 380),
    "홍대입구": (264, 445),
    "합정": (264, 501),
    "당산": (264, 568),
    "영등포구청": (264, 634),
    "문래": (264, 694),
    "신도림": (264, 757),
    "대림": (266, 815),
    "구로디지털단지": (278, 853),
    "신대방": (337, 869),
    "신림": (390, 869),
    "봉천": (445, 869),
    "서울대입구": (498, 869),
    "낙성대": (556, 869),
    "사당": (649, 852),
    "방배": (713, 869),
    "서초": (780, 869),
    "교대": (849, 869),
    "강남": (918, 850),
    "역삼": (978, 869),
    "선릉": (1043, 869),
    "삼성": (1111, 845),
    "종합운동장": (1141, 781),
    "신천": (1144, 719),
    "잠실": (1144, 640),
}

STATION_RATIO = {
    name: (x / ORIGINAL_WIDTH, y / ORIGINAL_HEIGHT)
    for name, (x, y) in STATION_PIXELS.items()
}


# ============================================================
# Quiz data: 6-7세용, 영역별 분리
# ============================================================
QUIZZES = [
    # 수학
    {"category": "수학", "question": "3 + 2는 얼마일까요?", "options": ["4", "5", "6", "7"], "answer": 1},
    {"category": "수학", "question": "10에서 4를 빼면 얼마일까요?", "options": ["5", "6", "7", "8"], "answer": 1},
    {"category": "수학", "question": "1, 2, 3 다음 수는 무엇일까요?", "options": ["4", "5", "6", "7"], "answer": 0},
    {"category": "수학", "question": "사과가 2개 있고 2개를 더 받으면 모두 몇 개일까요?", "options": ["2개", "3개", "4개", "5개"], "answer": 2},
    {"category": "수학", "question": "5는 4보다 어떻게 될까요?", "options": ["작다", "같다", "크다", "없다"], "answer": 2},
    {"category": "수학", "question": "네모의 변은 몇 개일까요?", "options": ["2개", "3개", "4개", "5개"], "answer": 2},
    {"category": "수학", "question": "시계 숫자 12 다음에 오는 숫자는 무엇일까요?", "options": ["1", "2", "11", "13"], "answer": 0},
    {"category": "수학", "question": "7에서 1을 더하면 얼마일까요?", "options": ["6", "7", "8", "9"], "answer": 2},
    {"category": "수학", "question": "두 손의 손가락을 모두 합치면 몇 개일까요?", "options": ["8개", "9개", "10개", "11개"], "answer": 2},
    {"category": "수학", "question": "동그라미는 모서리가 있을까요?", "options": ["1개", "2개", "있다", "없다"], "answer": 3},
    {"category": "수학", "question": "2 + 6은 얼마일까요?", "options": ["6", "7", "8", "9"], "answer": 2},
    {"category": "수학", "question": "9에서 3을 빼면 얼마일까요?", "options": ["5", "6", "7", "8"], "answer": 1},
    {"category": "수학", "question": "삼각형의 꼭짓점은 몇 개일까요?", "options": ["2개", "3개", "4개", "5개"], "answer": 1},
    {"category": "수학", "question": "4와 4를 합치면 얼마일까요?", "options": ["6", "7", "8", "9"], "answer": 2},
    {"category": "수학", "question": "다음 중 가장 큰 수는 무엇일까요?", "options": ["3", "8", "5", "1"], "answer": 1},
    {"category": "수학", "question": "다음 중 가장 작은 수는 무엇일까요?", "options": ["6", "2", "9", "5"], "answer": 1},
    {"category": "수학", "question": "연필 5자루 중 2자루를 쓰면 남은 것은 몇 자루일까요?", "options": ["2자루", "3자루", "4자루", "5자루"], "answer": 1},
    {"category": "수학", "question": "하루는 아침, 점심, 저녁으로 크게 몇 부분처럼 말할 수 있을까요?", "options": ["1부분", "2부분", "3부분", "4부분"], "answer": 2},

    # 국어
    {"category": "국어", "question": "'가, 나, 다' 다음 글자는 무엇일까요?", "options": ["라", "마", "바", "사"], "answer": 0},
    {"category": "국어", "question": "'사과'의 첫 글자는 무엇일까요?", "options": ["사", "과", "수", "가"], "answer": 0},
    {"category": "국어", "question": "'바다'는 몇 글자일까요?", "options": ["1글자", "2글자", "3글자", "4글자"], "answer": 1},
    {"category": "국어", "question": "'하늘'과 반대 느낌의 말로 알맞은 것은 무엇일까요?", "options": ["구름", "땅", "파랑", "새"], "answer": 1},
    {"category": "국어", "question": "다음 중 동물 이름은 무엇일까요?", "options": ["의자", "토끼", "연필", "창문"], "answer": 1},
    {"category": "국어", "question": "'엄마'는 누구를 부르는 말일까요?", "options": ["친구", "선생님", "가족", "동물"], "answer": 2},
    {"category": "국어", "question": "'학교'에서 공부를 가르쳐 주시는 분은 누구일까요?", "options": ["의사", "선생님", "요리사", "경찰관"], "answer": 1},
    {"category": "국어", "question": "'자동차'의 마지막 글자는 무엇일까요?", "options": ["자", "동", "차", "타"], "answer": 2},
    {"category": "국어", "question": "다음 중 과일 이름은 무엇일까요?", "options": ["바나나", "버스", "침대", "신발"], "answer": 0},
    {"category": "국어", "question": "'해'가 뜨는 시간은 언제일까요?", "options": ["아침", "점심", "저녁", "밤"], "answer": 0},
    {"category": "국어", "question": "'기차'는 몇 글자일까요?", "options": ["1글자", "2글자", "3글자", "4글자"], "answer": 1},
    {"category": "국어", "question": "다음 중 탈것 이름은 무엇일까요?", "options": ["책", "지하철", "우유", "꽃"], "answer": 1},
    {"category": "국어", "question": "'고양이'의 첫 글자는 무엇일까요?", "options": ["고", "양", "이", "강"], "answer": 0},
    {"category": "국어", "question": "다음 중 인사말은 무엇일까요?", "options": ["안녕하세요", "사과", "의자", "연필"], "answer": 0},
    {"category": "국어", "question": "'크다'와 반대말은 무엇일까요?", "options": ["작다", "높다", "멀다", "빠르다"], "answer": 0},
    {"category": "국어", "question": "'빠르다'와 반대 느낌의 말은 무엇일까요?", "options": ["느리다", "예쁘다", "동그랗다", "밝다"], "answer": 0},
    {"category": "국어", "question": "다음 중 색깔 이름은 무엇일까요?", "options": ["빨강", "책상", "구름", "기차"], "answer": 0},
    {"category": "국어", "question": "'눈사람'은 몇 글자일까요?", "options": ["2글자", "3글자", "4글자", "5글자"], "answer": 1},

    # 상식
    {"category": "상식", "question": "대한민국의 수도는 어디일까요?", "options": ["서울", "부산", "제주", "대전"], "answer": 0},
    {"category": "상식", "question": "비가 올 때 쓰는 것은 무엇일까요?", "options": ["우산", "연필", "베개", "장갑"], "answer": 0},
    {"category": "상식", "question": "잠을 잘 때 보통 어디에 누울까요?", "options": ["책상", "침대", "냉장고", "자동차"], "answer": 1},
    {"category": "상식", "question": "학교에 갈 때 메고 가는 것은 무엇일까요?", "options": ["가방", "냄비", "빗자루", "컵"], "answer": 0},
    {"category": "상식", "question": "치아를 닦을 때 쓰는 것은 무엇일까요?", "options": ["칫솔", "포크", "수건", "빗"], "answer": 0},
    {"category": "상식", "question": "겨울에 눈이 많이 오는 계절은 무엇일까요?", "options": ["봄", "여름", "가을", "겨울"], "answer": 3},
    {"category": "상식", "question": "빨간불일 때 길을 건너면 될까요?", "options": ["네", "아니요", "가끔", "뛰어서"], "answer": 1},
    {"category": "상식", "question": "소방관은 무엇을 끌까요?", "options": ["불", "자동차", "비", "바람"], "answer": 0},
    {"category": "상식", "question": "지하철은 어디를 달릴까요?", "options": ["하늘", "물속", "땅 위와 땅 아래", "나무 위"], "answer": 2},
    {"category": "상식", "question": "생일 케이크의 촛불은 보통 무엇으로 끌까요?", "options": ["발", "입김", "연필", "물감"], "answer": 1},
    {"category": "상식", "question": "손을 씻을 때 필요한 것은 무엇일까요?", "options": ["물", "모래", "색연필", "베개"], "answer": 0},
    {"category": "상식", "question": "버스나 지하철에서 어른이 서 있으면 어떻게 하면 좋을까요?", "options": ["모른 척한다", "자리를 양보한다", "소리를 지른다", "뛰어다닌다"], "answer": 1},
    {"category": "상식", "question": "길을 건널 때 먼저 보아야 하는 것은 무엇일까요?", "options": ["신호등", "하늘", "가방", "신발"], "answer": 0},
    {"category": "상식", "question": "뜨거운 냄비를 만지면 어떻게 될 수 있을까요?", "options": ["화상을 입을 수 있다", "손이 차가워진다", "잠이 온다", "노래가 나온다"], "answer": 0},
    {"category": "상식", "question": "밥을 먹기 전 손을 씻는 이유는 무엇일까요?", "options": ["깨끗하게 하려고", "더럽히려고", "잠을 자려고", "놀라려고"], "answer": 0},
    {"category": "상식", "question": "길에서 쓰레기를 보면 어디에 버려야 할까요?", "options": ["쓰레기통", "길바닥", "의자 위", "가방 밖"], "answer": 0},
    {"category": "상식", "question": "아플 때 도움을 주는 곳은 어디일까요?", "options": ["병원", "놀이터", "극장", "문구점"], "answer": 0},
    {"category": "상식", "question": "밤에 잘 때 보통 불은 어떻게 할까요?", "options": ["끄거나 어둡게 한다", "더 밝게 켠다", "물을 뿌린다", "창문을 칠한다"], "answer": 0},

    # 과학
    {"category": "과학", "question": "하늘에서 낮에 밝게 빛나는 것은 무엇일까요?", "options": ["달", "별", "해", "구름"], "answer": 2},
    {"category": "과학", "question": "식물은 자라려면 무엇이 필요할까요?", "options": ["물", "장난감", "텔레비전", "베개"], "answer": 0},
    {"category": "과학", "question": "얼음이 녹으면 무엇이 될까요?", "options": ["돌", "물", "모래", "불"], "answer": 1},
    {"category": "과학", "question": "새는 무엇으로 날까요?", "options": ["지느러미", "날개", "바퀴", "손"], "answer": 1},
    {"category": "과학", "question": "물고기는 어디에서 살까요?", "options": ["산", "하늘", "물", "사막"], "answer": 2},
    {"category": "과학", "question": "사람은 무엇으로 숨을 쉴까요?", "options": ["귀", "코", "팔", "무릎"], "answer": 1},
    {"category": "과학", "question": "밤하늘에서 볼 수 있는 것은 무엇일까요?", "options": ["별", "태양", "무지개", "벼락만"], "answer": 0},
    {"category": "과학", "question": "비가 많이 오면 길에 생기는 것은 무엇일까요?", "options": ["그림", "웅덩이", "책장", "풍선"], "answer": 1},
    {"category": "과학", "question": "봄이 되면 많이 피는 것은 무엇일까요?", "options": ["꽃", "눈사람", "얼음", "낙엽"], "answer": 0},
    {"category": "과학", "question": "자석에 잘 붙는 것은 무엇일까요?", "options": ["종이", "나무", "쇠", "물"], "answer": 2},
    {"category": "과학", "question": "비가 온 뒤 하늘에 여러 색으로 보일 수 있는 것은 무엇일까요?", "options": ["무지개", "책상", "양말", "컵"], "answer": 0},
    {"category": "과학", "question": "해가 지면 주변은 보통 어떻게 될까요?", "options": ["어두워진다", "더 밝아진다", "뜨거운 물이 된다", "눈이 온다"], "answer": 0},
    {"category": "과학", "question": "바람이 불면 나뭇잎은 어떻게 될 수 있을까요?", "options": ["흔들린다", "숨어 버린다", "숫자가 된다", "노래가 된다"], "answer": 0},
    {"category": "과학", "question": "달은 보통 언제 더 잘 보일까요?", "options": ["밤", "점심", "아침밥 시간", "운동할 때만"], "answer": 0},
    {"category": "과학", "question": "물이 아주 차가워지면 무엇이 될 수 있을까요?", "options": ["얼음", "불", "연필", "책"], "answer": 0},
    {"category": "과학", "question": "사람의 눈은 무엇을 할 때 필요할까요?", "options": ["보는 것", "듣는 것", "냄새 맡는 것", "걷는 것만"], "answer": 0},
    {"category": "과학", "question": "귀는 무엇을 들을 때 쓰나요?", "options": ["소리", "색깔", "맛", "모양만"], "answer": 0},
    {"category": "과학", "question": "풍선에 바람을 넣으면 어떻게 될까요?", "options": ["커진다", "작아진다", "사라진다", "얼음이 된다"], "answer": 0},

    # 영어
    {"category": "영어", "question": "'apple'은 무엇일까요?", "options": ["사과", "바나나", "우유", "책"], "answer": 0},
    {"category": "영어", "question": "'cat'은 어떤 동물일까요?", "options": ["강아지", "고양이", "물고기", "새"], "answer": 1},
    {"category": "영어", "question": "'blue'는 어떤 색일까요?", "options": ["빨강", "파랑", "노랑", "검정"], "answer": 1},
    {"category": "영어", "question": "'one'은 숫자 몇일까요?", "options": ["1", "2", "3", "4"], "answer": 0},
    {"category": "영어", "question": "'sun'은 무엇일까요?", "options": ["해", "달", "별", "구름"], "answer": 0},
    {"category": "영어", "question": "'book'은 무엇일까요?", "options": ["책", "공", "신발", "컵"], "answer": 0},
    {"category": "영어", "question": "'dog'는 어떤 동물일까요?", "options": ["토끼", "강아지", "고래", "거북이"], "answer": 1},
    {"category": "영어", "question": "'red'는 어떤 색일까요?", "options": ["빨강", "초록", "파랑", "하양"], "answer": 0},
]


# ============================================================
# Session state
# ============================================================
def init_game(keep_names=True):
    old_names = st.session_state.get("players", ["플레이어 1", "플레이어 2"])
    st.session_state.players = old_names if keep_names else ["플레이어 1", "플레이어 2"]
    st.session_state.positions = [0, 0]
    st.session_state.current_player = 0
    st.session_state.game_phase = "start"  # start, ready_to_roll, answering_quiz, waiting_penalty_roll, game_over
    st.session_state.current_quiz = None
    st.session_state.used_quiz_indices = []
    st.session_state.last_dice_value = None
    st.session_state.last_message = "시작 화면에서 게임을 시작해 주세요."
    st.session_state.winner = None
    st.session_state.quiz_key = 0
    st.session_state.pending_action = None
    st.session_state.pending_answer = None
    st.session_state.animation_running = False
    st.session_state.play_sound = None
    st.session_state.show_win_animation = False


if "positions" not in st.session_state:
    init_game(keep_names=False)


# ============================================================
# Sounds
# ============================================================
@st.cache_data(show_spinner=False)
def make_tone_b64(kind="dice"):
    sample_rate = 22050

    if kind == "dice":
        notes = [(600, 0.07), (720, 0.07), (840, 0.07), (660, 0.07), (900, 0.10)]
        volume = 0.22
    elif kind == "correct":
        notes = [(660, 0.10), (880, 0.12), (1040, 0.18)]
        volume = 0.24
    elif kind == "wrong":
        notes = [(300, 0.18), (220, 0.22)]
        volume = 0.23
    elif kind == "win":
        notes = [(523, 0.11), (659, 0.11), (784, 0.11), (1046, 0.28), (784, 0.13), (1046, 0.35)]
        volume = 0.25
    else:
        notes = [(440, 0.20)]
        volume = 0.20

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        for freq, duration in notes:
            total = int(sample_rate * duration)
            for i in range(total):
                fade = min(1.0, i / max(1, total * 0.15), (total - i) / max(1, total * 0.18))
                sample = int(32767 * volume * fade * math.sin(2 * math.pi * freq * i / sample_rate))
                wav.writeframesraw(sample.to_bytes(2, "little", signed=True))
            silence = int(sample_rate * 0.025)
            for _ in range(silence):
                wav.writeframesraw((0).to_bytes(2, "little", signed=True))

    return base64.b64encode(buffer.getvalue()).decode("ascii")


def play_sound_once():
    if not st.session_state.get("sound_enabled", True):
        st.session_state.play_sound = None
        return

    kind = st.session_state.get("play_sound")
    if not kind:
        return

    audio_b64 = make_tone_b64(kind)
    components.html(
        f"""
        <audio autoplay>
            <source src="data:audio/wav;base64,{audio_b64}" type="audio/wav">
        </audio>
        """,
        height=0,
    )
    st.session_state.play_sound = None


# ============================================================
# Map and drawing functions
# ============================================================
def default_map_path():
    for path in DEFAULT_MAP_PATHS:
        if path.exists():
            return path
    return None


def load_map_image(uploaded_file):
    if uploaded_file is not None:
        return Image.open(uploaded_file).convert("RGBA")
    path = default_map_path()
    if path is None:
        st.error("노선도 이미지 파일이 없습니다. line2_map.png를 GitHub 저장소에 함께 올려 주세요.")
        st.stop()
    return Image.open(path).convert("RGBA")


def resized_map(base_img, target_width=1050):
    w, h = base_img.size
    target_height = int(h * (target_width / w))
    return base_img.resize((target_width, target_height), Image.Resampling.LANCZOS)


def station_xy(map_img, station_index):
    name = STATIONS[station_index]
    rx, ry = STATION_RATIO[name]
    return int(rx * map_img.width), int(ry * map_img.height)


def get_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf" if bold else "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/malgunbd.ttf" if bold else "C:/Windows/Fonts/malgun.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def draw_label_center(draw, text, center, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text((center[0] - (bbox[2] - bbox[0]) / 2, center[1] - (bbox[3] - bbox[1]) / 2), text, font=font, fill=fill)


def draw_train_token(draw, x, y, color, label, scale=1.0):
    w = max(32, int(44 * scale))
    h = max(28, int(36 * scale))
    r = max(8, int(9 * scale))

    x0, y0 = x - w // 2, y - h // 2
    x1, y1 = x + w // 2, y + h // 2

    draw.rounded_rectangle((x0 + 4, y0 + 5, x1 + 4, y1 + 5), radius=r, fill=(0, 0, 0, 80))
    draw.rounded_rectangle((x0, y0, x1, y1), radius=r, fill=color, outline=(255, 255, 255, 255), width=max(2, int(3 * scale)))

    win_h = int(10 * scale)
    draw.rounded_rectangle((x0 + int(8 * scale), y0 + int(7 * scale), x1 - int(8 * scale), y0 + int(7 * scale) + win_h),
                           radius=int(4 * scale), fill=(230, 245, 255, 255))

    wheel_r = max(3, int(4 * scale))
    draw.ellipse((x0 + int(9 * scale) - wheel_r, y1 - int(4 * scale) - wheel_r,
                  x0 + int(9 * scale) + wheel_r, y1 - int(4 * scale) + wheel_r), fill=(35, 35, 35, 255))
    draw.ellipse((x1 - int(9 * scale) - wheel_r, y1 - int(4 * scale) - wheel_r,
                  x1 - int(9 * scale) + wheel_r, y1 - int(4 * scale) + wheel_r), fill=(35, 35, 35, 255))

    font = get_font(max(11, int(13 * scale)), bold=True)
    draw_label_center(draw, label, (x, y + int(5 * scale)), font, (255, 255, 255, 255))


def draw_character_token(draw, x, y, color, label, scale=1.0):
    r = max(17, int(22 * scale))
    draw.ellipse((x - r + 4, y - r + 5, x + r + 4, y + r + 5), fill=(0, 0, 0, 75))
    draw.ellipse((x - r, y - r, x + r, y + r), fill=color, outline=(255, 255, 255, 255), width=max(2, int(3 * scale)))

    eye_r = max(2, int(3 * scale))
    draw.ellipse((x - int(8 * scale) - eye_r, y - int(4 * scale) - eye_r,
                  x - int(8 * scale) + eye_r, y - int(4 * scale) + eye_r), fill=(255, 255, 255, 255))
    draw.ellipse((x + int(8 * scale) - eye_r, y - int(4 * scale) - eye_r,
                  x + int(8 * scale) + eye_r, y - int(4 * scale) + eye_r), fill=(255, 255, 255, 255))
    draw.arc((x - int(9 * scale), y, x + int(9 * scale), y + int(12 * scale)), 10, 170, fill=(255, 255, 255, 255), width=max(2, int(2 * scale)))

    font = get_font(max(10, int(12 * scale)), bold=True)
    draw_label_center(draw, label, (x, y + int(14 * scale)), font, (255, 255, 255, 255))


def draw_token(draw, x, y, color, label, token_style, scale=1.0):
    if token_style == "캐릭터 말":
        draw_character_token(draw, x, y, color, label, scale)
    else:
        draw_train_token(draw, x, y, color, label, scale)


def draw_die_face(draw, x, y, size, value):
    radius = max(8, size // 7)
    draw.rounded_rectangle((x + 4, y + 4, x + size + 4, y + size + 4), radius=radius, fill=(0, 0, 0, 60))
    draw.rounded_rectangle(
        (x, y, x + size, y + size),
        radius=radius,
        fill=(255, 250, 240, 255),
        outline=(251, 146, 60, 255),
        width=max(2, size // 24),
    )
    dot_r = max(4, size // 13)
    positions = {
        "tl": (x + size * 0.27, y + size * 0.27),
        "tr": (x + size * 0.73, y + size * 0.27),
        "cl": (x + size * 0.27, y + size * 0.50),
        "cc": (x + size * 0.50, y + size * 0.50),
        "cr": (x + size * 0.73, y + size * 0.50),
        "bl": (x + size * 0.27, y + size * 0.73),
        "br": (x + size * 0.73, y + size * 0.73),
    }
    patterns = {
        1: ["cc"],
        2: ["tl", "br"],
        3: ["tl", "cc", "br"],
        4: ["tl", "tr", "bl", "br"],
        5: ["tl", "tr", "cc", "bl", "br"],
        6: ["tl", "tr", "cl", "cr", "bl", "br"],
    }
    for key in patterns.get(value, ["cc"]):
        cx, cy = positions[key]
        draw.ellipse((cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r), fill=(154, 52, 18, 255))


def draw_info_panel(draw, map_img, dice_value=None, moving_text=None):
    scale = map_img.width / 1000
    x0, y0 = int(24 * scale), int(24 * scale)
    w, h = int(272 * scale), int(106 * scale)
    draw.rounded_rectangle((x0 + 4, y0 + 4, x0 + w + 4, y0 + h + 4), radius=int(18 * scale), fill=(0, 0, 0, 55))
    draw.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=int(18 * scale), fill=(255, 255, 255, 240), outline=(34, 197, 94, 255), width=max(2, int(3 * scale)))
    font_title = get_font(max(13, int(17 * scale)), bold=True)
    font_small = get_font(max(11, int(13 * scale)), bold=False)
    draw.text((x0 + int(14 * scale), y0 + int(14 * scale)), "주사위", font=font_title, fill=(20, 83, 45, 255))
    if moving_text:
        draw.text((x0 + int(14 * scale), y0 + int(62 * scale)), moving_text, font=font_small, fill=(17, 24, 39, 255))
    die_size = int(66 * scale)
    draw_die_face(draw, x0 + w - die_size - int(14 * scale), y0 + int(18 * scale), die_size, dice_value or 1)


def draw_path_highlight(draw, map_img, path_indices, upto=None):
    if not path_indices or len(path_indices) < 2:
        return
    line_width = max(4, int(map_img.width * 0.006))
    max_i = len(path_indices) - 1 if upto is None else min(upto, len(path_indices) - 1)
    for i in range(max_i):
        p1 = station_xy(map_img, path_indices[i])
        p2 = station_xy(map_img, path_indices[i + 1])
        draw.line((p1[0], p1[1], p2[0], p2[1]), fill=(255, 75, 75, 170), width=line_width)


def draw_board(base_img, positions, dice_value=None, moving_text=None, moving_token=None, path_indices=None, highlight_upto=None, confetti=None, celebration_text=None):
    img = base_img.copy()
    draw = ImageDraw.Draw(img, "RGBA")

    if path_indices:
        draw_path_highlight(draw, img, path_indices, upto=highlight_upto)

    token_colors = [(239, 68, 68, 255), (37, 99, 235, 255)]
    scale = img.width / 1000
    token_positions = [station_xy(img, positions[0]), station_xy(img, positions[1])]

    if moving_token is not None:
        moving_player, xy = moving_token
        token_positions[moving_player] = xy

    same_station = positions[0] == positions[1] and moving_token is None
    for i, (x, y) in enumerate(token_positions):
        if same_station:
            dx = -20 if i == 0 else 20
            dy = -18 if i == 0 else 18
        else:
            dx = 0
            dy = -20 if i == 0 else 20
        if moving_token is not None and i == moving_token[0]:
            dx = 0
            dy = -20
        draw_token(
            draw,
            x + int(dx * scale),
            y + int(dy * scale),
            token_colors[i],
            str(i + 1),
            st.session_state.get("token_style", "기차 아이콘"),
            scale=scale,
        )

    if confetti:
        for item in confetti:
            cx, cy, size, color = item
            draw.ellipse((cx - size, cy - size, cx + size, cy + size), fill=color)

    if celebration_text:
        font_big = get_font(max(26, int(38 * scale)), bold=True)
        font_mid = get_font(max(15, int(20 * scale)), bold=True)
        box_w = int(520 * scale)
        box_h = int(130 * scale)
        x0 = img.width // 2 - box_w // 2
        y0 = int(42 * scale)
        draw.rounded_rectangle((x0 + 5, y0 + 6, x0 + box_w + 5, y0 + box_h + 6), radius=int(26 * scale), fill=(0, 0, 0, 70))
        draw.rounded_rectangle((x0, y0, x0 + box_w, y0 + box_h), radius=int(26 * scale), fill=(255, 255, 255, 245), outline=(251, 191, 36, 255), width=max(3, int(5 * scale)))
        draw_label_center(draw, celebration_text, (img.width // 2, y0 + int(45 * scale)), font_big, (180, 83, 9, 255))
        draw_label_center(draw, "잠실역 도착!", (img.width // 2, y0 + int(92 * scale)), font_mid, (30, 64, 175, 255))

    draw_info_panel(draw, img, dice_value=dice_value, moving_text=moving_text)
    return img.convert("RGB")


def interpolate(p1, p2, t):
    return int(p1[0] + (p2[0] - p1[0]) * t), int(p1[1] + (p2[1] - p1[1]) * t)


def make_confetti(width, height, n=90, progress=0.0):
    random.seed(20260605)
    colors = [
        (239, 68, 68, 220), (59, 130, 246, 220), (34, 197, 94, 220),
        (250, 204, 21, 220), (168, 85, 247, 220), (236, 72, 153, 220),
    ]
    confetti = []
    for _ in range(n):
        x = random.randint(20, width - 20)
        start_y = random.randint(-height // 2, 20)
        fall = int((height + 160) * progress)
        y = (start_y + fall + random.randint(-30, 30)) % (height + 80) - 40
        size = random.randint(4, 10)
        color = random.choice(colors)
        confetti.append((x, y, size, color))
    return confetti


def animate_victory(placeholder, base_img, positions, dice_value):
    for i in range(24):
        progress = i / 23
        confetti = make_confetti(base_img.width, base_img.height, n=120, progress=progress)
        frame = draw_board(
            base_img,
            positions,
            dice_value=dice_value,
            moving_text="승리!",
            confetti=confetti,
            celebration_text="축하합니다!",
        )
        placeholder.image(frame, use_container_width=True)
        time.sleep(0.07)


def animate_move(placeholder, base_img, old_positions, player_index, path_indices, dice_value, direction_text):
    st.session_state.animation_running = True

    for _ in range(12):
        frame = draw_board(
            base_img,
            old_positions,
            dice_value=random.randint(1, 6),
            moving_text="주사위 굴리는 중",
        )
        placeholder.image(frame, use_container_width=True)
        time.sleep(0.065)

    frame = draw_board(base_img, old_positions, dice_value=dice_value, moving_text=f"결과: {dice_value}")
    placeholder.image(frame, use_container_width=True)
    time.sleep(0.18)

    if len(path_indices) >= 2:
        for seg_i in range(len(path_indices) - 1):
            start_xy = station_xy(base_img, path_indices[seg_i])
            end_xy = station_xy(base_img, path_indices[seg_i + 1])
            for step in range(1, 11):
                x, y = interpolate(start_xy, end_xy, step / 10)
                frame = draw_board(
                    base_img,
                    old_positions,
                    dice_value=dice_value,
                    moving_text=direction_text,
                    moving_token=(player_index, (x, y)),
                    path_indices=path_indices,
                    highlight_upto=seg_i + 1,
                )
                placeholder.image(frame, use_container_width=True)
                time.sleep(0.05)

    final_positions = old_positions.copy()
    final_positions[player_index] = path_indices[-1]
    frame = draw_board(
        base_img,
        final_positions,
        dice_value=dice_value,
        moving_text=f"도착: {STATIONS[path_indices[-1]]}",
        path_indices=path_indices,
    )
    placeholder.image(frame, use_container_width=True)
    time.sleep(0.22)
    st.session_state.animation_running = False


# ============================================================
# Game logic
# ============================================================
def roll_dice():
    return random.randint(1, 6)


def path_between(start_idx, end_idx):
    if end_idx >= start_idx:
        return list(range(start_idx, end_idx + 1))
    return list(range(start_idx, end_idx - 1, -1))


def selected_categories():
    categories = st.session_state.get("selected_categories", ["수학", "국어", "상식", "과학"])
    if not categories:
        return ["수학", "국어", "상식", "과학"]
    return categories


def get_random_quiz():
    categories = selected_categories()
    candidate_indices = [i for i, q in enumerate(QUIZZES) if q["category"] in categories]
    used = set(st.session_state.used_quiz_indices)
    available = [i for i in candidate_indices if i not in used]
    if not available:
        st.session_state.used_quiz_indices = []
        available = candidate_indices[:]
    idx = random.choice(available)
    st.session_state.used_quiz_indices.append(idx)
    quiz = QUIZZES[idx].copy()
    quiz["quiz_id"] = idx
    return quiz


def start_game():
    st.session_state.positions = [0, 0]
    st.session_state.current_player = 0
    st.session_state.game_phase = "ready_to_roll"
    st.session_state.current_quiz = None
    st.session_state.used_quiz_indices = []
    st.session_state.last_dice_value = None
    st.session_state.last_message = "게임이 시작되었습니다. 플레이어 1이 주사위를 굴립니다."
    st.session_state.winner = None
    st.session_state.quiz_key = 0
    st.session_state.pending_action = None
    st.session_state.pending_answer = None
    st.session_state.show_win_animation = False


def handle_forward_action(board_placeholder, base_map):
    player = st.session_state.current_player
    old_positions = st.session_state.positions.copy()
    old_pos = old_positions[player]
    dice = roll_dice()
    new_pos = min(old_pos + dice, len(STATIONS) - 1)
    path_indices = path_between(old_pos, new_pos)

    animate_move(board_placeholder, base_map, old_positions, player, path_indices, dice, "앞으로 이동")
    st.session_state.positions[player] = new_pos
    st.session_state.last_dice_value = dice
    st.session_state.play_sound = "dice"

    if new_pos >= len(STATIONS) - 1:
        st.session_state.game_phase = "game_over"
        st.session_state.winner = player
        st.session_state.current_quiz = None
        st.session_state.last_message = f"🎉 {st.session_state.players[player]}님이 잠실역에 도착했습니다!"
        st.session_state.play_sound = "win"
        st.session_state.show_win_animation = True
        animate_victory(board_placeholder, base_map, st.session_state.positions, dice)
    else:
        st.session_state.current_quiz = get_random_quiz()
        st.session_state.game_phase = "answering_quiz"
        st.session_state.last_message = (
            f"{st.session_state.players[player]}님이 주사위 {dice}을/를 굴려 "
            f"{STATIONS[new_pos]}역에 도착했습니다. 사이드바에서 퀴즈를 풀어 보세요."
        )
        st.session_state.quiz_key += 1


def handle_backward_action(board_placeholder, base_map):
    player = st.session_state.current_player
    old_positions = st.session_state.positions.copy()
    old_pos = old_positions[player]
    dice = roll_dice()
    new_pos = max(0, old_pos - dice)
    path_indices = path_between(old_pos, new_pos)

    animate_move(board_placeholder, base_map, old_positions, player, path_indices, dice, "뒤로 이동")
    st.session_state.positions[player] = new_pos
    st.session_state.last_dice_value = dice
    st.session_state.current_quiz = None
    st.session_state.play_sound = "dice"

    next_player = 1 - player
    st.session_state.current_player = next_player
    st.session_state.game_phase = "ready_to_roll"
    st.session_state.last_message = (
        f"{st.session_state.players[player]}님이 벌칙 주사위 {dice}만큼 뒤로 이동해 "
        f"{STATIONS[new_pos]}역으로 갔습니다. 이제 {st.session_state.players[next_player]}님의 차례입니다."
    )


def handle_quiz_answer(answer):
    quiz = st.session_state.current_quiz
    player = st.session_state.current_player
    if quiz is None:
        return

    correct = quiz["options"][quiz["answer"]]
    if answer == correct:
        st.session_state.current_quiz = None
        st.session_state.game_phase = "ready_to_roll"
        st.session_state.last_message = f"✅ 정답입니다. {st.session_state.players[player]}님은 한 번 더 주사위를 굴립니다."
        st.session_state.play_sound = "correct"
    else:
        st.session_state.game_phase = "waiting_penalty_roll"
        st.session_state.last_message = (
            f"❌ 아쉽지만 정답은 '{correct}'입니다. "
            f"{st.session_state.players[player]}님은 사이드바에서 벌칙 주사위를 굴려 주세요."
        )
        st.session_state.play_sound = "wrong"


# ============================================================
# Sidebar
# ============================================================
ALL_CATEGORIES = sorted({q["category"] for q in QUIZZES}, key=["수학", "국어", "상식", "과학", "영어"].index)

with st.sidebar:
    st.title("🎲 게임 진행")

    st.write(f"현재 차례: **{st.session_state.players[st.session_state.current_player]}**")
    st.write(f"마지막 주사위: **{st.session_state.last_dice_value if st.session_state.last_dice_value else '-'}**")
    st.write(f"1번 말: **{STATIONS[st.session_state.positions[0]]}**")
    st.write(f"2번 말: **{STATIONS[st.session_state.positions[1]]}**")

    st.divider()

    phase = st.session_state.game_phase

    if phase == "start":
        st.info("메인 화면 또는 아래 버튼으로 게임을 시작하세요.")
        if st.button("🚇 게임 시작", use_container_width=True, type="primary"):
            start_game()
            st.rerun()

    elif phase == "ready_to_roll":
        if st.button("🎲 주사위 굴리기", use_container_width=True, type="primary"):
            st.session_state.pending_action = "forward"
            st.rerun()

    elif phase == "answering_quiz":
        quiz = st.session_state.current_quiz
        st.subheader("🧠 퀴즈")
        if quiz is None:
            st.warning("퀴즈가 아직 준비되지 않았습니다.")
        else:
            st.markdown(f"**[{quiz['category']}] {quiz['question']}**")
            answer = st.radio(
                "정답을 고르세요.",
                quiz["options"],
                key=f"sidebar_quiz_answer_{st.session_state.quiz_key}",
            )
            if st.button("정답 제출", use_container_width=True, type="primary"):
                st.session_state.pending_answer = answer
                st.rerun()

    elif phase == "waiting_penalty_roll":
        st.error("오답입니다. 벌칙 주사위를 굴려 뒤로 이동하세요.")
        if st.button("↩️ 벌칙 주사위 굴리기", use_container_width=True, type="primary"):
            st.session_state.pending_action = "backward"
            st.rerun()

    elif phase == "game_over":
        st.success(f"🏆 우승: {st.session_state.players[st.session_state.winner]}")
        if st.button("새 게임 시작", use_container_width=True, type="primary"):
            start_game()
            st.rerun()

    st.divider()
    st.subheader("설정")

    with st.form("name_form"):
        p1 = st.text_input("플레이어 1 이름", st.session_state.players[0])
        p2 = st.text_input("플레이어 2 이름", st.session_state.players[1])
        if st.form_submit_button("이름 저장", use_container_width=True):
            st.session_state.players = [p1.strip() or "플레이어 1", p2.strip() or "플레이어 2"]
            st.rerun()

    st.session_state.token_style = st.radio(
        "말 모양",
        ["기차 아이콘", "캐릭터 말"],
        index=0 if st.session_state.get("token_style", "기차 아이콘") == "기차 아이콘" else 1,
    )

    st.session_state.sound_enabled = st.toggle(
        "효과음 켜기",
        value=st.session_state.get("sound_enabled", True),
    )

    st.session_state.selected_categories = st.multiselect(
        "퀴즈 영역",
        ALL_CATEGORIES,
        default=st.session_state.get("selected_categories", ["수학", "국어", "상식", "과학"]),
    )

    st.caption(f"선택된 영역 문제 수: {sum(1 for q in QUIZZES if q['category'] in selected_categories())}개")

    uploaded_map = st.file_uploader("다른 노선도 이미지 사용", type=["png", "jpg", "jpeg"])

    if st.button("게임 초기화", use_container_width=True):
        init_game(keep_names=True)
        st.rerun()


# ============================================================
# Main page
# ============================================================
st.title("🚇 서울 지하철 2호선 퀴즈 보드게임")
st.caption("왼쪽 사이드바에서 주사위와 퀴즈를 조작하고, 메인 화면에서 예쁜 말 이동과 축하 애니메이션을 확인합니다.")

play_sound_once()

base_original = load_map_image(uploaded_map)
base_map = resized_map(base_original, target_width=1050)

board_placeholder = st.empty()

if st.session_state.pending_answer is not None:
    answer_to_process = st.session_state.pending_answer
    st.session_state.pending_answer = None
    handle_quiz_answer(answer_to_process)
    st.rerun()

elif st.session_state.pending_action == "forward":
    st.session_state.pending_action = None
    handle_forward_action(board_placeholder, base_map)
    st.rerun()

elif st.session_state.pending_action == "backward":
    st.session_state.pending_action = None
    handle_backward_action(board_placeholder, base_map)
    st.rerun()

else:
    board = draw_board(
        base_map,
        st.session_state.positions,
        dice_value=st.session_state.last_dice_value,
        moving_text="현재 위치",
    )
    board_placeholder.image(board, use_container_width=True)


if st.session_state.game_phase == "start":
    st.markdown(
        """
        <div style="padding: 26px; border-radius: 22px; background: linear-gradient(135deg, #ecfdf5, #eff6ff); border: 1px solid #bfdbfe;">
            <h2 style="margin-top:0;">🚇 성수역에서 잠실역까지!</h2>
            <p style="font-size: 18px;">
                2호선을 짧게 가지 않고 크게 돌아가는 긴 경로로 이동합니다.
                주사위를 굴리고, 역마다 6-7세용 객관식 퀴즈를 풀어 보세요.
            </p>
            <p style="font-size: 16px;">
                정답이면 한 번 더 이동하고, 오답이면 벌칙 주사위를 굴려 뒤로 이동합니다.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("🚇 지금 시작하기", type="primary", use_container_width=True):
        start_game()
        st.rerun()

elif st.session_state.game_phase == "game_over":
    winner_name = st.session_state.players[st.session_state.winner]
    st.balloons()
    st.markdown(
        f"""
        <div style="padding: 28px; border-radius: 24px; background: linear-gradient(135deg, #fff7ed, #fef3c7); border: 2px solid #fbbf24; text-align:center;">
            <h1 style="margin-top:0;">🏆 {winner_name} 승리!</h1>
            <p style="font-size: 20px;">잠실역에 도착했습니다. 축하합니다!</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

else:
    st.info(st.session_state.last_message)

col1, col2 = st.columns(2)
with col1:
    st.metric(st.session_state.players[0], STATIONS[st.session_state.positions[0]], f"{st.session_state.positions[0]} / {len(STATIONS) - 1}")
    st.progress(st.session_state.positions[0] / (len(STATIONS) - 1))
with col2:
    st.metric(st.session_state.players[1], STATIONS[st.session_state.positions[1]], f"{st.session_state.positions[1]} / {len(STATIONS) - 1}")
    st.progress(st.session_state.positions[1] / (len(STATIONS) - 1))

with st.expander("전체 이동 경로 보기"):
    st.write(" → ".join(STATIONS))
