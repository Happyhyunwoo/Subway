
import random
import time
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw, ImageFont


st.set_page_config(
    page_title="서울 지하철 2호선 퀴즈 게임",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_DIR = Path(__file__).parent
DEFAULT_MAP_PATH = APP_DIR / "line2_map.png"


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

QUIZZES = [
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
]


def init_game(keep_names=True):
    old_names = st.session_state.get("players", ["플레이어 1", "플레이어 2"])
    st.session_state.players = old_names if keep_names else ["플레이어 1", "플레이어 2"]
    st.session_state.positions = [0, 0]
    st.session_state.current_player = 0
    st.session_state.game_phase = "ready_to_roll"
    st.session_state.current_quiz = None
    st.session_state.used_quiz_indices = []
    st.session_state.last_dice_value = None
    st.session_state.last_message = "게임을 시작하세요. 플레이어 1이 주사위를 굴립니다."
    st.session_state.winner = None
    st.session_state.quiz_key = 0
    st.session_state.pending_action = None
    st.session_state.pending_answer = None
    st.session_state.animation_running = False


if "positions" not in st.session_state:
    init_game(keep_names=False)


def roll_dice():
    return random.randint(1, 6)


def path_between(start_idx, end_idx):
    if end_idx >= start_idx:
        return list(range(start_idx, end_idx + 1))
    return list(range(start_idx, end_idx - 1, -1))


def get_random_quiz():
    used = set(st.session_state.used_quiz_indices)
    available = [i for i in range(len(QUIZZES)) if i not in used]
    if not available:
        st.session_state.used_quiz_indices = []
        available = list(range(len(QUIZZES)))
    idx = random.choice(available)
    st.session_state.used_quiz_indices.append(idx)
    quiz = QUIZZES[idx].copy()
    quiz["quiz_id"] = idx
    return quiz


def load_map_image(uploaded_file):
    if uploaded_file is not None:
        return Image.open(uploaded_file).convert("RGBA")
    if not DEFAULT_MAP_PATH.exists():
        st.error("line2_map.png 파일이 없습니다. GitHub 저장소에 이 파일을 함께 올려 주세요.")
        st.stop()
    return Image.open(DEFAULT_MAP_PATH).convert("RGBA")


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
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def draw_token(draw, x, y, color, label, scale=1.0):
    r = max(13, int(18 * scale))
    draw.ellipse((x - r + 3, y - r + 3, x + r + 3, y + r + 3), fill=(0, 0, 0, 80))
    draw.ellipse((x - r, y - r, x + r, y + r), fill=color, outline=(255, 255, 255, 255), width=max(2, int(3 * scale)))
    font = get_font(max(14, int(18 * scale)), bold=True)
    bbox = draw.textbbox((0, 0), label, font=font)
    draw.text((x - (bbox[2] - bbox[0]) / 2, y - (bbox[3] - bbox[1]) / 2 - 1), label, font=font, fill=(255, 255, 255, 255))


def draw_die_face(draw, x, y, size, value):
    radius = max(8, size // 7)
    draw.rounded_rectangle((x + 4, y + 4, x + size + 4, y + size + 4), radius=radius, fill=(0, 0, 0, 60))
    draw.rounded_rectangle((x, y, x + size, y + size), radius=radius, fill=(255, 250, 240, 255), outline=(251, 146, 60, 255), width=max(2, size // 24))
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
    w, h = int(248 * scale), int(102 * scale)
    draw.rounded_rectangle((x0 + 4, y0 + 4, x0 + w + 4, y0 + h + 4), radius=int(16 * scale), fill=(0, 0, 0, 55))
    draw.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=int(16 * scale), fill=(255, 255, 255, 238), outline=(34, 197, 94, 255), width=max(2, int(3 * scale)))
    font_title = get_font(max(13, int(17 * scale)), bold=True)
    font_small = get_font(max(11, int(13 * scale)), bold=False)
    draw.text((x0 + int(14 * scale), y0 + int(14 * scale)), "주사위", font=font_title, fill=(20, 83, 45, 255))
    if moving_text:
        draw.text((x0 + int(14 * scale), y0 + int(61 * scale)), moving_text, font=font_small, fill=(17, 24, 39, 255))
    die_size = int(64 * scale)
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


def draw_board(base_img, positions, dice_value=None, moving_text=None, moving_token=None, path_indices=None, highlight_upto=None):
    img = base_img.copy()
    draw = ImageDraw.Draw(img, "RGBA")
    if path_indices:
        draw_path_highlight(draw, img, path_indices, upto=highlight_upto)
    token_colors = [(255, 75, 75, 255), (59, 130, 246, 255)]
    scale = img.width / 1000
    token_positions = [station_xy(img, positions[0]), station_xy(img, positions[1])]
    if moving_token is not None:
        moving_player, xy = moving_token
        token_positions[moving_player] = xy
    same_station = positions[0] == positions[1] and moving_token is None
    for i, (x, y) in enumerate(token_positions):
        if same_station:
            dx = -15 if i == 0 else 15
            dy = -16 if i == 0 else 16
        else:
            dx = 0
            dy = -17 if i == 0 else 17
        if moving_token is not None and i == moving_token[0]:
            dx = 0
            dy = -18
        draw_token(draw, x + int(dx * scale), y + int(dy * scale), token_colors[i], str(i + 1), scale=scale)
    draw_info_panel(draw, img, dice_value=dice_value, moving_text=moving_text)
    return img.convert("RGB")


def interpolate(p1, p2, t):
    return int(p1[0] + (p2[0] - p1[0]) * t), int(p1[1] + (p2[1] - p1[1]) * t)


def animate_move(placeholder, base_img, old_positions, player_index, path_indices, dice_value, direction_text):
    st.session_state.animation_running = True
    for _ in range(12):
        frame = draw_board(base_img, old_positions, random.randint(1, 6), "주사위 굴리는 중")
        placeholder.image(frame, use_container_width=True)
        time.sleep(0.07)

    frame = draw_board(base_img, old_positions, dice_value, f"결과: {dice_value}")
    placeholder.image(frame, use_container_width=True)
    time.sleep(0.2)

    if len(path_indices) >= 2:
        for seg_i in range(len(path_indices) - 1):
            start_xy = station_xy(base_img, path_indices[seg_i])
            end_xy = station_xy(base_img, path_indices[seg_i + 1])
            for step in range(1, 11):
                x, y = interpolate(start_xy, end_xy, step / 10)
                frame = draw_board(base_img, old_positions, dice_value, direction_text, (player_index, (x, y)), path_indices, seg_i + 1)
                placeholder.image(frame, use_container_width=True)
                time.sleep(0.055)

    final_positions = old_positions.copy()
    final_positions[player_index] = path_indices[-1]
    frame = draw_board(base_img, final_positions, dice_value, f"도착: {STATIONS[path_indices[-1]]}", path_indices=path_indices)
    placeholder.image(frame, use_container_width=True)
    time.sleep(0.25)
    st.session_state.animation_running = False


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

    if new_pos >= len(STATIONS) - 1:
        st.session_state.game_phase = "game_over"
        st.session_state.winner = player
        st.session_state.current_quiz = None
        st.session_state.last_message = f"🎉 {st.session_state.players[player]}님이 잠실역에 도착했습니다!"
    else:
        st.session_state.current_quiz = get_random_quiz()
        st.session_state.game_phase = "answering_quiz"
        st.session_state.last_message = f"{st.session_state.players[player]}님이 주사위 {dice}을/를 굴려 {STATIONS[new_pos]}역에 도착했습니다. 사이드바에서 퀴즈를 풀어 보세요."
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

    next_player = 1 - player
    st.session_state.current_player = next_player
    st.session_state.game_phase = "ready_to_roll"
    st.session_state.last_message = f"{st.session_state.players[player]}님이 벌칙 주사위 {dice}만큼 뒤로 이동해 {STATIONS[new_pos]}역으로 갔습니다. 이제 {st.session_state.players[next_player]}님의 차례입니다."


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
    else:
        st.session_state.game_phase = "waiting_penalty_roll"
        st.session_state.last_message = f"❌ 아쉽지만 정답은 '{correct}'입니다. {st.session_state.players[player]}님은 사이드바에서 벌칙 주사위를 굴려 주세요."


# ============================================================
# Sidebar first: Streamlit Cloud에서도 조작 패널이 항상 보이도록 구성
# ============================================================
with st.sidebar:
    st.title("🎲 게임 진행")

    st.write(f"현재 차례: **{st.session_state.players[st.session_state.current_player]}**")
    st.write(f"마지막 주사위: **{st.session_state.last_dice_value if st.session_state.last_dice_value else '-'}**")
    st.write(f"1번 말: **{STATIONS[st.session_state.positions[0]]}**")
    st.write(f"2번 말: **{STATIONS[st.session_state.positions[1]]}**")

    st.divider()

    phase = st.session_state.game_phase

    if phase == "ready_to_roll":
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
            init_game(keep_names=True)
            st.rerun()

    st.divider()
    st.subheader("설정")

    with st.form("name_form"):
        p1 = st.text_input("플레이어 1 이름", st.session_state.players[0])
        p2 = st.text_input("플레이어 2 이름", st.session_state.players[1])
        if st.form_submit_button("이름 저장", use_container_width=True):
            st.session_state.players = [p1.strip() or "플레이어 1", p2.strip() or "플레이어 2"]
            st.rerun()

    uploaded_map = st.file_uploader("다른 노선도 이미지 사용", type=["png", "jpg", "jpeg"])

    if st.button("게임 초기화", use_container_width=True):
        init_game(keep_names=True)
        st.rerun()


# ============================================================
# Main page
# ============================================================
st.title("🚇 서울 지하철 2호선 퀴즈 보드게임")
st.caption("왼쪽 사이드바에서 주사위와 퀴즈를 조작하고, 메인 화면에서 말 이동을 확인합니다.")

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
    board = draw_board(base_map, st.session_state.positions, st.session_state.last_dice_value, "현재 위치")
    board_placeholder.image(board, use_container_width=True)

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
