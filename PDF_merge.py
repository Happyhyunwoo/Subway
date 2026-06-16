import base64
import json
import random
import time
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

STATIONS = [
    "성수", "뚝섬", "한양대", "왕십리", "상왕십리", "신당", "동대문역사문화공원",
    "을지로4가", "을지로3가", "을지로입구", "시청", "충정로", "아현", "이대",
    "신촌", "홍대입구", "합정", "당산", "영등포구청", "문래", "신도림", "대림",
    "구로디지털단지", "신대방", "신림", "봉천", "서울대입구", "낙성대", "사당",
    "방배", "서초", "교대", "강남", "역삼", "선릉", "삼성", "종합운동장",
    "신천", "잠실"
]

ORIGINAL_WIDTH = 1366
ORIGINAL_HEIGHT = 917

STATION_PIXELS = {
    "성수": (1147, 385), "뚝섬": (1099, 320), "한양대": (1045, 292),
    "왕십리": (1007, 247), "상왕십리": (928, 247), "신당": (854, 228),
    "동대문역사문화공원": (781, 247), "을지로4가": (694, 247), "을지로3가": (615, 247),
    "을지로입구": (540, 246), "시청": (474, 246), "충정로": (399, 247),
    "아현": (324, 247), "이대": (291, 289), "신촌": (264, 380),
    "홍대입구": (264, 445), "합정": (264, 501), "당산": (264, 568),
    "영등포구청": (264, 634), "문래": (264, 694), "신도림": (264, 757),
    "대림": (266, 815), "구로디지털단지": (278, 853), "신대방": (337, 869),
    "신림": (390, 869), "봉천": (445, 869), "서울대입구": (498, 869),
    "낙성대": (556, 869), "사당": (649, 852), "방배": (713, 869),
    "서초": (780, 869), "교대": (849, 869), "강남": (918, 850),
    "역삼": (978, 869), "선릉": (1043, 869), "삼성": (1111, 845),
    "종합운동장": (1141, 781), "신천": (1144, 719), "잠실": (1144, 640),
}

STATION_POINTS = {
    name: {"x": x / ORIGINAL_WIDTH * 100, "y": y / ORIGINAL_HEIGHT * 100}
    for name, (x, y) in STATION_PIXELS.items()
}

SPECIAL_EVENTS = {
    "홍대입구": {"type": "bonus", "msg": "🎵 홍대 거리 이벤트! 주사위를 한 번 더 굴립니다.", "extra_roll": True},
    "강남": {"type": "bonus", "msg": "💰 강남 특수! 2칸 추가 전진!", "move": 2},
    "신도림": {"type": "penalty", "msg": "🚧 신도림 환승 혼잡! 1칸 뒤로 이동합니다.", "move": -1},
    "왕십리": {"type": "bonus", "msg": "🎭 왕십리 축제! 다음 퀴즈 면제 + 1칸 전진!", "skip_quiz": True, "move": 1},
    "사당": {"type": "penalty", "msg": "⚠️ 사당 혼잡! 이번 턴 퀴즈 2문제 도전!", "double_quiz": True},
}

QUIZZES = [
    {'category': '수학', 'question': '3 + 2는 얼마일까요?', 'options': ['4', '5', '6', '7'], 'answer': 1},
    {'category': '수학', 'question': '10에서 4를 빼면 얼마일까요?', 'options': ['5', '6', '7', '8'], 'answer': 1},
    {'category': '수학', 'question': '1, 2, 3 다음 수는 무엇일까요?', 'options': ['4', '5', '6', '7'], 'answer': 0},
    {'category': '수학', 'question': '사과가 2개 있고 2개를 더 받으면 모두 몇 개일까요?', 'options': ['2개', '3개', '4개', '5개'], 'answer': 2},
    {'category': '수학', 'question': '5는 4보다 어떻게 될까요?', 'options': ['작다', '같다', '크다', '없다'], 'answer': 2},
    {'category': '수학', 'question': '네모의 변은 몇 개일까요?', 'options': ['2개', '3개', '4개', '5개'], 'answer': 2},
    {'category': '수학', 'question': '시계 숫자 12 다음에 오는 숫자는 무엇일까요?', 'options': ['1', '2', '11', '13'], 'answer': 0},
    {'category': '수학', 'question': '7에서 1을 더하면 얼마일까요?', 'options': ['6', '7', '8', '9'], 'answer': 2},
    {'category': '수학', 'question': '두 손의 손가락을 모두 합치면 몇 개일까요?', 'options': ['8개', '9개', '10개', '11개'], 'answer': 2},
    {'category': '수학', 'question': '2 + 6은 얼마일까요?', 'options': ['6', '7', '8', '9'], 'answer': 2},
    {'category': '수학', 'question': '9에서 3을 빼면 얼마일까요?', 'options': ['5', '6', '7', '8'], 'answer': 1},
    {'category': '수학', 'question': '4와 4를 합치면 얼마일까요?', 'options': ['6', '7', '8', '9'], 'answer': 2},
    {'category': '국어', 'question': "'가, 나, 다' 다음 글자는 무엇일까요?", 'options': ['라', '마', '바', '사'], 'answer': 0},
    {'category': '국어', 'question': "'사과'의 첫 글자는 무엇일까요?", 'options': ['사', '과', '수', '가'], 'answer': 0},
    {'category': '국어', 'question': "'하늘'과 반대 느낌의 말로 알맞은 것은 무엇일까요?", 'options': ['구름', '땅', '파랑', '새'], 'answer': 1},
    {'category': '국어', 'question': "다음 중 동물 이름은 무엇일까요?", 'options': ['의자', '토끼', '연필', '창문'], 'answer': 1},
    {'category': '국어', 'question': "'크다'와 반대말은 무엇일까요?", 'options': ['작다', '높다', '멀다', '빠르다'], 'answer': 0},
    {'category': '국어', 'question': "다음 중 색깔 이름은 무엇일까요?", 'options': ['빨강', '책상', '구름', '기차'], 'answer': 0},
    {'category': '상식', 'question': '대한민국의 수도는 어디일까요?', 'options': ['서울', '부산', '제주', '대전'], 'answer': 0},
    {'category': '상식', 'question': '비가 올 때 쓰는 것은 무엇일까요?', 'options': ['우산', '연필', '베개', '장갑'], 'answer': 0},
    {'category': '상식', 'question': '지하철은 어디를 달릴까요?', 'options': ['하늘', '물속', '땅 위와 땅 아래', '나무 위'], 'answer': 2},
    {'category': '상식', 'question': '빨간불일 때 길을 건너면 될까요?', 'options': ['네', '아니요', '가끔', '뛰어서'], 'answer': 1},
    {'category': '상식', 'question': '소방관은 무엇을 끌까요?', 'options': ['불', '자동차', '비', '바람'], 'answer': 0},
    {'category': '과학', 'question': '하늘에서 낮에 밝게 빛나는 것은 무엇일까요?', 'options': ['달', '별', '해', '구름'], 'answer': 2},
    {'category': '과학', 'question': '식물은 자라려면 무엇이 필요할까요?', 'options': ['물', '장난감', '텔레비전', '베개'], 'answer': 0},
    {'category': '과학', 'question': '얼음이 녹으면 무엇이 될까요?', 'options': ['돌', '물', '모래', '불'], 'answer': 1},
    {'category': '과학', 'question': '새는 무엇으로 날까요?', 'options': ['지느러미', '날개', '바퀴', '손'], 'answer': 1},
    {'category': '과학', 'question': '자석에 잘 붙는 것은 무엇일까요?', 'options': ['종이', '나무', '쇠', '물'], 'answer': 2},
    {'category': '영어', 'question': "'apple'은 무엇일까요?", 'options': ['사과', '바나나', '우유', '책'], 'answer': 0},
    {'category': '영어', 'question': "'cat'은 어떤 동물일까요?", 'options': ['강아지', '고양이', '물고기', '새'], 'answer': 1},
    {'category': '영어', 'question': "'blue'는 어떤 색일까요?", 'options': ['빨강', '파랑', '노랑', '검정'], 'answer': 1},
    {'category': '영어', 'question': "'sun'은 무엇일까요?", 'options': ['해', '달', '별', '구름'], 'answer': 0},
    {'category': '영어', 'question': "'dog'는 어떤 동물일까요?", 'options': ['토끼', '강아지', '고래', '거북이'], 'answer': 1},
]


def init_game(keep_name=True):
    old_name = st.session_state.get("player_name", "플레이어")
    st.session_state.player_name = old_name if keep_name else "플레이어"
    st.session_state.position = 0
    st.session_state.game_phase = "start"
    st.session_state.current_quiz = None
    st.session_state.quiz_queue = []
    st.session_state.used_quiz_indices = []
    st.session_state.last_dice_value = None
    st.session_state.last_message = "왼쪽 사이드바에서 게임을 시작하세요."
    st.session_state.winner = False
    st.session_state.quiz_key = 0
    st.session_state.animation_event = None
    st.session_state.play_sound = None
    st.session_state.score = 0
    st.session_state.turns = 0
    st.session_state.correct_streak = 0
    st.session_state.extra_roll = False
    st.session_state.skip_quiz = False


if "position" not in st.session_state:
    init_game(keep_name=False)


def start_game():
    name = st.session_state.get("player_name", "플레이어")
    init_game(keep_name=True)
    st.session_state.player_name = name
    st.session_state.game_phase = "ready_to_roll"
    st.session_state.last_message = f"🚇 {name}님, 게임이 시작되었습니다! 주사위를 굴려 보세요."


def get_map_bytes():
    for fname in ["line2_map-3.jpg", "line2_map.png", "line2_map_smooth.png"]:
        p = APP_DIR / fname
        if p.exists():
            return p.read_bytes()
    st.error("노선도 이미지 파일이 없습니다. line2_map-3.jpg 파일을 같은 폴더에 놓아 주세요.")
    st.stop()


def selected_categories():
    cats = st.session_state.get("selected_categories", ["수학", "국어", "상식", "과학", "영어"])
    return cats or ["수학", "국어", "상식", "과학", "영어"]


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


def roll_dice_value():
    streak = st.session_state.get("correct_streak", 0)
    dice = random.randint(1, 6)
    if streak >= 3 and random.random() < 0.2:
        dice = max(dice, random.randint(1, 6))
    return dice


def apply_special_event(station_name, pos):
    ev = SPECIAL_EVENTS.get(station_name)
    if not ev:
        return pos, None, False, False
    msg = ev["msg"]
    extra = ev.get("extra_roll", False)
    skip = ev.get("skip_quiz", False)
    move = ev.get("move", 0)
    double_q = ev.get("double_quiz", False)
    new_pos = max(0, min(pos + move, len(STATIONS) - 1))
    if double_q:
        st.session_state.quiz_queue = [get_random_quiz(), get_random_quiz()]
    return new_pos, msg, extra, skip


def move_forward():
    if st.session_state.game_phase not in ("ready_to_roll",):
        return
    old_pos = st.session_state.position
    dice = roll_dice_value()
    raw_pos = min(old_pos + dice, len(STATIONS) - 1)

    station_name = STATIONS[raw_pos]
    new_pos, ev_msg, extra_roll, skip_quiz = apply_special_event(station_name, raw_pos)

    st.session_state.position = new_pos
    st.session_state.last_dice_value = dice
    st.session_state.turns += 1
    st.session_state.extra_roll = extra_roll
    st.session_state.skip_quiz = skip_quiz

    path_indices = list(range(old_pos, new_pos + 1)) if new_pos >= old_pos else list(range(old_pos, new_pos - 1, -1))
    did_win = new_pos >= len(STATIONS) - 1

    st.session_state.animation_event = {
        "id": random.randint(100000, 999999),
        "position": new_pos,
        "path_indices": path_indices,
        "dice": dice,
        "win": did_win,
        "sound": "win" if did_win else "dice",
    }

    if did_win:
        st.session_state.game_phase = "game_over"
        st.session_state.winner = True
        st.session_state.last_message = (
            f"🎉 {st.session_state.player_name}님이 잠실역에 도착했습니다! "
            f"총 {st.session_state.turns}턴, {st.session_state.score}점 획득!"
        )
        return

    base_msg = (
        f"🎲 주사위 **{dice}** → **{STATIONS[new_pos]}**역 도착! "
        f"(현재 {new_pos + 1}/{len(STATIONS)})"
    )
    if ev_msg:
        base_msg += f"\n\n{ev_msg}"

    if skip_quiz:
        st.session_state.game_phase = "ready_to_roll"
        st.session_state.correct_streak = 0
        base_msg += "\n\n✨ 퀴즈 면제! 계속 진행합니다."
    elif st.session_state.quiz_queue:
        st.session_state.current_quiz = st.session_state.quiz_queue.pop(0)
        st.session_state.game_phase = "answering_quiz"
        base_msg += "\n\n📝 사이드바에서 퀴즈를 풀어 보세요!"
    else:
        st.session_state.current_quiz = get_random_quiz()
        st.session_state.game_phase = "answering_quiz"
        base_msg += "\n\n📝 사이드바에서 퀴즈를 풀어 보세요!"

    st.session_state.last_message = base_msg
    st.session_state.quiz_key += 1


def move_backward():
    if st.session_state.game_phase != "waiting_penalty_roll":
        return
    old_pos = st.session_state.position
    dice = random.randint(1, 6)
    new_pos = max(0, old_pos - dice)
    st.session_state.position = new_pos
    st.session_state.last_dice_value = dice
    st.session_state.current_quiz = None
    st.session_state.correct_streak = 0

    path_indices = list(range(old_pos, new_pos - 1, -1))
    st.session_state.animation_event = {
        "id": random.randint(100000, 999999),
        "position": new_pos,
        "path_indices": path_indices,
        "dice": dice,
        "win": False,
        "sound": "wrong",
    }

    st.session_state.game_phase = "ready_to_roll"
    st.session_state.last_message = (
        f"😢 벌칙 주사위 **{dice}** → **{STATIONS[new_pos]}**역으로 후퇴! "
        f"다시 주사위를 굴려 보세요."
    )


def submit_answer(answer):
    quiz = st.session_state.current_quiz
    if quiz is None:
        return
    correct = quiz["options"][quiz["answer"]]
    if answer == correct:
        st.session_state.score += 10
        st.session_state.correct_streak += 1
        streak = st.session_state.correct_streak
        bonus_msg = ""
        if streak >= 3:
            st.session_state.score += 5
            bonus_msg = f" 🔥 연속 {streak}정답 보너스 +5점!"
        st.session_state.current_quiz = None
        st.session_state.play_sound = "correct"

        if st.session_state.quiz_queue:
            st.session_state.current_quiz = st.session_state.quiz_queue.pop(0)
            st.session_state.game_phase = "answering_quiz"
            st.session_state.last_message = f"✅ 정답! (+10점{bonus_msg})\n\n📝 다음 퀴즈를 풀어 보세요!"
        else:
            extra = st.session_state.get("extra_roll", False)
            if extra:
                st.session_state.extra_roll = False
                st.session_state.game_phase = "ready_to_roll"
                st.session_state.last_message = f"✅ 정답! (+10점{bonus_msg})\n\n🎲 보너스 주사위를 한 번 더 굴립니다!"
            else:
                st.session_state.game_phase = "ready_to_roll"
                st.session_state.last_message = f"✅ 정답! (+10점{bonus_msg})\n\n다시 주사위를 굴려 보세요."
        st.session_state.quiz_key += 1
    else:
        st.session_state.correct_streak = 0
        st.session_state.play_sound = "wrong"
        st.session_state.game_phase = "waiting_penalty_roll"
        st.session_state.last_message = (
            f"❌ 아쉽지만 정답은 **'{correct}'** 입니다.\n\n"
            f"사이드바에서 벌칙 주사위를 굴려 주세요!"
        )
        st.session_state.current_quiz = None


def render_board_component(map_bytes):
    ext = "jpeg" if str(get_map_bytes.__code__.co_filename).endswith(".jpg") else "png"
    # 이미지 확장자 자동 감지
    img_ext = "jpeg"
    for fname in ["line2_map-3.jpg"]:
        if (APP_DIR / fname).exists():
            img_ext = "jpeg"
            break
        img_ext = "png"

    image_b64 = base64.b64encode(map_bytes).decode("ascii")
    payload = {
        "image": f"data:image/{img_ext};base64,{image_b64}",
        "stations": STATIONS,
        "points": STATION_POINTS,
        "position": st.session_state.position,
        "playerName": st.session_state.player_name,
        "lastDice": st.session_state.last_dice_value,
        "phase": st.session_state.game_phase,
        "winner": st.session_state.winner,
        "score": st.session_state.score,
        "turns": st.session_state.turns,
        "streak": st.session_state.correct_streak,
        "soundEnabled": st.session_state.get("sound_enabled", True),
        "playSound": st.session_state.get("play_sound"),
        "event": st.session_state.animation_event,
        "specialStations": list(SPECIAL_EVENTS.keys()),
    }
    payload_json = json.dumps(payload, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #0a0a1a; font-family: 'Noto Sans KR', sans-serif; overflow: hidden; }}
  #board-container {{
    position: relative; width: 100%; padding-bottom: 69%;
    overflow: hidden; border-radius: 12px;
    box-shadow: 0 0 30px rgba(0,200,100,0.3);
  }}
  #board-img {{
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    object-fit: contain;
  }}
  .token {{
    position: absolute;
    width: 36px; height: 36px;
    transform: translate(-50%, -50%);
    border-radius: 50%;
    border: 3px solid #fff;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
    box-shadow: 0 0 12px rgba(255,255,255,0.8);
    transition: left 0.45s cubic-bezier(.68,-0.55,.27,1.55),
                top  0.45s cubic-bezier(.68,-0.55,.27,1.55);
    z-index: 10;
    animation: tokenPulse 1.5s ease-in-out infinite;
    background-color: #2ecc71;
  }}
  @keyframes tokenPulse {{
    0%,100% {{ box-shadow: 0 0 10px 3px rgba(46,204,113,0.8); }}
    50%      {{ box-shadow: 0 0 22px 10px rgba(46,204,113,0.3); }}
  }}
  .station-dot {{
    position: absolute;
    width: 10px; height: 10px;
    border-radius: 50%;
    background: rgba(255,255,255,0.12);
    transform: translate(-50%, -50%);
    transition: all 0.3s;
    z-index: 5;
  }}
  .station-dot.special {{
    background: rgba(255,200,0,0.5);
    box-shadow: 0 0 8px rgba(255,200,0,0.7);
    width: 14px; height: 14px;
    animation: specialGlow 2s ease-in-out infinite;
  }}
  @keyframes specialGlow {{
    0%,100% {{ transform: translate(-50%,-50%) scale(1); }}
    50%      {{ transform: translate(-50%,-50%) scale(1.5); }}
  }}
  .station-dot.active {{
    background: rgba(46,204,113,0.7);
    box-shadow: 0 0 12px rgba(46,204,113,0.9);
    width: 14px; height: 14px;
  }}
  .station-label {{
    position: absolute;
    transform: translate(-50%, -210%);
    background: rgba(0,0,0,0.88);
    color: #2ecc71;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 12px;
    white-space: nowrap;
    z-index: 15;
    pointer-events: none;
    border: 1px solid #2ecc71;
    animation: labelPop 0.4s ease-out;
  }}
  @keyframes labelPop {{
    0%   {{ opacity:0; transform: translate(-50%,-185%) scale(0.8); }}
    100% {{ opacity:1; transform: translate(-50%,-210%) scale(1); }}
  }}
  .dice-display {{
    position: absolute; bottom: 12px; right: 12px;
    background: rgba(0,0,0,0.75); border: 2px solid #2ecc71;
    border-radius: 10px; padding: 6px 12px;
    color: #fff; font-size: 14px; z-index: 20;
  }}
  .score-display {{
    position: absolute; top: 12px; right: 12px;
    background: rgba(0,0,0,0.75); border: 2px solid #f39c12;
    border-radius: 10px; padding: 6px 12px;
    color: #f1c40f; font-size: 13px; font-weight: bold; z-index: 20;
  }}
  .progress-bar-wrap {{
    position: absolute; bottom: 0; left: 0; right: 0; height: 6px;
    background: rgba(255,255,255,0.1); z-index: 20;
  }}
  .progress-bar {{
    height: 100%;
    background: linear-gradient(90deg, #2ecc71, #f1c40f);
    transition: width 0.7s ease;
  }}
  .win-overlay {{
    display: none; position: absolute; inset: 0;
    background: rgba(0,0,0,0.82);
    align-items: center; justify-content: center;
    flex-direction: column; z-index: 50;
    border-radius: 12px;
  }}
  .win-overlay.show {{ display: flex; }}
  .win-text {{
    color: #f1c40f; font-size: 2.8em; font-weight: bold;
    text-align: center; animation: winAnim 0.6s ease-out;
  }}
  @keyframes winAnim {{
    0%   {{ transform: scale(0.4) rotate(-15deg); opacity: 0; }}
    100% {{ transform: scale(1)   rotate(0deg);   opacity: 1; }}
  }}
</style>
</head>
<body>
<div id="board-container">
  <img id="board-img" src="" alt="노선도">
  <div id="token-p0" class="token">🚃</div>
  <div id="station-label" class="station-label" style="display:none"></div>
  <div class="score-display" id="score-display">점수: 0 | 턴: 0</div>
  <div class="dice-display" id="dice-display">🎲 −</div>
  <div class="progress-bar-wrap"><div class="progress-bar" id="progress-bar" style="width:0%"></div></div>
  <div class="win-overlay" id="win-overlay">
    <div class="win-text">🎉 잠실 도착! 🎉</div>
    <div style="color:#fff;margin-top:14px;font-size:1.3em" id="win-details"></div>
  </div>
</div>
<script id="data-script" type="application/json">{payload_json}</script>
<script>
(function() {{
  const d = JSON.parse(document.getElementById('data-script').textContent);
  const img = document.getElementById('board-img');
  img.src = d.image;

  const container = document.getElementById('board-container');
  const token     = document.getElementById('token-p0');
  const label     = document.getElementById('station-label');
  const diceDisp  = document.getElementById('dice-display');
  const scoreDisp = document.getElementById('score-display');
  const progressBar = document.getElementById('progress-bar');
  const winOverlay  = document.getElementById('win-overlay');

  function placeToken(posIdx) {{
    const name = d.stations[posIdx];
    const pt   = d.points[name];
    if (!pt) return;
    token.style.left = pt.x + '%';
    token.style.top  = pt.y + '%';
    label.textContent  = name;
    label.style.left   = pt.x + '%';
    label.style.top    = pt.y + '%';
    label.style.display = 'block';
  }}

  // 역 점 그리기
  d.stations.forEach((name, i) => {{
    const pt = d.points[name];
    if (!pt) return;
    const dot = document.createElement('div');
    let cls = 'station-dot';
    if (d.specialStations && d.specialStations.includes(name)) cls += ' special';
    if (i === d.position) cls += ' active';
    dot.className = cls;
    dot.style.left = pt.x + '%';
    dot.style.top  = pt.y + '%';
    dot.title = name;
    container.appendChild(dot);
  }});

  diceDisp.textContent  = d.lastDice ? '🎲 ' + d.lastDice : '🎲 −';
  scoreDisp.textContent = '점수: ' + (d.score||0) + ' | 턴: ' + (d.turns||0);
  const pct = d.stations.length > 1 ? (d.position / (d.stations.length - 1) * 100).toFixed(1) : 0;
  progressBar.style.width = pct + '%';

  // 스텝 애니메이션
  const ev = d.event;
  if (ev && ev.path_indices && ev.path_indices.length > 1) {{
    let step = 0;
    const path = ev.path_indices;
    function animStep() {{
      if (step >= path.length) {{ placeToken(d.position); return; }}
      placeToken(path[step]);
      step++;
      setTimeout(animStep, 230);
    }}
    animStep();
  }} else {{
    placeToken(d.position);
  }}

  if (d.winner) {{
    winOverlay.classList.add('show');
    document.getElementById('win-details').textContent =
      '총 ' + (d.turns||0) + '턴 · ' + (d.score||0) + '점';
  }}

  // 효과음
  if (d.soundEnabled && d.playSound) {{
    try {{
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      function beep(freq, dur, type='sine', vol=0.3) {{
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain); gain.connect(ctx.destination);
        osc.type = type; osc.frequency.value = freq;
        gain.gain.setValueAtTime(vol, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + dur);
        osc.start(); osc.stop(ctx.currentTime + dur);
      }}
      if (d.playSound === 'dice')    {{ beep(440,0.12); setTimeout(()=>beep(660,0.12),110); }}
      if (d.playSound === 'correct') {{ beep(523,0.1); setTimeout(()=>beep(659,0.1),100); setTimeout(()=>beep(784,0.25),200); }}
      if (d.playSound === 'wrong')   {{ beep(200,0.3,'sawtooth',0.2); }}
      if (d.playSound === 'win')     {{ [523,659,784,1047].forEach((f,i)=>setTimeout(()=>beep(f,0.3),i*150)); }}
    }} catch(e) {{}}
  }}
}})();
</script>
</body>
</html>"""

    st.session_state.play_sound = None
    st.session_state.animation_event = None
    components.html(html, height=700, scrolling=False)


# ═══════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════
with st.sidebar:
    st.title("🚇 지하철 퀴즈 게임")
    st.caption("서울 2호선 · 1인용")

    st.session_state.player_name = st.text_input(
        "플레이어 이름",
        value=st.session_state.get("player_name", "플레이어"),
        key="name_input"
    )

    st.markdown("---")
    st.subheader("📚 퀴즈 카테고리")
    all_cats = ["수학", "국어", "상식", "과학", "영어"]
    if "selected_categories" not in st.session_state:
        st.session_state.selected_categories = all_cats[:]
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
        if st.button("🎮 시작", use_container_width=True):
            start_game()
            st.rerun()
    with col2:
        if st.button("🔄 리셋", use_container_width=True):
            init_game(keep_name=True)
            st.rerun()

    st.markdown("---")
    phase = st.session_state.game_phase

    if phase == "ready_to_roll":
        st.subheader("🎲 주사위")
        streak = st.session_state.correct_streak
        if streak >= 3:
            st.success(f"🔥 연속 {streak}정답! 보너스 확률 활성화!")
        if st.button("🎲 주사위 굴리기!", use_container_width=True, type="primary"):
            move_forward()
            st.rerun()

    elif phase == "waiting_penalty_roll":
        st.subheader("😱 벌칙 주사위")
        st.error("틀렸습니다! 벌칙 주사위로 뒤로 이동합니다.")
        if st.button("🎲 벌칙 주사위 굴리기", use_container_width=True):
            move_backward()
            st.rerun()

    elif phase == "answering_quiz":
        quiz = st.session_state.current_quiz
        if quiz:
            remaining = len(st.session_state.quiz_queue)
            title = "📝 퀴즈"
            if remaining > 0:
                title += f" (이후 {remaining}문제 더)"
            st.subheader(title)
            st.info(f"[{quiz['category']}] {quiz['question']}")
            for opt in quiz["options"]:
                if st.button(opt, key=f"opt_{opt}_{st.session_state.quiz_key}", use_container_width=True):
                    submit_answer(opt)
                    st.rerun()

    elif phase == "game_over":
        st.balloons()
        st.success("🎉 게임 클리어!")
        st.metric("최종 점수", st.session_state.score)
        st.metric("총 턴 수", st.session_state.turns)
        if st.button("🔄 다시 하기", use_container_width=True, type="primary"):
            init_game(keep_name=True)
            st.rerun()

    st.markdown("---")
    pos   = st.session_state.position
    total = len(STATIONS)
    st.subheader("📊 현황")
    st.progress(pos / (total - 1) if total > 1 else 0)
    st.caption(f"📍 현재: **{STATIONS[pos]}** ({pos+1}/{total}역)")
    st.caption(f"🏆 점수: **{st.session_state.score}점** | 🔥 스트릭: **{st.session_state.correct_streak}**")

    with st.expander("⭐ 특수역 안내"):
        for stn, ev in SPECIAL_EVENTS.items():
            icon = "🎁" if ev["type"] == "bonus" else "⚠️"
            st.caption(f"{icon} **{stn}**: {ev['msg']}")


# ═══════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════
st.title("🚇 서울 2호선 지하철 퀴즈 게임")

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

map_bytes = get_map_bytes()
render_board_component(map_bytes)
