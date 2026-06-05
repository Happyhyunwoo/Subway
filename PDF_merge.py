
import base64
import json
import random
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="서울 지하철 2호선 퀴즈 게임",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_DIR = Path(__file__).parent
DEFAULT_MAP_PATHS = [
    APP_DIR / "line2_map.png",
    APP_DIR / "line2_map_smooth.png",
    APP_DIR / "line2_map_pretty_ui.png",
]


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

STATION_POINTS = {
    name: {"x": x / ORIGINAL_WIDTH * 100, "y": y / ORIGINAL_HEIGHT * 100}
    for name, (x, y) in STATION_PIXELS.items()
}

QUIZZES = [{'category': '수학', 'question': '3 + 2는 얼마일까요?', 'options': ['4', '5', '6', '7'], 'answer': 1}, {'category': '수학', 'question': '10에서 4를 빼면 얼마일까요?', 'options': ['5', '6', '7', '8'], 'answer': 1}, {'category': '수학', 'question': '1, 2, 3 다음 수는 무엇일까요?', 'options': ['4', '5', '6', '7'], 'answer': 0}, {'category': '수학', 'question': '사과가 2개 있고 2개를 더 받으면 모두 몇 개일까요?', 'options': ['2개', '3개', '4개', '5개'], 'answer': 2}, {'category': '수학', 'question': '5는 4보다 어떻게 될까요?', 'options': ['작다', '같다', '크다', '없다'], 'answer': 2}, {'category': '수학', 'question': '네모의 변은 몇 개일까요?', 'options': ['2개', '3개', '4개', '5개'], 'answer': 2}, {'category': '수학', 'question': '시계 숫자 12 다음에 오는 숫자는 무엇일까요?', 'options': ['1', '2', '11', '13'], 'answer': 0}, {'category': '수학', 'question': '7에서 1을 더하면 얼마일까요?', 'options': ['6', '7', '8', '9'], 'answer': 2}, {'category': '수학', 'question': '두 손의 손가락을 모두 합치면 몇 개일까요?', 'options': ['8개', '9개', '10개', '11개'], 'answer': 2}, {'category': '수학', 'question': '동그라미는 모서리가 있을까요?', 'options': ['1개', '2개', '있다', '없다'], 'answer': 3}, {'category': '수학', 'question': '2 + 6은 얼마일까요?', 'options': ['6', '7', '8', '9'], 'answer': 2}, {'category': '수학', 'question': '9에서 3을 빼면 얼마일까요?', 'options': ['5', '6', '7', '8'], 'answer': 1}, {'category': '수학', 'question': '삼각형의 꼭짓점은 몇 개일까요?', 'options': ['2개', '3개', '4개', '5개'], 'answer': 1}, {'category': '수학', 'question': '4와 4를 합치면 얼마일까요?', 'options': ['6', '7', '8', '9'], 'answer': 2}, {'category': '수학', 'question': '다음 중 가장 큰 수는 무엇일까요?', 'options': ['3', '8', '5', '1'], 'answer': 1}, {'category': '수학', 'question': '다음 중 가장 작은 수는 무엇일까요?', 'options': ['6', '2', '9', '5'], 'answer': 1}, {'category': '수학', 'question': '연필 5자루 중 2자루를 쓰면 남은 것은 몇 자루일까요?', 'options': ['2자루', '3자루', '4자루', '5자루'], 'answer': 1}, {'category': '수학', 'question': '하루는 아침, 점심, 저녁으로 크게 몇 부분처럼 말할 수 있을까요?', 'options': ['1부분', '2부분', '3부분', '4부분'], 'answer': 2}, {'category': '국어', 'question': "'가, 나, 다' 다음 글자는 무엇일까요?", 'options': ['라', '마', '바', '사'], 'answer': 0}, {'category': '국어', 'question': "'사과'의 첫 글자는 무엇일까요?", 'options': ['사', '과', '수', '가'], 'answer': 0}, {'category': '국어', 'question': "'바다'는 몇 글자일까요?", 'options': ['1글자', '2글자', '3글자', '4글자'], 'answer': 1}, {'category': '국어', 'question': "'하늘'과 반대 느낌의 말로 알맞은 것은 무엇일까요?", 'options': ['구름', '땅', '파랑', '새'], 'answer': 1}, {'category': '국어', 'question': '다음 중 동물 이름은 무엇일까요?', 'options': ['의자', '토끼', '연필', '창문'], 'answer': 1}, {'category': '국어', 'question': "'엄마'는 누구를 부르는 말일까요?", 'options': ['친구', '선생님', '가족', '동물'], 'answer': 2}, {'category': '국어', 'question': "'학교'에서 공부를 가르쳐 주시는 분은 누구일까요?", 'options': ['의사', '선생님', '요리사', '경찰관'], 'answer': 1}, {'category': '국어', 'question': "'자동차'의 마지막 글자는 무엇일까요?", 'options': ['자', '동', '차', '타'], 'answer': 2}, {'category': '국어', 'question': '다음 중 과일 이름은 무엇일까요?', 'options': ['바나나', '버스', '침대', '신발'], 'answer': 0}, {'category': '국어', 'question': "'해'가 뜨는 시간은 언제일까요?", 'options': ['아침', '점심', '저녁', '밤'], 'answer': 0}, {'category': '국어', 'question': "'기차'는 몇 글자일까요?", 'options': ['1글자', '2글자', '3글자', '4글자'], 'answer': 1}, {'category': '국어', 'question': '다음 중 탈것 이름은 무엇일까요?', 'options': ['책', '지하철', '우유', '꽃'], 'answer': 1}, {'category': '국어', 'question': "'고양이'의 첫 글자는 무엇일까요?", 'options': ['고', '양', '이', '강'], 'answer': 0}, {'category': '국어', 'question': '다음 중 인사말은 무엇일까요?', 'options': ['안녕하세요', '사과', '의자', '연필'], 'answer': 0}, {'category': '국어', 'question': "'크다'와 반대말은 무엇일까요?", 'options': ['작다', '높다', '멀다', '빠르다'], 'answer': 0}, {'category': '국어', 'question': "'빠르다'와 반대 느낌의 말은 무엇일까요?", 'options': ['느리다', '예쁘다', '동그랗다', '밝다'], 'answer': 0}, {'category': '국어', 'question': '다음 중 색깔 이름은 무엇일까요?', 'options': ['빨강', '책상', '구름', '기차'], 'answer': 0}, {'category': '국어', 'question': "'눈사람'은 몇 글자일까요?", 'options': ['2글자', '3글자', '4글자', '5글자'], 'answer': 1}, {'category': '상식', 'question': '대한민국의 수도는 어디일까요?', 'options': ['서울', '부산', '제주', '대전'], 'answer': 0}, {'category': '상식', 'question': '비가 올 때 쓰는 것은 무엇일까요?', 'options': ['우산', '연필', '베개', '장갑'], 'answer': 0}, {'category': '상식', 'question': '잠을 잘 때 보통 어디에 누울까요?', 'options': ['책상', '침대', '냉장고', '자동차'], 'answer': 1}, {'category': '상식', 'question': '학교에 갈 때 메고 가는 것은 무엇일까요?', 'options': ['가방', '냄비', '빗자루', '컵'], 'answer': 0}, {'category': '상식', 'question': '치아를 닦을 때 쓰는 것은 무엇일까요?', 'options': ['칫솔', '포크', '수건', '빗'], 'answer': 0}, {'category': '상식', 'question': '겨울에 눈이 많이 오는 계절은 무엇일까요?', 'options': ['봄', '여름', '가을', '겨울'], 'answer': 3}, {'category': '상식', 'question': '빨간불일 때 길을 건너면 될까요?', 'options': ['네', '아니요', '가끔', '뛰어서'], 'answer': 1}, {'category': '상식', 'question': '소방관은 무엇을 끌까요?', 'options': ['불', '자동차', '비', '바람'], 'answer': 0}, {'category': '상식', 'question': '지하철은 어디를 달릴까요?', 'options': ['하늘', '물속', '땅 위와 땅 아래', '나무 위'], 'answer': 2}, {'category': '상식', 'question': '생일 케이크의 촛불은 보통 무엇으로 끌까요?', 'options': ['발', '입김', '연필', '물감'], 'answer': 1}, {'category': '상식', 'question': '손을 씻을 때 필요한 것은 무엇일까요?', 'options': ['물', '모래', '색연필', '베개'], 'answer': 0}, {'category': '상식', 'question': '버스나 지하철에서 어른이 서 있으면 어떻게 하면 좋을까요?', 'options': ['모른 척한다', '자리를 양보한다', '소리를 지른다', '뛰어다닌다'], 'answer': 1}, {'category': '상식', 'question': '길을 건널 때 먼저 보아야 하는 것은 무엇일까요?', 'options': ['신호등', '하늘', '가방', '신발'], 'answer': 0}, {'category': '상식', 'question': '뜨거운 냄비를 만지면 어떻게 될 수 있을까요?', 'options': ['화상을 입을 수 있다', '손이 차가워진다', '잠이 온다', '노래가 나온다'], 'answer': 0}, {'category': '상식', 'question': '밥을 먹기 전 손을 씻는 이유는 무엇일까요?', 'options': ['깨끗하게 하려고', '더럽히려고', '잠을 자려고', '놀라려고'], 'answer': 0}, {'category': '상식', 'question': '길에서 쓰레기를 보면 어디에 버려야 할까요?', 'options': ['쓰레기통', '길바닥', '의자 위', '가방 밖'], 'answer': 0}, {'category': '상식', 'question': '아플 때 도움을 주는 곳은 어디일까요?', 'options': ['병원', '놀이터', '극장', '문구점'], 'answer': 0}, {'category': '상식', 'question': '밤에 잘 때 보통 불은 어떻게 할까요?', 'options': ['끄거나 어둡게 한다', '더 밝게 켠다', '물을 뿌린다', '창문을 칠한다'], 'answer': 0}, {'category': '과학', 'question': '하늘에서 낮에 밝게 빛나는 것은 무엇일까요?', 'options': ['달', '별', '해', '구름'], 'answer': 2}, {'category': '과학', 'question': '식물은 자라려면 무엇이 필요할까요?', 'options': ['물', '장난감', '텔레비전', '베개'], 'answer': 0}, {'category': '과학', 'question': '얼음이 녹으면 무엇이 될까요?', 'options': ['돌', '물', '모래', '불'], 'answer': 1}, {'category': '과학', 'question': '새는 무엇으로 날까요?', 'options': ['지느러미', '날개', '바퀴', '손'], 'answer': 1}, {'category': '과학', 'question': '물고기는 어디에서 살까요?', 'options': ['산', '하늘', '물', '사막'], 'answer': 2}, {'category': '과학', 'question': '사람은 무엇으로 숨을 쉴까요?', 'options': ['귀', '코', '팔', '무릎'], 'answer': 1}, {'category': '과학', 'question': '밤하늘에서 볼 수 있는 것은 무엇일까요?', 'options': ['별', '태양', '무지개', '벼락만'], 'answer': 0}, {'category': '과학', 'question': '비가 많이 오면 길에 생기는 것은 무엇일까요?', 'options': ['그림', '웅덩이', '책장', '풍선'], 'answer': 1}, {'category': '과학', 'question': '봄이 되면 많이 피는 것은 무엇일까요?', 'options': ['꽃', '눈사람', '얼음', '낙엽'], 'answer': 0}, {'category': '과학', 'question': '자석에 잘 붙는 것은 무엇일까요?', 'options': ['종이', '나무', '쇠', '물'], 'answer': 2}, {'category': '과학', 'question': '비가 온 뒤 하늘에 여러 색으로 보일 수 있는 것은 무엇일까요?', 'options': ['무지개', '책상', '양말', '컵'], 'answer': 0}, {'category': '과학', 'question': '해가 지면 주변은 보통 어떻게 될까요?', 'options': ['어두워진다', '더 밝아진다', '뜨거운 물이 된다', '눈이 온다'], 'answer': 0}, {'category': '과학', 'question': '바람이 불면 나뭇잎은 어떻게 될 수 있을까요?', 'options': ['흔들린다', '숨어 버린다', '숫자가 된다', '노래가 된다'], 'answer': 0}, {'category': '과학', 'question': '달은 보통 언제 더 잘 보일까요?', 'options': ['밤', '점심', '아침밥 시간', '운동할 때만'], 'answer': 0}, {'category': '과학', 'question': '물이 아주 차가워지면 무엇이 될 수 있을까요?', 'options': ['얼음', '불', '연필', '책'], 'answer': 0}, {'category': '과학', 'question': '사람의 눈은 무엇을 할 때 필요할까요?', 'options': ['보는 것', '듣는 것', '냄새 맡는 것', '걷는 것만'], 'answer': 0}, {'category': '과학', 'question': '귀는 무엇을 들을 때 쓰나요?', 'options': ['소리', '색깔', '맛', '모양만'], 'answer': 0}, {'category': '과학', 'question': '풍선에 바람을 넣으면 어떻게 될까요?', 'options': ['커진다', '작아진다', '사라진다', '얼음이 된다'], 'answer': 0}, {'category': '영어', 'question': "'apple'은 무엇일까요?", 'options': ['사과', '바나나', '우유', '책'], 'answer': 0}, {'category': '영어', 'question': "'cat'은 어떤 동물일까요?", 'options': ['강아지', '고양이', '물고기', '새'], 'answer': 1}, {'category': '영어', 'question': "'blue'는 어떤 색일까요?", 'options': ['빨강', '파랑', '노랑', '검정'], 'answer': 1}, {'category': '영어', 'question': "'one'은 숫자 몇일까요?", 'options': ['1', '2', '3', '4'], 'answer': 0}, {'category': '영어', 'question': "'sun'은 무엇일까요?", 'options': ['해', '달', '별', '구름'], 'answer': 0}, {'category': '영어', 'question': "'book'은 무엇일까요?", 'options': ['책', '공', '신발', '컵'], 'answer': 0}, {'category': '영어', 'question': "'dog'는 어떤 동물일까요?", 'options': ['토끼', '강아지', '고래', '거북이'], 'answer': 1}, {'category': '영어', 'question': "'red'는 어떤 색일까요?", 'options': ['빨강', '초록', '파랑', '하양'], 'answer': 0}]


def init_game(keep_names=True):
    old_names = st.session_state.get("players", ["플레이어 1", "플레이어 2"])
    st.session_state.players = old_names if keep_names else ["플레이어 1", "플레이어 2"]
    st.session_state.positions = [0, 0]
    st.session_state.current_player = 0
    st.session_state.game_phase = "start"
    st.session_state.current_quiz = None
    st.session_state.used_quiz_indices = []
    st.session_state.last_dice_value = None
    st.session_state.last_message = "시작 화면에서 게임을 시작해 주세요."
    st.session_state.winner = None
    st.session_state.quiz_key = 0
    st.session_state.animation_event = None
    st.session_state.play_sound = None


if "positions" not in st.session_state:
    init_game(keep_names=False)


def start_game():
    names = st.session_state.get("players", ["플레이어 1", "플레이어 2"])
    init_game(keep_names=True)
    st.session_state.players = names
    st.session_state.game_phase = "ready_to_roll"
    st.session_state.last_message = "게임이 시작되었습니다. 플레이어 1이 주사위를 굴립니다."


def default_map_path():
    for path in DEFAULT_MAP_PATHS:
        if path.exists():
            return path
    return None


def get_map_bytes(uploaded_file):
    if uploaded_file is not None:
        return uploaded_file.getvalue()
    path = default_map_path()
    if path is None:
        st.error("노선도 이미지 파일이 없습니다. line2_map.png를 GitHub 저장소에 함께 올려 주세요.")
        st.stop()
    return path.read_bytes()


def roll_dice():
    return random.randint(1, 6)


def path_between(start_idx, end_idx):
    if end_idx >= start_idx:
        return list(range(start_idx, end_idx + 1))
    return list(range(start_idx, end_idx - 1, -1))


def selected_categories():
    categories = st.session_state.get("selected_categories", ["수학", "국어", "상식", "과학"])
    return categories or ["수학", "국어", "상식", "과학"]


def get_random_quiz():
    categories = selected_categories()
    candidate_indices = [i for i, q in enumerate(QUIZZES) if q["category"] in categories]
    if not candidate_indices:
        candidate_indices = list(range(len(QUIZZES)))

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


def make_animation_event(old_positions, new_positions, player, path_indices, dice, kind, win=False):
    return {
        "id": random.randint(100000, 999999),
        "old_positions": old_positions,
        "new_positions": new_positions,
        "player": player,
        "path_indices": path_indices,
        "dice": dice,
        "kind": kind,
        "win": win,
        "sound": "win" if win else "dice",
    }


def move_forward():
    if st.session_state.game_phase != "ready_to_roll":
        return

    player = st.session_state.current_player
    old_positions = st.session_state.positions.copy()
    old_pos = old_positions[player]
    dice = roll_dice()
    new_pos = min(old_pos + dice, len(STATIONS) - 1)

    new_positions = old_positions.copy()
    new_positions[player] = new_pos
    path_indices = path_between(old_pos, new_pos)

    st.session_state.positions = new_positions
    st.session_state.last_dice_value = dice
    did_win = new_pos >= len(STATIONS) - 1

    st.session_state.animation_event = make_animation_event(
        old_positions=old_positions,
        new_positions=new_positions,
        player=player,
        path_indices=path_indices,
        dice=dice,
        kind="forward",
        win=did_win,
    )

    if did_win:
        st.session_state.game_phase = "game_over"
        st.session_state.winner = player
        st.session_state.current_quiz = None
        st.session_state.last_message = f"🎉 {st.session_state.players[player]}님이 잠실역에 도착했습니다!"
    else:
        st.session_state.current_quiz = get_random_quiz()
        st.session_state.game_phase = "answering_quiz"
        st.session_state.last_message = (
            f"{st.session_state.players[player]}님이 주사위 {dice}을/를 굴려 "
            f"{STATIONS[new_pos]}역에 도착했습니다. 사이드바에서 퀴즈를 풀어 보세요."
        )
        st.session_state.quiz_key += 1


def move_backward():
    if st.session_state.game_phase != "waiting_penalty_roll":
        return

    player = st.session_state.current_player
    old_positions = st.session_state.positions.copy()
    old_pos = old_positions[player]
    dice = roll_dice()
    new_pos = max(0, old_pos - dice)

    new_positions = old_positions.copy()
    new_positions[player] = new_pos
    path_indices = path_between(old_pos, new_pos)

    st.session_state.positions = new_positions
    st.session_state.last_dice_value = dice
    st.session_state.current_quiz = None
    st.session_state.animation_event = make_animation_event(
        old_positions=old_positions,
        new_positions=new_positions,
        player=player,
        path_indices=path_indices,
        dice=dice,
        kind="backward",
        win=False,
    )

    next_player = 1 - player
    st.session_state.current_player = next_player
    st.session_state.game_phase = "ready_to_roll"
    st.session_state.last_message = (
        f"{st.session_state.players[player]}님이 벌칙 주사위 {dice}만큼 뒤로 이동해 "
        f"{STATIONS[new_pos]}역으로 갔습니다. 이제 {st.session_state.players[next_player]}님의 차례입니다."
    )


def submit_answer(answer):
    quiz = st.session_state.current_quiz
    if quiz is None:
        return

    player = st.session_state.current_player
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


def render_board_component(map_bytes, event_for_render):
    image_b64 = base64.b64encode(map_bytes).decode("ascii")
    payload = {
        "image": f"data:image/png;base64,{image_b64}",
        "stations": STATIONS,
        "points": STATION_POINTS,
        "positions": st.session_state.positions,
        "players": st.session_state.players,
        "lastDice": st.session_state.last_dice_value,
        "phase": st.session_state.game_phase,
        "winner": st.session_state.winner,
        "tokenStyle": st.session_state.get("token_style", "기차 아이콘"),
        "soundEnabled": st.session_state.get("sound_enabled", True),
        "playSound": st.session_state.get("play_sound"),
        "event": event_for_render,
    }

    payload_json = json.dumps(payload, ensure_ascii=False)

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8" />
<style>
  :root {{
    --p1: #ef4444;
    --p2: #2563eb;
    --green: #22c55e;
    --orange: #fb923c;
  }}
  html, body {{
    margin: 0;
    padding: 0;
    background: transparent;
    font-family: Arial, 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
  }}
  .game-root {{
    width: 100%;
    box-sizing: border-box;
  }}
  .board {{
    position: relative;
    width: 100%;
    max-width: 1120px;
    margin: 0 auto;
    border-radius: 22px;
    overflow: hidden;
    background: #f8fafc;
    box-shadow: 0 14px 34px rgba(15, 23, 42, 0.17);
  }}
  .board img {{
    display: block;
    width: 100%;
    user-select: none;
    pointer-events: none;
  }}
  .token {{
    position: absolute;
    left: 0;
    top: 0;
    transform: translate(-50%, -50%);
    z-index: 20;
    transition: left 380ms cubic-bezier(.2,.85,.3,1), top 380ms cubic-bezier(.2,.85,.3,1), transform 240ms ease;
    filter: drop-shadow(0 6px 8px rgba(0,0,0,.28));
  }}
  .token.train {{
    width: 50px;
    height: 40px;
    border: 3px solid #fff;
    border-radius: 12px;
    color: #fff;
    font-weight: 900;
    display: flex;
    align-items: end;
    justify-content: center;
    padding-bottom: 3px;
    box-sizing: border-box;
  }}
  .token.train::before {{
    content: "";
    position: absolute;
    left: 9px;
    right: 9px;
    top: 7px;
    height: 11px;
    border-radius: 5px;
    background: rgba(230,245,255,.95);
  }}
  .token.train::after {{
    content: "●  ●";
    position: absolute;
    bottom: -10px;
    left: 7px;
    right: 7px;
    color: #1f2937;
    font-size: 10px;
    letter-spacing: 13px;
  }}
  .token.character {{
    width: 48px;
    height: 48px;
    border: 3px solid #fff;
    border-radius: 999px;
    color: #fff;
    font-weight: 900;
    display: flex;
    align-items: end;
    justify-content: center;
    padding-bottom: 3px;
    box-sizing: border-box;
  }}
  .token.character::before {{
    content: "•  •";
    position: absolute;
    top: 9px;
    left: 0;
    right: 0;
    text-align: center;
    color: #fff;
    font-size: 18px;
    letter-spacing: 6px;
  }}
  .token.character::after {{
    content: "⌣";
    position: absolute;
    top: 19px;
    left: 0;
    right: 0;
    text-align: center;
    color: #fff;
    font-size: 20px;
  }}
  .p1 {{ background: var(--p1); }}
  .p2 {{ background: var(--p2); }}
  .panel {{
    position: absolute;
    left: 24px;
    top: 24px;
    min-width: 245px;
    z-index: 30;
    background: rgba(255,255,255,.94);
    border: 3px solid var(--green);
    border-radius: 20px;
    box-shadow: 0 7px 18px rgba(0,0,0,.18);
    padding: 14px 16px;
    box-sizing: border-box;
  }}
  .panel-title {{
    color: #14532d;
    font-size: 19px;
    font-weight: 900;
    margin-bottom: 6px;
  }}
  .panel-row {{
    color: #111827;
    font-size: 15px;
    font-weight: 700;
  }}
  .dice {{
    position: absolute;
    right: 16px;
    top: 16px;
    width: 72px;
    height: 72px;
    border-radius: 16px;
    border: 3px solid var(--orange);
    background: #fff7ed;
    color: #9a3412;
    font-size: 44px;
    font-weight: 900;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: inset 0 0 0 2px rgba(255,255,255,.5);
  }}
  .route-line {{
    position: absolute;
    z-index: 12;
    height: 7px;
    background: rgba(239,68,68,.74);
    border-radius: 999px;
    transform-origin: left center;
    opacity: 0;
    transition: opacity 220ms ease;
  }}
  .win-card {{
    position: absolute;
    left: 50%;
    top: 9%;
    transform: translateX(-50%) scale(.94);
    z-index: 60;
    width: min(560px, 74%);
    background: linear-gradient(135deg, #fff7ed, #fef3c7);
    border: 4px solid #fbbf24;
    border-radius: 28px;
    box-shadow: 0 16px 38px rgba(0,0,0,.22);
    text-align: center;
    padding: 26px 24px;
    box-sizing: border-box;
    opacity: 0;
    pointer-events: none;
  }}
  .win-card.show {{
    opacity: 1;
    transform: translateX(-50%) scale(1);
    transition: opacity 550ms ease, transform 550ms cubic-bezier(.18,.89,.32,1.28);
  }}
  .win-title {{
    font-size: 38px;
    font-weight: 1000;
    color: #92400e;
    margin-bottom: 8px;
  }}
  .win-sub {{
    font-size: 21px;
    font-weight: 800;
    color: #1e40af;
  }}
  .start-card {{
    position: absolute;
    left: 50%;
    top: 7%;
    transform: translateX(-50%);
    z-index: 50;
    width: min(620px, 78%);
    background: linear-gradient(135deg, rgba(236,253,245,.96), rgba(239,246,255,.96));
    border: 2px solid #bfdbfe;
    border-radius: 28px;
    box-shadow: 0 14px 30px rgba(15,23,42,.16);
    padding: 24px 26px;
    box-sizing: border-box;
  }}
  .start-card h2 {{
    margin: 0 0 10px 0;
    font-size: 30px;
  }}
  .start-card p {{
    margin: 6px 0;
    font-size: 17px;
    line-height: 1.55;
  }}
  .confetti {{
    position: absolute;
    z-index: 55;
    width: 10px;
    height: 16px;
    border-radius: 2px;
    opacity: .95;
    animation-name: fall;
    animation-timing-function: linear;
    animation-fill-mode: forwards;
  }}
  @keyframes fall {{
    0% {{ transform: translateY(-80px) rotate(0deg); }}
    100% {{ transform: translateY(880px) rotate(720deg); }}
  }}
  @media (max-width: 760px) {{
    .panel {{
      left: 10px;
      top: 10px;
      min-width: 190px;
      padding: 10px 12px;
    }}
    .dice {{
      width: 54px;
      height: 54px;
      font-size: 32px;
    }}
    .token.train {{
      width: 40px;
      height: 32px;
    }}
    .token.character {{
      width: 40px;
      height: 40px;
    }}
    .start-card {{
      display: none;
    }}
  }}
</style>
</head>
<body>
<div class="game-root">
  <div class="board" id="board">
    <img id="map" src="" alt="서울 지하철 2호선 노선도">
    <div id="route-layer"></div>
    <div id="token0" class="token p1">1</div>
    <div id="token1" class="token p2">2</div>
    <div class="panel">
      <div class="panel-title">🚇 2호선 퀴즈 게임</div>
      <div class="panel-row" id="station-row">현재 위치</div>
      <div class="dice" id="dice">🎲</div>
    </div>
    <div class="start-card" id="start-card" style="display:none;">
      <h2>🚇 성수역에서 잠실역까지!</h2>
      <p>주사위를 굴리고, 도착한 역에서 퀴즈를 풀어 보세요.</p>
      <p>정답이면 한 번 더, 오답이면 벌칙 주사위로 뒤로 이동합니다.</p>
    </div>
    <div class="win-card" id="win-card">
      <div class="win-title" id="win-title">축하합니다!</div>
      <div class="win-sub">잠실역 도착!</div>
    </div>
  </div>
</div>

<script>
const payload = {payload_json};

const board = document.getElementById("board");
const map = document.getElementById("map");
const dice = document.getElementById("dice");
const tokenEls = [document.getElementById("token0"), document.getElementById("token1")];
const stationRow = document.getElementById("station-row");
const routeLayer = document.getElementById("route-layer");
const winCard = document.getElementById("win-card");
const winTitle = document.getElementById("win-title");
const startCard = document.getElementById("start-card");

map.src = payload.image;

const tokenClass = payload.tokenStyle === "캐릭터 말" ? "character" : "train";
tokenEls.forEach((el) => {{
  el.classList.remove("train", "character");
  el.classList.add(tokenClass);
}});

function sleep(ms) {{
  return new Promise(resolve => setTimeout(resolve, ms));
}}

function diceFace(value) {{
  const faces = {{1:"⚀", 2:"⚁", 3:"⚂", 4:"⚃", 5:"⚄", 6:"⚅"}};
  return faces[value] || "🎲";
}}

function stationPoint(index) {{
  const name = payload.stations[index];
  return payload.points[name];
}}

function sameStationOffset(playerIndex, positions) {{
  if (positions[0] === positions[1]) {{
    return playerIndex === 0 ? {{x: -20, y: -20}} : {{x: 20, y: 20}};
  }}
  return playerIndex === 0 ? {{x: 0, y: -22}} : {{x: 0, y: 22}};
}}

function placeToken(playerIndex, stationIndex, positionsForOverlap, overridePoint=null) {{
  const el = tokenEls[playerIndex];
  const p = overridePoint || stationPoint(stationIndex);
  const off = overridePoint ? {{x: 0, y: -22}} : sameStationOffset(playerIndex, positionsForOverlap);
  el.style.left = `calc(${{p.x}}% + ${{off.x}}px)`;
  el.style.top = `calc(${{p.y}}% + ${{off.y}}px)`;
}}

function placeAll(positions) {{
  placeToken(0, positions[0], positions);
  placeToken(1, positions[1], positions);
  stationRow.textContent = `1번: ${{payload.stations[positions[0]]}} · 2번: ${{payload.stations[positions[1]]}}`;
}}

function createRouteLine(fromIndex, toIndex) {{
  const p1 = stationPoint(fromIndex);
  const p2 = stationPoint(toIndex);
  const boardRect = board.getBoundingClientRect();
  const x1 = p1.x / 100 * boardRect.width;
  const y1 = p1.y / 100 * boardRect.height;
  const x2 = p2.x / 100 * boardRect.width;
  const y2 = p2.y / 100 * boardRect.height;
  const dx = x2 - x1;
  const dy = y2 - y1;
  const length = Math.sqrt(dx*dx + dy*dy);
  const angle = Math.atan2(dy, dx) * 180 / Math.PI;

  const line = document.createElement("div");
  line.className = "route-line";
  line.style.left = `${{x1}}px`;
  line.style.top = `${{y1 - 3}}px`;
  line.style.width = `${{length}}px`;
  line.style.transform = `rotate(${{angle}}deg)`;
  routeLayer.appendChild(line);
  requestAnimationFrame(() => line.style.opacity = "1");
  return line;
}}

function pctInterpolate(p1, p2, t) {{
  return {{
    x: p1.x + (p2.x - p1.x) * t,
    y: p1.y + (p2.y - p1.y) * t
  }};
}}

async function animateDice(finalValue) {{
  if (!finalValue) {{
    dice.textContent = "🎲";
    return;
  }}
  for (let i = 0; i < 16; i++) {{
    const v = 1 + Math.floor(Math.random() * 6);
    dice.textContent = diceFace(v);
    dice.style.transform = `rotate(${{(i % 2 === 0 ? -1 : 1) * 8}}deg) scale(1.04)`;
    await sleep(55);
  }}
  dice.style.transform = "rotate(0deg) scale(1)";
  dice.textContent = diceFace(finalValue);
}}

function playTone(kind) {{
  if (!payload.soundEnabled) return;
  try {{
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    const ctx = new AudioContext();
    const patterns = {{
      dice: [[620, .06], [760, .06], [900, .09]],
      correct: [[660, .10], [880, .12], [1040, .18]],
      wrong: [[300, .16], [220, .22]],
      win: [[523, .11], [659, .11], [784, .11], [1046, .30], [784, .12], [1046, .32]]
    }};
    let t = ctx.currentTime;
    for (const [freq, dur] of (patterns[kind] || patterns.dice)) {{
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.frequency.value = freq;
      osc.type = "sine";
      gain.gain.setValueAtTime(0.0001, t);
      gain.gain.exponentialRampToValueAtTime(0.14, t + 0.015);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(t);
      osc.stop(t + dur + 0.02);
      t += dur + 0.025;
    }}
  }} catch(e) {{}}
}}

function showConfetti() {{
  const colors = ["#ef4444", "#3b82f6", "#22c55e", "#facc15", "#a855f7", "#ec4899"];
  for (let i = 0; i < 130; i++) {{
    const piece = document.createElement("div");
    piece.className = "confetti";
    piece.style.left = `${{Math.random() * 100}}%`;
    piece.style.top = `${{-120 - Math.random() * 240}}px`;
    piece.style.background = colors[Math.floor(Math.random() * colors.length)];
    piece.style.animationDuration = `${{1.9 + Math.random() * 1.4}}s`;
    piece.style.animationDelay = `${{Math.random() * 0.6}}s`;
    piece.style.transform = `rotate(${{Math.random()*360}}deg)`;
    board.appendChild(piece);
    setTimeout(() => piece.remove(), 4200);
  }}
}}

function showWin() {{
  const winnerName = payload.winner !== null && payload.winner !== undefined ? payload.players[payload.winner] : "승리";
  winTitle.textContent = `🏆 ${{winnerName}} 승리!`;
  winCard.classList.add("show");
  showConfetti();
}}

async function animatePath(event) {{
  const player = event.player;
  const path = event.path_indices || [];
  let movingPositions = event.old_positions.slice();

  playTone(event.sound || "dice");
  await animateDice(event.dice);

  if (path.length <= 1) {{
    placeAll(event.new_positions);
  }} else {{
    for (let i = 0; i < path.length - 1; i++) {{
      createRouteLine(path[i], path[i + 1]);

      const p1 = stationPoint(path[i]);
      const p2 = stationPoint(path[i + 1]);
      const steps = 12;
      for (let s = 1; s <= steps; s++) {{
        const point = pctInterpolate(p1, p2, s / steps);
        placeToken(player, path[i], movingPositions, point);
        await sleep(32);
      }}
      movingPositions[player] = path[i + 1];
      stationRow.textContent = `이동 중: ${{payload.stations[path[i + 1]]}}`;
      await sleep(120);
    }}
    placeAll(event.new_positions);
  }}

  if (event.win) {{
    await sleep(300);
    playTone("win");
    showWin();
  }}
}}

async function main() {{
  const event = payload.event;
  if (payload.phase === "start") {{
    startCard.style.display = "block";
  }}

  if (event) {{
    placeAll(event.old_positions);
    await sleep(160);
    await animatePath(event);
  }} else {{
    placeAll(payload.positions);
    if (payload.lastDice) dice.textContent = diceFace(payload.lastDice);
    if (payload.playSound) playTone(payload.playSound);
    if (payload.phase === "game_over") showWin();
  }}
}}

if (map.complete) {{
  main();
}} else {{
  map.onload = main;
}}
</script>
</body>
</html>
"""
    components.html(html, height=790, scrolling=False)


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
        st.info("게임 시작 버튼을 누르면 시작합니다.")
        st.button("🚇 게임 시작", use_container_width=True, type="primary", on_click=start_game)

    elif phase == "ready_to_roll":
        st.button("🎲 주사위 굴리기", use_container_width=True, type="primary", on_click=move_forward)

    elif phase == "answering_quiz":
        quiz = st.session_state.current_quiz
        st.subheader("🧠 퀴즈")
        if quiz is None:
            st.warning("퀴즈가 아직 준비되지 않았습니다.")
        else:
            with st.form(f"quiz_form_{st.session_state.quiz_key}"):
                st.markdown(f"**[{quiz['category']}] {quiz['question']}**")
                answer = st.radio("정답을 고르세요.", quiz["options"], key=f"answer_{st.session_state.quiz_key}")
                submitted = st.form_submit_button("정답 제출", use_container_width=True, type="primary")
                if submitted:
                    submit_answer(answer)

    elif phase == "waiting_penalty_roll":
        st.error("오답입니다. 벌칙 주사위를 굴려 뒤로 이동하세요.")
        st.button("↩️ 벌칙 주사위 굴리기", use_container_width=True, type="primary", on_click=move_backward)

    elif phase == "game_over":
        st.success(f"🏆 우승: {st.session_state.players[st.session_state.winner]}")
        st.button("새 게임 시작", use_container_width=True, type="primary", on_click=start_game)

    st.divider()
    st.subheader("설정")

    with st.form("name_form"):
        p1 = st.text_input("플레이어 1 이름", st.session_state.players[0])
        p2 = st.text_input("플레이어 2 이름", st.session_state.players[1])
        saved = st.form_submit_button("이름 저장", use_container_width=True)
        if saved:
            st.session_state.players = [p1.strip() or "플레이어 1", p2.strip() or "플레이어 2"]

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

    st.button("게임 초기화", use_container_width=True, on_click=init_game, kwargs={"keep_names": True})


st.title("🚇 서울 지하철 2호선 퀴즈 보드게임")
st.caption("이번 버전은 Python이 프레임을 계속 다시 그리지 않고, 브라우저 안에서 JavaScript/CSS로 부드럽게 움직입니다.")

map_bytes = get_map_bytes(uploaded_map)
event_for_render = st.session_state.get("animation_event")

render_board_component(map_bytes, event_for_render)

# 같은 이동 애니메이션이 퀴즈 제출/설정 변경 때 반복 재생되지 않도록 한 번 렌더링 후 지웁니다.
if event_for_render is not None:
    st.session_state.animation_event = None

# 정답/오답 효과음도 한 번만 재생합니다.
if st.session_state.get("play_sound"):
    st.session_state.play_sound = None

if st.session_state.game_phase == "start":
    st.markdown(
        """
        <div style="padding: 24px; border-radius: 22px; background: linear-gradient(135deg, #ecfdf5, #eff6ff); border: 1px solid #bfdbfe;">
            <h2 style="margin-top:0;">🚇 성수역에서 잠실역까지!</h2>
            <p style="font-size: 18px;">
                성수에서 바로 잠실로 가지 않고, 2호선을 크게 돌아가는 긴 경로로 이동합니다.
                왼쪽 사이드바에서 게임을 시작하세요.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
elif st.session_state.game_phase == "game_over":
    st.balloons()
    winner_name = st.session_state.players[st.session_state.winner]
    st.success(f"🏆 {winner_name}님이 승리했습니다! 잠실역 도착!")
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
