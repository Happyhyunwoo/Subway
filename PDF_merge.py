import base64
import json
import random
import time
from pathlib import Path
from urllib.parse import quote

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

def svg_data_uri(svg_markup: str) -> str:
    return "data:image/svg+xml;utf8," + quote(svg_markup)


def build_train_svg(label: str, kind: str, body: str, stripe: str, nose: str, outline: str) -> str:
    if kind == "ktx":
        svg = f"""
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 220 88'>
  <defs>
    <linearGradient id='bg' x1='0' x2='1'>
      <stop offset='0' stop-color='#ffffff'/>
      <stop offset='1' stop-color='#eef5ff'/>
    </linearGradient>
  </defs>
  <rect x='3' y='20' width='214' height='48' rx='22' fill='url(#bg)' stroke='{outline}' stroke-width='3'/>
  <path d='M18 61 C34 42, 60 27, 101 24 L101 64 C58 64, 31 64, 18 61 Z' fill='{nose}' stroke='{outline}' stroke-width='2'/>
  <rect x='86' y='30' width='94' height='16' rx='8' fill='{body}' opacity='0.95'/>
  <rect x='111' y='50' width='73' height='6' rx='3' fill='{stripe}'/>
  <rect x='102' y='47' width='12' height='10' rx='3' fill='{stripe}'/>
  <rect x='64' y='39' width='28' height='10' rx='5' fill='#20364f' opacity='0.92'/>
  <g fill='#d9ecff'>
    <rect x='119' y='33' width='9' height='8' rx='2'/>
    <rect x='131' y='33' width='9' height='8' rx='2'/>
    <rect x='143' y='33' width='9' height='8' rx='2'/>
    <rect x='155' y='33' width='9' height='8' rx='2'/>
  </g>
  <text x='171' y='65' font-size='18' text-anchor='middle' font-family='Arial, sans-serif' font-weight='900' fill='{body}'>{label}</text>
</svg>"""
    elif kind == "srt":
        svg = f"""
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 220 88'>
  <defs>
    <linearGradient id='bg' x1='0' x2='1'>
      <stop offset='0' stop-color='#fff8fb'/>
      <stop offset='1' stop-color='#f4ecff'/>
    </linearGradient>
  </defs>
  <rect x='8' y='20' width='204' height='48' rx='22' fill='url(#bg)' stroke='{outline}' stroke-width='3'/>
  <path d='M24 61 C38 47, 53 32, 93 26 L93 64 C54 64, 37 63, 24 61 Z' fill='{nose}' stroke='{outline}' stroke-width='2'/>
  <rect x='88' y='28' width='102' height='18' rx='9' fill='{body}'/>
  <rect x='98' y='50' width='88' height='7' rx='3.5' fill='{stripe}'/>
  <path d='M55 39 C65 30, 77 28, 90 30 L90 48 C76 50, 64 50, 55 46 Z' fill='#2c2142' opacity='0.95'/>
  <g fill='#f6ecff'>
    <rect x='116' y='32' width='10' height='8' rx='2'/>
    <rect x='129' y='32' width='10' height='8' rx='2'/>
    <rect x='142' y='32' width='10' height='8' rx='2'/>
    <rect x='155' y='32' width='10' height='8' rx='2'/>
  </g>
  <text x='170' y='65' font-size='18' text-anchor='middle' font-family='Arial, sans-serif' font-weight='900' fill='{body}'>{label}</text>
</svg>"""
    else:
        svg = f"""
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 220 88'>
  <defs>
    <linearGradient id='bg' x1='0' x2='1'>
      <stop offset='0' stop-color='#ffffff'/>
      <stop offset='1' stop-color='#f2f9ff'/>
    </linearGradient>
  </defs>
  <rect x='8' y='24' width='204' height='40' rx='20' fill='url(#bg)' stroke='{outline}' stroke-width='3'/>
  <path d='M18 60 C34 41, 54 25, 118 24 L118 64 C55 64, 33 64, 18 60 Z' fill='{nose}' stroke='{outline}' stroke-width='2'/>
  <rect x='109' y='29' width='84' height='10' rx='5' fill='{body}'/>
  <rect x='111' y='48' width='82' height='6' rx='3' fill='{stripe}'/>
  <path d='M69 39 C79 30, 93 27, 116 30 L116 45 C95 47, 81 48, 69 46 Z' fill='#294a72' opacity='0.92'/>
  <g fill='#eaf6ff'>
    <rect x='126' y='31' width='8' height='6' rx='2'/>
    <rect x='137' y='31' width='8' height='6' rx='2'/>
    <rect x='148' y='31' width='8' height='6' rx='2'/>
    <rect x='159' y='31' width='8' height='6' rx='2'/>
  </g>
  <text x='165' y='64' font-size='16' text-anchor='middle' font-family='Arial, sans-serif' font-weight='900' fill='{body}'>{label}</text>
</svg>"""
    return " ".join(svg.split())


def image_file_data_uri(candidates, fallback_uri):
    """같은 폴더의 실제 열차 사진을 data URI로 읽고, 없으면 기존 SVG를 사용합니다."""
    for fname in candidates:
        p = APP_DIR / fname
        if p.exists():
            mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
            encoded = base64.b64encode(p.read_bytes()).decode("ascii")
            return f"data:{mime};base64,{encoded}"
    return fallback_uri


TRAIN_TYPES = {
    "KTX 청룡": {
        "name": "KTX 청룡",
        "emoji": "🚄",
        "color": "#1270d8",
        "glow": "rgba(18,112,216,.85)",
        "image": image_file_data_uri(
            ["train_ktx_cheongryong.png", "1. 청룡.png"],
            svg_data_uri(build_train_svg("청룡", "ktx", "#0d63c7", "#28b7e8", "#9de8ff", "#0a3f8a")),
        ),
        # 말 이동에는 작은 전용 이미지를 사용해 브라우저 재도색 비용을 줄입니다.
        "token_image": image_file_data_uri(
            ["train_ktx_cheongryong_token.png"],
            svg_data_uri(build_train_svg("청룡", "ktx", "#0d63c7", "#28b7e8", "#9de8ff", "#0a3f8a")),
        ),
    },
    "무궁화호": {
        "name": "무궁화호",
        "emoji": "🚆",
        "color": "#d35454",
        "glow": "rgba(211,84,84,.85)",
        "image": image_file_data_uri(
            ["train_mugunghwa.png", "2. 무궁화호.png"],
            svg_data_uri(build_train_svg("무궁화", "shinkansen", "#c44747", "#f4d03f", "#fff6ec", "#8a3b3b")),
        ),
        "token_image": image_file_data_uri(
            ["train_mugunghwa_token.png"],
            svg_data_uri(build_train_svg("무궁화", "shinkansen", "#c44747", "#f4d03f", "#fff6ec", "#8a3b3b")),
        ),
    },
    "SRT": {
        "name": "SRT",
        "emoji": "🚅",
        "color": "#8e44ad",
        "glow": "rgba(142,68,173,.85)",
        "image": image_file_data_uri(
            ["train_srt.png", "3. SRT.png"],
            svg_data_uri(build_train_svg("SRT", "srt", "#8e214f", "#5b2c83", "#e35b93", "#5a1d47")),
        ),
        "token_image": image_file_data_uri(
            ["train_srt_token.png"],
            svg_data_uri(build_train_svg("SRT", "srt", "#8e214f", "#5b2c83", "#e35b93", "#5a1d47")),
        ),
    },
}


def get_query_value(name):
    """Streamlit 버전에 관계없이 URL 쿼리 파라미터 하나를 문자열로 읽습니다."""
    try:
        value = st.query_params.get(name)
    except Exception:
        try:
            value = st.experimental_get_query_params().get(name)
        except Exception:
            value = None
    if isinstance(value, list):
        value = value[-1] if value else None
    return str(value) if value not in (None, "") else None


def set_query_values(**values):
    """기존 URL 값을 지우지 않고 필요한 쿼리 파라미터만 갱신합니다."""
    try:
        for key, value in values.items():
            if value in (None, ""):
                try:
                    del st.query_params[key]
                except Exception:
                    pass
            else:
                st.query_params[key] = str(value)
        return
    except Exception:
        pass

    # 구형 Streamlit 호환 경로
    try:
        current = st.experimental_get_query_params()
        for key, value in values.items():
            if value in (None, ""):
                current.pop(key, None)
            else:
                current[key] = str(value)
        st.experimental_set_query_params(**current)
    except Exception:
        pass


def get_train_choice_from_query():
    """사진 카드 클릭으로 전달된 열차 선택 값을 읽습니다."""
    value = get_query_value("train")
    return normalize_train_key(value) if value else None


def render_train_choice_gallery(selected_train: str, enabled: bool = True) -> str:
    """실제 열차 사진을 클릭해 말을 고르는 카드형 선택 UI를 만듭니다."""
    cards = []
    for key, train in TRAIN_TYPES.items():
        selected = key == selected_train
        border = train["color"] if selected else "rgba(255,255,255,.20)"
        shadow = train["glow"] if selected else "rgba(0,0,0,.16)"
        badge = "✓ 선택됨" if selected else "사진을 클릭해 선택"
        opacity = "1" if enabled else ".72"
        cursor = "pointer" if enabled else "default"
        card_body = (
            f"<div style='background:rgba(255,255,255,.055);border:3px solid {border};"
            f"border-radius:15px;overflow:hidden;box-shadow:0 0 17px {shadow};"
            f"opacity:{opacity};cursor:{cursor};transition:transform .15s ease,border-color .15s ease;'>"
            f"<img src='{train['image']}' alt='{key}' "
            f"style='width:100%;height:126px;object-fit:cover;display:block;background:#111;'>"
            f"<div style='padding:8px 10px 9px;text-align:center;'>"
            f"<div style='font-weight:900;font-size:15px;color:white'>{key}</div>"
            f"<div style='font-size:11px;margin-top:2px;color:{train['color'] if selected else '#cfc7dc'};font-weight:700'>{badge}</div>"
            f"</div></div>"
        )
        if enabled:
            # 열차 사진을 다시 눌러도 새로고침 간 퀴즈 기록 쿼리 파라미터를 보존합니다.
            preserved = []
            for qp_key in ("qu", "qr"):
                qp_value = get_query_value(qp_key)
                if qp_value:
                    preserved.append(f"{qp_key}={quote(qp_value)}")
            suffix = ("&" + "&".join(preserved)) if preserved else ""
            href = f"?train={quote(key)}{suffix}"
            card = (
                f"<a href='{href}' target='_self' aria-label='{key} 선택' "
                "style='display:block;text-decoration:none;color:inherit;margin:7px 0;'>"
                + card_body
                + "</a>"
            )
        else:
            card = f"<div style='margin:7px 0'>{card_body}</div>"
        cards.append(card)
    return "<div style='margin:4px 0 8px'>" + "".join(cards) + "</div>"

SQUARE_TYPES = {
    # 파란 칸과 보물상자 칸. 보물상자는 기존 5개 + 신규 4개 = 총 9개입니다.
    "홍대입구": "blue",  "강남": "blue",  "왕십리": "blue",
    "선릉":     "blue",  "시청": "blue",  "이대":   "blue",
    "아현": "treasure", "을지로4가": "treasure", "문래": "treasure",
    "당산": "treasure", "봉천": "treasure", "사당": "treasure",
    "역삼": "treasure", "잠실나루": "treasure", "잠실": "treasure",
}

BLUE_EVENTS = [
    {"msg": "🎵 이벤트 발생! 다음 주사위 +2 보너스 획득!", "bonus_dice": 2},
    {"msg": "💰 행운! 점수 +20점!", "score": 20},
    {"msg": "🎁 아이템 카드 획득! 다음 이동 2배 카드!", "item": "double_move"},
    {"msg": "⚡ 급행열차! 주사위를 한 번 더 굴립니다!", "extra_roll": True},
    {"msg": "🌟 럭키! 먹보유령이 3칸 뒤로 물러납니다!", "push_binbou": 3},
    {"msg": "🎶 축제! 점수 +15점 + 추가 주사위!", "score": 15, "extra_roll": True},
]

TREASURE_REWARD = 30
TREASURE_RETRY_REWARD = 20
TREASURE_MAX_ATTEMPTS = 3

# 5연속/10연속 정답 달성 시 열리는 특별 보물상자.
# 네 보상은 상자 네 개에 하나씩 무작위로 배치됩니다.
STREAK_TREASURE_MILESTONES = {5, 10}
STREAK_TREASURE_REWARDS = [100, 0, 20, 10]

# 보물상자에서는 지식 퀴즈 대신 직접 상태를 바꾸는 퍼즐형 활동을 사용합니다.
TREASURE_GAME_TYPES = [
    "car_sort",
    "switch_route",
    "signal_grid",
    "track_rotate",
    "memory_pairs",
    "maze",
    "cargo_balance",
    "mastermind",
    "sliding_tiles",
]

TREASURE_GAME_LABELS = {
    "car_sort": "객차 순서 맞추기",
    "switch_route": "선로 스위치 연결",
    "signal_grid": "신호등 색 맞추기",
    "track_rotate": "선로 타일 회전",
    "memory_pairs": "철도 카드 짝맞추기",
    "maze": "미니 선로 미로",
    "cargo_balance": "화물 균형 맞추기",
    "mastermind": "색깔 객차 순서 맞추기",
    "sliding_tiles": "숫자 선로 연결",
}

# 미니 선로 미로는 기존 4×4 단일 구조보다 조금 더 생각이 필요하도록
# 5×5의 여러 고정 배치 중 하나를 무작위로 사용합니다.
# 각 배치는 시작점 (0,0)에서 보물 (4,4)까지 반드시 도달할 수 있으며,
# 갈림길과 막다른 길이 일부 포함되어 있습니다.
TREASURE_MAZE_LAYOUTS = [
    {(1, 1), (1, 2), (1, 4), (2, 0), (2, 4), (3, 2), (3, 3), (4, 0)},
    {(1, 2), (2, 1), (2, 4), (3, 0), (3, 3), (3, 4), (4, 0)},
    {(1, 0), (1, 2), (2, 3), (2, 4), (3, 1), (3, 2), (3, 3)},
    {(0, 4), (1, 0), (1, 1), (2, 0), (2, 3), (3, 2), (3, 4)},
    {(0, 1), (1, 1), (1, 3), (2, 3), (3, 1), (3, 3), (4, 2)},
    {(1, 0), (1, 3), (2, 1), (2, 2), (3, 1), (3, 4)},
]


def _shuffle_until_changed(values):
    values = list(values)
    shuffled = values[:]
    for _ in range(20):
        random.shuffle(shuffled)
        if shuffled != values:
            break
    return shuffled


def _make_easy_signal_state(goal, color_count=3):
    """목표 신호에서 3~5칸만 다른 색으로 바꿔 쉬운 색 맞추기 시작 상태를 만듭니다."""
    state = list(goal)
    change_count = random.randint(3, 5)
    for i in random.sample(range(len(state)), k=change_count):
        # 목표와 반드시 다른 색이 되도록 1칸 또는 2칸 앞으로 돌립니다.
        state[i] = (int(goal[i]) + random.choice([1, 2])) % color_count
    return state


def _make_number_path_start():
    """1~6 숫자를 화면 위치만 섞어, 순서대로 누르는 쉬운 숫자 연결 퍼즐을 만듭니다."""
    tiles = [1, 2, 3, 4, 5, 6]
    random.shuffle(tiles)
    if tiles == [1, 2, 3, 4, 5, 6]:
        tiles[0], tiles[1] = tiles[1], tiles[0]
    return tiles


def build_treasure_puzzle(station_name, game_type=None):
    """보물상자에 도착할 때마다 조작형 퍼즐 9종 중 하나를 랜덤으로 생성합니다."""
    if game_type not in TREASURE_GAME_TYPES:
        previous = st.session_state.get("last_treasure_game_type")
        candidates = [g for g in TREASURE_GAME_TYPES if g != previous] or TREASURE_GAME_TYPES
        game_type = random.choice(candidates)
    st.session_state.last_treasure_game_type = game_type

    if game_type == "car_sort":
        goal = ["🚂 기관차", "🚃 객차", "🍽️ 식당칸", "🚪 마지막칸"]
        return {
            "game_type": game_type,
            "title": "🚃 객차 순서 맞추기",
            "icon": "🚃",
            "prompt": "섞여 있는 차량을 **▲/▼ 버튼으로 직접 움직여** 목표 순서와 똑같이 만들어 보세요.",
            "state": _shuffle_until_changed(goal),
            "goal": goal,
            "max_attempts": 3,
            "hint": "기관차가 맨 앞, 마지막칸이 맨 뒤입니다.",
        }

    if game_type == "switch_route":
        goal = [random.choice([0, 1]) for _ in range(3)]
        # 목표 방향을 지도 표지판처럼 보여 줍니다. 정답 선택지가 아니라 스위치를 조작하는 활동입니다.
        markers = []
        for i, direction in enumerate(goal, start=1):
            left = "⭐" if direction == 0 else "⬜"
            right = "⭐" if direction == 1 else "⬜"
            markers.append(f"{i}번 분기  ◀ {left}   {right} ▶")
        return {
            "game_type": game_type,
            "title": "🛤️ 선로 스위치 연결",
            "icon": "🛤️",
            "prompt": "위의 ⭐ 표지판이 이어지는 쪽으로 3개의 분기기를 돌려 보물 선로를 연결하세요.",
            "state": [random.choice([0, 1]) for _ in range(3)],
            "goal": goal,
            "map_lines": markers,
            "max_attempts": 3,
            "hint": "각 분기에서 별이 있는 방향과 현재 스위치 방향을 하나씩 비교하세요.",
        }

    if game_type == "signal_grid":
        # 어려운 Lights Out 방식 대신, 누른 칸 하나만 색이 바뀌는 쉬운 시각 퍼즐입니다.
        colors = ["🔴", "🟡", "🟢"]
        goal = [random.randrange(len(colors)) for _ in range(6)]
        return {
            "game_type": game_type,
            "title": "🚦 신호등 색 맞추기",
            "icon": "🚦",
            "prompt": (
                "위의 **목표 신호**와 아래의 **현재 신호**가 똑같아지도록 불빛을 눌러 보세요. "
                "한 칸을 누르면 **그 칸만** 🔴 → 🟡 → 🟢 → 🔴 순서로 바뀝니다."
            ),
            "state": _make_easy_signal_state(goal, len(colors)),
            "goal": goal,
            "colors": colors,
            "max_attempts": 3,
            "hint": "목표와 색이 다른 칸만 하나씩 눌러 보세요. 다른 칸의 색은 함께 바뀌지 않습니다.",
        }

    if game_type == "track_rotate":
        cycle = ["─", "╲", "│", "╱"]
        goal_rot = [random.randrange(4) for _ in range(5)]
        state = [(g + random.choice([1, 2, 3])) % 4 for g in goal_rot]
        return {
            "game_type": game_type,
            "title": "🔄 선로 타일 회전",
            "icon": "🔄",
            "prompt": "각 선로 타일을 눌러 회전시키고, **목표 선로 모양**과 완전히 같게 맞춰 보세요.",
            "state": state,
            "goal": goal_rot,
            "cycle": cycle,
            "max_attempts": 3,
            "hint": "타일을 누를 때마다 45~90도씩 다음 모양으로 바뀝니다.",
        }

    if game_type == "memory_pairs":
        cards = ["🚄", "🚇", "🚆"] * 2
        random.shuffle(cards)
        return {
            "game_type": game_type,
            "title": "🃏 철도 카드 짝맞추기",
            "icon": "🃏",
            "prompt": "카드를 두 장씩 뒤집어 같은 열차 그림 3쌍을 모두 찾아 보세요.",
            "cards": cards,
            "revealed": [],
            "matched": [],
            "mismatch": False,
            "moves": 0,
            "hint": "한 번 본 카드의 위치를 기억해 두면 빨리 맞출 수 있습니다.",
        }

    if game_type == "maze":
        walls = set(random.choice(TREASURE_MAZE_LAYOUTS))
        return {
            "game_type": game_type,
            "title": "🧭 미니 선로 미로",
            "icon": "🧭",
            "prompt": (
                "화살표 버튼으로 열차를 움직여 벽(⬛)과 막다른 길을 피해 보물(🎁)까지 도착하세요. "
                "이번에는 **5×5 미로**라서 길을 한 번 더 살펴봐야 해요."
            ),
            "rows": 5,
            "cols": 5,
            "walls": [list(p) for p in sorted(walls)],
            "position": [0, 0],
            "goal": [4, 4],
            "moves": 0,
            "hint": "바로 보물 쪽으로만 가지 말고, 막히면 열린 통로를 따라 한 번 돌아가 보세요.",
        }

    if game_type == "cargo_balance":
        weights = [1, 2, 3, 4]
        sides = [random.choice([0, 1]) for _ in weights]
        if sides in ([0, 0, 0, 0], [1, 1, 1, 1]):
            sides[0] = 1 - sides[0]
        return {
            "game_type": game_type,
            "title": "⚖️ 화물 균형 맞추기",
            "icon": "⚖️",
            "prompt": "각 화물 버튼을 눌러 왼쪽/오른쪽 화물칸을 바꾸고, **두 칸의 총 무게를 같게** 만드세요.",
            "weights": weights,
            "state": sides,
            "max_attempts": 3,
            "hint": "전체 무게는 10kg이므로 양쪽이 각각 같은 무게가 되어야 합니다.",
        }

    if game_type == "mastermind":
        # 어려운 Mastermind 추리 대신, 눈으로 비교하며 인접 객차를 바꾸는 쉬운 배열 퍼즐입니다.
        colors = ["🔴", "🟡", "🟢", "🔵"]
        goal = colors[:]
        random.shuffle(goal)
        state = _shuffle_until_changed(goal)
        return {
            "game_type": game_type,
            "title": "🌈 색깔 객차 순서 맞추기",
            "icon": "🌈",
            "prompt": (
                "위의 **목표 객차 순서**를 보고, 아래의 색깔 객차 사이에 있는 **↔ 교환 버튼**을 눌러 "
                "똑같은 순서로 만들어 보세요."
            ),
            "colors": colors,
            "goal": goal,
            "state": state,
            "max_attempts": 3,
            "hint": "목표의 첫 번째 색부터 비교해 보세요. 이웃한 두 객차만 서로 자리를 바꿀 수 있습니다.",
        }

    # sliding_tiles라는 내부 키는 이전 세션과의 호환을 위해 유지하지만,
    # 실제 게임은 쉬운 "숫자 선로 연결" 활동으로 바꿉니다.
    return {
        "game_type": "sliding_tiles",
        "title": "🔢 숫자 선로 연결",
        "icon": "🔢",
        "prompt": (
            "섞여 있는 숫자 칸에서 **1 → 2 → 3 → 4 → 5 → 6** 순서로 눌러 "
            "기차 선로를 완성해 보세요. 맞게 누른 숫자는 초록색으로 표시됩니다."
        ),
        "state": _make_number_path_start(),
        "next_number": 1,
        "completed_numbers": [],
        "last_wrong": None,
        "hint": "가장 작은 숫자 1부터 시작해 하나씩 큰 숫자를 누르면 됩니다.",
    }


ITEMS = {
    "double_move":  {"name": "🚄 2배 이동 카드", "desc": "이번 주사위 결과를 2배로!"},
    "skip_penalty": {"name": "✨ 면제 카드",     "desc": "뒤로 가기 주사위 면제"},
    "score_up":     {"name": "💎 점수 2배 카드", "desc": "다음 정답 점수 2배"},
}

QUIZ_CATEGORIES = ["지명", "상식", "과학", "영어", "수수께끼"]

QUIZZES = [
    # ══════════════ 지명 (30문제 · 한국 명소 중심) ══════════════
    {'category': '지명', 'question': '서울에서 조선 시대 왕들이 살았던 대표 궁궐로, 광화문을 지나 들어갈 수 있는 곳은 어디일까요?',
     'options': ['경복궁', '불국사', '수원화성', '전주한옥마을'], 'answer': 0},
    {'category': '지명', 'question': '서울 남산 정상 부근에 있어 서울 시내를 높은 곳에서 내려다볼 수 있는 전망 명소는 어디일까요?',
     'options': ['광안대교', '남산서울타워', '성산일출봉', '첨성대'], 'answer': 1},
    {'category': '지명', 'question': '서울 경복궁 앞에 있으며 큰 광장과 세종대왕 동상을 볼 수 있는 곳은 어디일까요?',
     'options': ['코엑스', '청계천', '광화문', '서울숲'], 'answer': 2},
    {'category': '지명', 'question': '서울 용산에 있으며 우리나라의 역사와 문화재를 많이 볼 수 있는 큰 박물관은 어디일까요?',
     'options': ['철도박물관', '서울역', '동대문디자인플라자', '국립중앙박물관'], 'answer': 3},
    {'category': '지명', 'question': '경기도 수원에 있는 조선 시대 성곽으로, 긴 성벽을 따라 걸어볼 수 있는 세계유산은 어디일까요?',
     'options': ['수원화성', '경복궁', '첨성대', '안동하회마을'], 'answer': 0},
    {'category': '지명', 'question': '경상북도 경주에 있으며 석가탑과 다보탑으로도 유명한 절은 어디일까요?',
     'options': ['해인사', '불국사', '봉은사', '조계사'], 'answer': 1},
    {'category': '지명', 'question': '부산에서 넓은 모래사장과 바다로 유명한 대표 해수욕장은 어디일까요?',
     'options': ['경포대해수욕장', '을왕리해수욕장', '해운대해수욕장', '대천해수욕장'], 'answer': 2},
    {'category': '지명', 'question': '제주도 동쪽에 있으며 정상에서 해가 떠오르는 모습을 보기 좋은 커다란 화산 지형은 어디일까요?',
     'options': ['한라산', '설악산', '남산', '성산일출봉'], 'answer': 3},
    {'category': '지명', 'question': '제주도 한가운데에 있으며 우리나라에서 가장 높은 산은 어디일까요?',
     'options': ['한라산', '북한산', '지리산', '설악산'], 'answer': 0},
    {'category': '지명', 'question': '전라북도 전주에 있으며 한옥이 많이 모여 있어 전통적인 거리 풍경을 볼 수 있는 곳은 어디일까요?',
     'options': ['북촌한옥마을', '전주한옥마을', '감천문화마을', '인사동'], 'answer': 1},
    {'category': '지명', 'question': '경상북도 안동에 있으며 전통 한옥과 옛 마을 모습을 간직한 세계유산 마을은 어디일까요?',
     'options': ['전주한옥마을', '남산골한옥마을', '안동하회마을', '북촌한옥마을'], 'answer': 2},
    {'category': '지명', 'question': '강원도에 있으며 울산바위와 단풍으로 유명한 국립공원 산은 어디일까요?',
     'options': ['한라산', '북한산', '남산', '설악산'], 'answer': 3},
    {'category': '지명', 'question': '부산의 바다 위를 가로지르며 밤에 불빛이 아름다운 큰 다리는 어디일까요?',
     'options': ['광안대교', '성산대교', '한강대교', '인천대교'], 'answer': 0},
    {'category': '지명', 'question': '대한민국의 대표 국제공항으로, 해외로 비행기를 타고 갈 때 많이 이용하는 공항은 어디일까요?',
     'options': ['김포국제공항', '인천국제공항', '제주국제공항', '김해국제공항'], 'answer': 1},
    {'category': '지명', 'question': '서울 동대문에 있으며 독특한 곡선 모양 건물과 전시·행사로 유명한 곳은 어디일까요?',
     'options': ['국립중앙박물관', '잠실롯데타워', '동대문디자인플라자', '경복궁'], 'answer': 2},
    {'category': '지명', 'question': '서울 삼성동에 있으며 큰 전시장, 쇼핑몰, 별마당도서관 등이 모여 있는 곳은 어디일까요?',
     'options': ['서울숲', '광화문', '하남스타필드', '코엑스'], 'answer': 3},
    {'category': '지명', 'question': '서울 도심을 흐르며 산책로가 잘 만들어져 있어 사람들이 걸으며 쉬기 좋은 하천은 어디일까요?',
     'options': ['청계천', '낙동강', '섬진강', '소양강'], 'answer': 0},
    {'category': '지명', 'question': '서울에 있는 과학고등학교 중 하나로, 과학과 수학에 관심이 많은 학생들이 공부하는 학교는 어디일까요?',
     'options': ['연세대학교', '한성과학고', '세브란스병원', '국립중앙박물관'], 'answer': 1},
    {'category': '지명', 'question': '서울 신촌에 있는 대학교로, 독수리를 상징으로 사용하며 오래된 캠퍼스로도 잘 알려진 곳은 어디일까요?',
     'options': ['서울대학교', '고려대학교', '연세대학교', '이화여자대학교'], 'answer': 2},
    {'category': '지명', 'question': '서울 신촌에서 연세대학교와 연결되어 있으며 많은 환자를 진료하는 큰 병원은 어디일까요?',
     'options': ['서울역', '한성과학고', '하남스타필드', '세브란스병원'], 'answer': 3},
    {'category': '지명', 'question': "이름에 '곤지'와 아기들이 손뼉 치며 하는 '잼잼'이 함께 들어가는 어린이집 이름은 무엇일까요?",
     'options': ['곤지잼잼어린이집', '하남스타필드', '한성과학고', '서울숲'], 'answer': 0},
    {'category': '지명', 'question': '경주에 있으며 신라 시대 사람들이 별과 하늘을 관찰하는 데 사용한 것으로 알려진 돌로 만든 천문 관측 유적은 어디일까요?',
     'options': ['다보탑', '첨성대', '광화문', '수원화성'], 'answer': 1},
    {'category': '지명', 'question': '경기도 하남에 있으며 쇼핑, 식사, 놀이를 한곳에서 즐길 수 있는 매우 큰 복합 쇼핑 공간은 어디일까요?',
     'options': ['코엑스', '동대문디자인플라자', '하남스타필드', '인천국제공항'], 'answer': 2},
    {'category': '지명', 'question': '서울 잠실에 있으며 아주 높은 전망대와 쇼핑 공간이 있는 초고층 건물로 잘 알려진 곳은 어디일까요?',
     'options': ['남산서울타워', '63빌딩', '에펠탑', '잠실롯데타워'], 'answer': 3},
    {'category': '지명', 'question': '레고기차, KTX, 무궁화호가 모여 있고, 공항과 캠핑 장소도 있는 곳은 어디일까요?',
     'options': ['주안랜드', '서울역', '철도박물관', '하남스타필드'], 'answer': 0},
    {'category': '지명', 'question': '일본 사이타마에 있으며 실제 철도 차량과 철도의 역사를 보고 체험할 수 있는 곳은 어디일까요?',
     'options': ['도쿄타워', '일본의 철도박물관', '오사카성', '후지산'], 'answer': 1},
    {'category': '지명', 'question': '프랑스 파리에 있는 거대한 철제 탑으로, 파리를 대표하는 명소는 무엇일까요?',
     'options': ['개선문', '루브르박물관', '에펠탑', '콜로세움'], 'answer': 2},
    {'category': '지명', 'question': '프랑스 파리의 샹젤리제 거리 끝쪽에 있는 거대한 문 모양의 기념물은 무엇일까요?',
     'options': ['에펠탑', '자유의 여신상', '빅벤', '개선문'], 'answer': 3},
    {'category': '지명', 'question': '미국 뉴욕항에 있으며 한 손에 횃불을 들고 있는 거대한 동상은 무엇일까요?',
     'options': ['자유의 여신상', '에펠탑', '개선문', '피사의 사탑'], 'answer': 0},
    {'category': '지명', 'question': '서울 성동구에 있는 큰 공원으로, 나무와 산책길이 많아 도심 속에서 자연을 즐기기 좋은 곳은 어디일까요?',
     'options': ['북한산', '서울숲', '광화문', '코엑스'], 'answer': 1},

    # ══════════════ 상식 (30문제 · 8세 수준) ══════════════
    {'category': '상식', 'question': '우리나라의 수도는 서울입니다. 그렇다면 서울시청이 하는 일과 가장 가까운 것은 무엇일까요?',
     'options': ['전국의 모든 학교 시험을 만든다', '모든 기차를 직접 운전한다', '서울의 여러 행정 일을 처리한다', '날씨를 정한다'], 'answer': 2},
    {'category': '상식', 'question': '지도를 볼 때 위쪽이 북쪽이라면, 북쪽을 보고 서 있을 때 오른손 쪽은 어느 방향일까요?',
     'options': ['동쪽', '서쪽', '남쪽', '북쪽'], 'answer': 0},
    {'category': '상식', 'question': '오전 9시에 시작한 수업이 40분 동안 진행되었다면 끝나는 시각은 언제일까요?',
     'options': ['오전 9시 20분', '오전 9시 30분', '오전 10시 40분', '오전 9시 40분'], 'answer': 3},
    {'category': '상식', 'question': '오늘이 화요일이라면 이틀 뒤는 무슨 요일일까요?',
     'options': ['수요일', '목요일', '금요일', '토요일'], 'answer': 1},
    {'category': '상식', 'question': '봄에 씨를 심어 여름 동안 기르고 가을에 거두는 활동을 무엇이라고 할까요?',
     'options': ['항해', '농사', '발명', '건축'], 'answer': 1},
    {'category': '상식', 'question': '한글날은 한글의 소중함을 생각하는 날입니다. 한글을 창제한 왕은 누구일까요?',
     'options': ['태조', '정조', '고종', '세종대왕'], 'answer': 3},
    {'category': '상식', 'question': '대한민국의 국기인 태극기 가운데 있는 빨강과 파랑의 둥근 무늬를 무엇이라고 할까요?',
     'options': ['태극', '무궁화', '오륜', '별자리'], 'answer': 0},
    {'category': '상식', 'question': '우리나라에서 가장 큰 섬인 제주도는 어느 방향의 바다 쪽에 있을까요?',
     'options': ['한반도의 북쪽', '서울의 동쪽 육지 한가운데', '한반도의 남쪽', '강원도 산속'], 'answer': 2},
    {'category': '상식', 'question': '화재가 났을 때 119에 전화한다면 가장 먼저 알려 주면 좋은 정보는 무엇일까요?',
     'options': ['좋아하는 음식', '학교 성적', '친구의 생일', '불이 난 장소와 상황'], 'answer': 3},
    {'category': '상식', 'question': '지진이 난 뒤 엘리베이터보다 계단을 이용하는 것이 좋은 까닭은 무엇일까요?',
     'options': ['계단이 더 재미있어서', '계단이 항상 더 짧아서', '엘리베이터가 멈출 수 있어서', '엘리베이터에는 사람이 없어서'], 'answer': 2},
    {'category': '상식', 'question': '종이, 캔, 플라스틱을 종류별로 나누어 버리는 가장 큰 까닭은 무엇일까요?',
     'options': ['쓰레기를 더 무겁게 만들려고', '다시 쓸 수 있는 자원을 재활용하려고', '쓰레기통을 많이 사용하려고', '색깔을 맞추려고'], 'answer': 1},
    {'category': '상식', 'question': '여름에 햇볕이 강한 날 모자나 양산을 사용하는 이유로 가장 알맞은 것은?',
     'options': ['햇빛과 더위로부터 몸을 보호하기 위해', '비를 더 많이 맞기 위해', '바람을 막아 더 덥게 하려고', '밤을 밝히기 위해'], 'answer': 0},
    {'category': '상식', 'question': '도서관에서 빌린 책의 반납 날짜가 지났다는 것을 알게 되었습니다. 가장 알맞은 행동은?',
     'options': ['가능한 빨리 도서관에 돌려준다', '책을 숨긴다', '친구에게 그냥 준다', '책 이름을 지운다'], 'answer': 0},
    {'category': '상식', 'question': '공원에서 길을 잃었을 때 가장 안전한 행동은 무엇일까요?',
     'options': ['혼자 멀리 돌아다니며 찾는다', '모르는 사람 차를 탄다', '아무에게도 말하지 않는다', '안내소나 믿을 수 있는 어른에게 도움을 요청한다'], 'answer': 3},
    {'category': '상식', 'question': '우리나라의 전통 명절인 추석과 가장 관계 깊은 것은 무엇일까요?',
     'options': ['크리스마스트리와 선물', '한글 창제 기념식', '송편과 성묘', '어린이날 운동회'], 'answer': 2},
    {'category': '상식', 'question': '바닷물이 강물보다 짠 까닭과 가장 관계 있는 것은 무엇일까요?',
     'options': ['바다가 파란색이기 때문', '바닷물에 여러 염류가 녹아 있기 때문', '물고기가 살기 때문', '파도가 있기 때문'], 'answer': 1},
    {'category': '상식', 'question': '태양이 동쪽에서 뜨고 서쪽으로 지는 것처럼 보이는 것과 가장 관계 깊은 것은?',
     'options': ['달의 모양', '비의 양', '지구의 자전', '바람의 세기'], 'answer': 2},
    {'category': '상식', 'question': '감기에 걸린 친구가 사용한 컵을 함께 쓰지 않는 것이 좋은 이유는 무엇일까요?',
     'options': ['병을 옮기는 것을 줄이기 위해', '컵이 무거워질 수 있어서', '컵 색깔이 변해서', '물이 빨리 식어서'], 'answer': 0},
    {'category': '상식', 'question': '횡단보도 신호가 초록불로 바뀌었더라도 바로 뛰어나가지 않고 좌우를 살피는 까닭은?',
     'options': ['신호등 색을 다시 바꾸려고', '혹시 움직이는 차가 있는지 확인하려고', '길을 더 오래 건너려고', '친구보다 늦게 가려고'], 'answer': 1},
    {'category': '상식', 'question': '한 사람이 사용한 전기를 줄이기 위한 행동으로 가장 알맞은 것은?',
     'options': ['빈 방의 불을 켜 둔다', '냉장고 문을 오래 열어 둔다', '텔레비전을 보지 않아도 켜 둔다', '사용하지 않는 전등을 끈다'], 'answer': 3},
    {'category': '상식', 'question': '지하철 노선도에서 서로 다른 색의 노선이 한 역에서 만난다면 그 역에서 할 수 있을 가능성이 가장 큰 것은?',
     'options': ['비행기 탑승', '환승', '배 타기', '자동차 주유'], 'answer': 1},
    {'category': '상식', 'question': '교통카드를 찍고 지하철에 들어간 뒤 같은 카드를 다시 찍고 나오는 이유로 가장 알맞은 것은?',
     'options': ['열차 색을 바꾸기 위해', '좌석 번호를 정하기 위해', '역 이름을 바꾸기 위해', '승차와 하차 정보를 확인하고 요금을 처리하기 위해'], 'answer': 3},
    {'category': '상식', 'question': '승강장에서 열차를 기다릴 때 안전선 안쪽에 서 있어야 하는 가장 중요한 이유는?',
     'options': ['열차와 선로에서 안전한 거리를 두기 위해', '광고를 더 잘 보기 위해', '열차가 더 빨리 오게 하려고', '의자에 빨리 앉으려고'], 'answer': 0},
    {'category': '상식', 'question': '열차 문이 열렸는데 안에서 많은 사람이 내리고 있습니다. 가장 바른 행동은?',
     'options': ['문 가운데 서서 바로 들어간다', '친구와 손을 잡고 뛰어 들어간다', '내리는 사람이 먼저 나오도록 옆에서 기다린다', '가방으로 문을 막는다'], 'answer': 2},
    {'category': '상식', 'question': '지하철에서 목적지를 지나쳤다는 것을 알았습니다. 가장 알맞은 방법은?',
     'options': ['선로를 걸어서 돌아간다', '움직이는 열차 문을 연다', '다음 역에서 내려 반대 방향 열차를 확인한다', '운전실로 들어간다'], 'answer': 2},
    {'category': '상식', 'question': 'KTX나 SRT처럼 먼 거리를 빠르게 이동하는 열차를 이용할 때 일반적으로 필요한 것은?',
     'options': ['목적지와 시간에 맞는 승차권 확인', '자전거 면허증', '수영 모자', '도서관 회원증'], 'answer': 0},
    {'category': '상식', 'question': '기차역 전광판에서 열차 번호와 출발 시각을 확인하는 가장 큰 이유는?',
     'options': ['기차의 무게를 재기 위해', '날씨를 바꾸기 위해', '좌석을 직접 만들기 위해', '내가 탈 열차와 시간을 정확히 찾기 위해'], 'answer': 3},
    {'category': '상식', 'question': '열차 안에서 비상 상황이 생겼을 때 가장 먼저 해야 할 행동으로 알맞은 것은?',
     'options': ['마음대로 문을 연다', '안내방송과 직원의 지시에 따른다', '선로로 뛰어내린다', '숨겨진 스위치를 아무거나 누른다'], 'answer': 1},
    {'category': '상식', 'question': '지하철의 종착역이라는 말은 무엇을 뜻할까요?',
     'options': ['그 열차 운행의 마지막 역', '항상 가장 사람이 많은 역', '모든 노선이 만나는 역', '기차를 만드는 공장'], 'answer': 0},
    {'category': '상식', 'question': '노선도에서 목적지까지 가는 길이 두 가지이고, 한 길은 환승 1번, 다른 길은 환승 3번이라면 길이 비슷할 때 더 간단한 길은?',
     'options': ['환승 3번인 길', '무조건 역 이름이 긴 길', '환승 1번인 길', '무조건 색이 밝은 노선'], 'answer': 2},

    # ══════════════ 과학 (30문제 · 8세 수준) ══════════════
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
    {'category': '과학', 'question': '전기줄이 있는 철도에서 팬터그래프가 하는 일로 가장 알맞은 것은 무엇일까요?',
     'options': ['바퀴에 물을 뿌린다', '승객의 표를 검사한다', '전기줄에서 전기를 받아 열차로 전달한다', '철길의 색을 바꾼다'], 'answer': 2},
    {'category': '과학', 'question': '전동차의 전동기는 전기에너지를 주로 어떤 에너지로 바꾸어 열차를 움직일까요?',
     'options': ['운동에너지', '소리에너지', '냄새에너지', '빛에너지만'], 'answer': 0},
    {'category': '과학', 'question': '달리던 기차가 브레이크를 잡으면 속도가 줄어드는 데 중요한 힘은 무엇일까요?',
     'options': ['부력', '자석이 끌어당기는 힘만', '빛의 힘', '마찰력'], 'answer': 3},
    {'category': '과학', 'question': '서 있던 지하철이 갑자기 출발할 때 몸이 뒤쪽으로 기울어지는 것과 가장 관계 깊은 것은 무엇일까요?',
     'options': ['증발', '관성', '광합성', '응결'], 'answer': 1},
    {'category': '과학', 'question': '터널 안에서 소리가 더 울려 들리는 까닭은 무엇일까요?',
     'options': ['소리가 얼음으로 변하기 때문에', '터널이 소리를 먹기 때문에', '소리가 벽에 반사되기 때문에', '빛이 소리로 변하기 때문에'], 'answer': 2},
    {'category': '과학', 'question': '더운 날 철길의 금속 레일이 아주 조금 길어질 수 있는 까닭은 무엇일까요?',
     'options': ['금속이 열을 받으면 팽창할 수 있어서', '금속이 물로 변해서', '레일이 숨을 쉬어서', '바퀴가 레일을 잡아당겨서'], 'answer': 0},
    {'category': '과학', 'question': '열차의 안내방송 소리가 우리 귀까지 전달될 때 주로 무엇을 통해 이동할까요?',
     'options': ['그림자', '철가루만', '빛', '공기'], 'answer': 3},
    {'category': '과학', 'question': '어두운 터널에서 열차의 전조등을 켜는 가장 큰 까닭은 무엇일까요?',
     'options': ['열차를 더 무겁게 만들기 위해', '앞쪽을 더 잘 보기 위해', '바퀴를 차갑게 하기 위해', '소리를 크게 만들기 위해'], 'answer': 1},
    {'category': '과학', 'question': '기차 바퀴와 레일을 주로 금속으로 만드는 것과 가장 관계 깊은 성질은 무엇일까요?',
     'options': ['물에 넣으면 사라진다', '항상 투명하다', '단단하고 큰 힘을 견딜 수 있다', '종이처럼 쉽게 찢어진다'], 'answer': 2},
    {'category': '과학', 'question': '달리는 열차가 멈출 때 운동에너지의 일부가 브레이크에서 주로 무엇으로 바뀔 수 있을까요?',
     'options': ['열에너지', '냄새에너지', '그림자에너지', '맛에너지'], 'answer': 0},

    # ══════════════ 영어 (30문제 · 8세 수준) ══════════════
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
    {'category': '영어', 'question': "'train'의 뜻은 무엇일까요?",
     'options': ['자전거', '비행기', '기차', '배'], 'answer': 2},
    {'category': '영어', 'question': "'subway'의 뜻으로 가장 알맞은 것은 무엇일까요?",
     'options': ['지하철', '도서관', '운동장', '우체국'], 'answer': 0},
    {'category': '영어', 'question': "'station'의 뜻은 무엇일까요?",
     'options': ['교실', '공원', '시장', '역'], 'answer': 3},
    {'category': '영어', 'question': "'platform'을 지하철이나 기차에서 쓰면 주로 무엇을 뜻할까요?",
     'options': ['운전대', '승강장', '창문', '좌석 번호'], 'answer': 1},
    {'category': '영어', 'question': "'ticket'의 뜻으로 알맞은 것은 무엇일까요?",
     'options': ['여행 가방', '철길', '승차권·표', '신호등'], 'answer': 2},
    {'category': '영어', 'question': "'The train is coming.'의 뜻은 무엇일까요?",
     'options': ['기차가 오고 있습니다.', '기차가 잠들었습니다.', '기차가 사라졌습니다.', '기차를 씻고 있습니다.'], 'answer': 0},
    {'category': '영어', 'question': "'Get off at City Hall.'의 뜻으로 가장 알맞은 것은 무엇일까요?",
     'options': ['시청에서 뛰세요.', '시청을 닫으세요.', '시청에서 기차를 운전하세요.', '시청에서 내리세요.'], 'answer': 3},
    {'category': '영어', 'question': "지하철에서 'transfer'는 주로 어떤 뜻으로 쓰일까요?",
     'options': ['잠들다', '환승하다', '사진을 찍다', '표를 찢다'], 'answer': 1},
    {'category': '영어', 'question': "'Where is the subway station?'의 뜻은 무엇일까요?",
     'options': ['기차는 몇 살인가요?', '표는 무슨 색인가요?', '지하철역이 어디에 있나요?', '오늘은 무슨 요일인가요?'], 'answer': 2},
    {'category': '영어', 'question': "'Please stand behind the safety line.'의 뜻으로 가장 알맞은 것은 무엇일까요?",
     'options': ['안전선 뒤에 서 주세요.', '기차 위에 올라가 주세요.', '문을 세게 밀어 주세요.', '선로를 건너가 주세요.'], 'answer': 0},

    # ══════════════ 수수께끼 (30문제 · 창의·말장난·철도 수수께끼) ══════════════
    {'category': '수수께끼', 'question': '차는 차인데 아기들이 가장 자주 타는 차는 무엇일까요?',
     'options': ['경찰차', '유모차', '기차', '소방차'], 'answer': 1},
    {'category': '수수께끼', 'question': '전기줄에 닿아도 혼나지 않고, 오히려 힘을 얻는 기차의 “손”은 무엇일까요?',
     'options': ['손잡이', '브레이크', '와이퍼', '팬터그래프'], 'answer': 3},
    {'category': '수수께끼', 'question': '옷은 그대로인데 하루에도 몇 번씩 “갈아타는” 것은 무엇일까요?',
     'options': ['환승', '세탁', '갈아입기', '이사'], 'answer': 0},
    {'category': '수수께끼', 'question': '땅속을 다니는 긴 용처럼 역마다 사람을 삼켰다가 다시 뱉는 것은 무엇일까요?',
     'options': ['두더지', '엘리베이터', '지하철', '터널'], 'answer': 2},
    {'category': '수수께끼', 'question': '두 줄짜리 길만 골라 다니는 아주 긴 애벌레는 무엇일까요?',
     'options': ['지네', '버스', '자전거', '기차'], 'answer': 3},
    {'category': '수수께끼', 'question': '입은 없는데 “이번 역은…” 하고 또박또박 말하는 것은 무엇일까요?',
     'options': ['노선도', '안내방송', '개찰구', '철길'], 'answer': 1},
    {'category': '수수께끼', 'question': '기차가 길을 잃지 않도록 하루 종일 나란히 누워 있는 두 줄은 무엇일까요?',
     'options': ['횡단보도', '전깃줄', '철길', '운동장 선'], 'answer': 2},
    {'category': '수수께끼', 'question': '손가락은 없지만 달리는 기차를 꽉 잡아 멈춰 세우는 “손”은 무엇일까요?',
     'options': ['브레이크', '팬터그래프', '좌석', '전조등'], 'answer': 0},
    {'category': '수수께끼', 'question': '산에 뚫린 커다란 입인데 기차를 삼켜도 잠시 뒤 다시 내보내는 것은 무엇일까요?',
     'options': ['동굴 속 곰', '터널', '승강장', '매표소'], 'answer': 1},
    {'category': '수수께끼', 'question': '성적표는 아닌데 이것이 있으면 기차 여행을 시작할 수 있는 “표”는 무엇일까요?',
     'options': ['시간표', '성적표', '이름표', '승차권'], 'answer': 3},
    {'category': '수수께끼', 'question': '사람들이 줄지어 기다리지만 침대가 하나도 없는 “기다림의 방”은 어디일까요?',
     'options': ['침실', '교실', '승강장', '주차장'], 'answer': 2},
    {'category': '수수께끼', 'question': '집 벽에는 없는데 열리면 바로 열차를 만날 수 있는 긴 문은 무엇일까요?',
     'options': ['승강장 안전문(스크린도어)', '냉장고 문', '교실 문', '옷장 문'], 'answer': 0},
    {'category': '수수께끼', 'question': '한 번 “찍으면” 문을 열어 주고, 다시 “찍으면” 여행을 마쳤다는 것도 아는 카드는 무엇일까요?',
     'options': ['생일카드', '트럼프 카드', '명함', '교통카드'], 'answer': 3},
    {'category': '수수께끼', 'question': '지도인데 산과 바다는 거의 없고, 알록달록한 선과 역 이름이 가득한 지도는 무엇일까요?',
     'options': ['세계지도', '지하철 노선도', '기상지도', '보물지도'], 'answer': 1},
    {'category': '수수께끼', 'question': '나는 역마다 이름을 달고 서 있지만 한 발짝도 움직이지 않아요. 승객에게 “여기가 어디인지” 알려 주는 나는 누구일까요?',
     'options': ['역명판', '기관사', '전동차', '에스컬레이터'], 'answer': 0},
    {'category': '수수께끼', 'question': '잠이 많은 사람이 이름만 듣고 가장 눕고 싶어 할 것 같은 서울 2호선 역은 어디일까요?',
     'options': ['강남', '합정', '잠실', '신도림'], 'answer': 2},
    {'category': '수수께끼', 'question': '왕이 열 리(十里)를 걸어가면 도착할 것 같은 서울 2호선 역은 어디일까요?',
     'options': ['시청', '왕십리', '성수', '문래'], 'answer': 1},
    {'category': '수수께끼', 'question': '감기에 걸린 기차가 약을 찾다가 이름만 보고 내려 보고 싶을 것 같은 수도권 전철역은 어디일까요?',
     'options': ['강남역', '신림역', '합정역', '약수역'], 'answer': 3},
    {'category': '수수께끼', 'question': '추운 겨울에 이름만 들어도 따뜻한 물이 생각나는 수도권 전철역은 어디일까요?',
     'options': ['온수역', '시청역', '당산역', '삼성역'], 'answer': 0},
    {'category': '수수께끼', 'question': '기차가 배가 고프다고 해도 김밥 대신 먹고 달리는 “밥”은 무엇일까요?',
     'options': ['모래', '종이', '전기', '물감'], 'answer': 2},
    {'category': '수수께끼', 'question': '기차가 매일 밟고 지나가지만 “아야!” 하지 않는 철길의 잠자리는 무엇일까요?',
     'options': ['베개', '이불', '매트리스', '침목'], 'answer': 3},
    {'category': '수수께끼', 'question': '길을 잃은 승객에게 말 한마디 없이 화살표로 계속 길을 알려 주는 친구는 무엇일까요?',
     'options': ['열차 바퀴', '안내표지판', '브레이크', '좌석'], 'answer': 1},
    {'category': '수수께끼', 'question': '기차가 큰 소리로 “빵!” 하고 인사할 때 사용하는 목소리는 무엇일까요?',
     'options': ['속삭임', '메아리', '기적', '알람'], 'answer': 2},
    {'category': '수수께끼', 'question': '계단인데 가만히 서 있어도 나를 위나 아래로 데려다주는 계단은 무엇일까요?',
     'options': ['에스컬레이터', '사다리', '돌계단', '징검다리'], 'answer': 0},
    {'category': '수수께끼', 'question': '먹이를 먹으면 먹을수록 몸집이 더 커지는 것은 무엇일까요?',
     'options': ['연필', '불', '얼음', '비누'], 'answer': 1},
    {'category': '수수께끼', 'question': '햇빛이 있는 날 나를 졸졸 따라오지만 아무리 빨리 달려도 붙잡을 수 없는 친구는 무엇일까요?',
     'options': ['구름', '바람', '메아리', '그림자'], 'answer': 3},
    {'category': '수수께끼', 'question': '산에서 내가 “야호!” 하면 똑같이 “야호!” 하고 장난치는 보이지 않는 친구는 무엇일까요?',
     'options': ['메아리', '바람', '별', '안개'], 'answer': 0},
    {'category': '수수께끼', 'question': '문은 문인데 손잡이도 자물쇠도 없고, 사람들 입에서 입으로 열리는 문은 무엇일까요?',
     'options': ['대문', '창문', '소문', '자동문'], 'answer': 2},
    {'category': '수수께끼', 'question': '세상에서 가장 억울해 보이는 도형은 무엇일까요? “정말 ○○하다!”라는 말과 이름이 같아요.',
     'options': ['삼각형', '오각형', '타원', '원통'], 'answer': 3},
    {'category': '수수께끼', 'question': '몸은 없는데 달릴 수 있고, 입은 없는데 창문을 흔들 수 있으며, 잡으려고 하면 손가락 사이로 빠져나가는 것은 무엇일까요?',
     'options': ['기차', '바람', '구름', '빛'], 'answer': 1},

]


# ═══════════════════════════════════════════════════
#  게임 상태 초기화
# ═══════════════════════════════════════════════════
def normalize_train_key(train_key: str) -> str:
    legacy_map = {"KTX": "KTX 청룡", "신칸센": "무궁화호"}
    normalized = legacy_map.get(train_key, train_key)
    return normalized if normalized in TRAIN_TYPES else "KTX 청룡"

def init_game(keep_name=True):
    old_name = st.session_state.get("player_name", "플레이어")
    old_train = normalize_train_key(st.session_state.get("selected_train", "KTX 청룡"))
    st.session_state.player_name       = old_name if keep_name else "플레이어"
    st.session_state.selected_train    = old_train
    st.session_state.position          = 0
    st.session_state.binbou_pos        = -8
    st.session_state.binbou_attached   = False
    st.session_state.binbou_effect     = None
    st.session_state.game_phase        = "start"
    st.session_state.current_quiz      = None
    st.session_state.quiz_queue        = []
    # 퀴즈 덱(quiz_decks), 카테고리 순환(quiz_category_cycle), 최근 문제 기록은
    # 새 게임을 시작해도 유지합니다. 따라서 직전 게임의 문제들이 곧바로
    # 다시 출제되지 않습니다.
    st.session_state.last_dice_value   = None
    st.session_state.last_message      = "왼쪽 사이드바에서 게임을 시작하세요."
    st.session_state.winner            = False
    st.session_state.quiz_key          = 0
    st.session_state.animation_event   = None
    st.session_state.play_sound        = None
    # 정답/오답 직후 한 번만 보여 주는 보드 오버레이 상태입니다.
    # play_sound와 분리하여 뒤로 가기 주사위에서 오답 화면이 다시 뜨지 않게 합니다.
    st.session_state.answer_effect     = None
    st.session_state.score             = 0
    st.session_state.turns             = 0
    st.session_state.correct_streak    = 0
    st.session_state.extra_roll        = False
    st.session_state.bonus_dice        = 0
    st.session_state.hand_items        = []
    st.session_state.active_item       = None
    st.session_state.score_x2         = False
    st.session_state.event_log         = []
    st.session_state.ghost_game        = None
    st.session_state.ghost_puzzle_counter = 0
    st.session_state.ghost_maze_counter = 0
    st.session_state.last_ghost_game_type = None
    st.session_state.treasure_game     = None
    st.session_state.pending_treasure  = None
    st.session_state.last_treasure_game_type = None
    st.session_state.pending_post_move = None
    st.session_state.post_move_delay   = 0.0
    st.session_state.treasure_effect   = None
    st.session_state.celebration_event = None
    # 5연속/10연속 정답 때 사용하는 별도의 보물상자 선택 상태입니다.
    st.session_state.streak_treasure_game = None
    st.session_state.ladder_animation  = None


if "position" not in st.session_state:
    init_game(keep_name=False)


# 퀴즈 회전 상태는 게임 상태와 별도로 유지됩니다. 함수 정의 전에는 생성할 수 없으므로
# 실제 첫 퀴즈를 뽑을 때 ensure_quiz_rotation_state()에서 초기화합니다.

def start_game():
    name = st.session_state.get("player_name", "플레이어")
    train_key = normalize_train_key(st.session_state.get("selected_train", "KTX 청룡"))
    init_game(keep_name=True)
    st.session_state.player_name   = name
    st.session_state.selected_train = train_key
    train = TRAIN_TYPES[st.session_state.selected_train]
    st.session_state.game_phase   = "ready_to_roll"
    st.session_state.last_message = (
        f"🚄 {name}님의 {train['name']} 출발! {GOAL_STATION}역을 향해 달립니다!"
    )


def get_map_bytes():
    for fname in ["line2_map.png", "line2_map(1).png", "line2_map-3.jpg"]:
        p = APP_DIR / fname
        if p.exists():
            return p.read_bytes(), fname.endswith(".jpg")
    st.error("노선도 이미지 파일이 없습니다. line2_map.png 파일을 같은 폴더에 놓아 주세요.")
    st.stop()


def selected_categories():
    cats = list(st.session_state.get("selected_categories", QUIZ_CATEGORIES) or QUIZ_CATEGORIES)
    # 이전 버전의 '국어' 선택은 새 '지명' 카테고리 선택으로 자동 이전합니다.
    if "국어" in cats and "지명" not in cats:
        cats = ["지명" if c == "국어" else c for c in cats]
    cats = [c for c in cats if c in QUIZ_CATEGORIES]
    return cats or QUIZ_CATEGORIES


QUIZ_RECENT_MEMORY = 20
QUIZ_USED_QUERY_KEY = "qu"
QUIZ_RECENT_QUERY_KEY = "qr"
QUIZ_VERSION_QUERY_KEY = "qv"
QUIZ_BANK_VERSION = "places_v1"


def _read_persistent_quiz_state():
    """URL에서 이미 출제한 문제와 최근 문제를 복원합니다.

    Streamlit session_state는 브라우저 새로고침 때 새 세션으로 바뀔 수 있으므로,
    150개 문제의 사용 여부를 작은 16진수 비트마스크로 URL에 함께 저장합니다.
    """
    used = set()
    raw_used = get_query_value(QUIZ_USED_QUERY_KEY)
    if raw_used:
        try:
            mask = int(raw_used, 16)
            used = {i for i in range(len(QUIZZES)) if (mask >> i) & 1}
        except (TypeError, ValueError):
            used = set()

    # 이번 버전에서 0~29번은 '국어'에서 완전히 새로운 '지명' 문제로 교체되었습니다.
    # 이전 URL 기록을 그대로 쓰면 새 문제를 이미 본 것으로 오인하므로 이 30개만 새로 열어 둡니다.
    if get_query_value(QUIZ_VERSION_QUERY_KEY) != QUIZ_BANK_VERSION:
        used = {i for i in used if i >= 30}

    recent = []
    raw_recent = get_query_value(QUIZ_RECENT_QUERY_KEY)
    if raw_recent:
        for token in raw_recent.split("."):
            try:
                idx = int(token)
            except ValueError:
                continue
            if 0 <= idx < len(QUIZZES) and idx not in recent:
                recent.append(idx)
    if get_query_value(QUIZ_VERSION_QUERY_KEY) != QUIZ_BANK_VERSION:
        recent = [i for i in recent if i >= 30]
    return used, recent[-QUIZ_RECENT_MEMORY:]


def _write_persistent_quiz_state():
    """현재 퀴즈 사용 기록을 URL에 저장해 새로고침 뒤에도 유지합니다."""
    used = {
        int(i) for i in st.session_state.get("quiz_used_indices", [])
        if isinstance(i, int) and 0 <= int(i) < len(QUIZZES)
    }
    mask = 0
    for idx in used:
        mask |= 1 << idx
    recent = [
        int(i) for i in st.session_state.get("quiz_recent_indices", [])
        if isinstance(i, int) and 0 <= int(i) < len(QUIZZES)
    ][-QUIZ_RECENT_MEMORY:]
    set_query_values(
        **{
            QUIZ_USED_QUERY_KEY: format(mask, "x") if mask else None,
            QUIZ_RECENT_QUERY_KEY: ".".join(map(str, recent)) if recent else None,
            QUIZ_VERSION_QUERY_KEY: QUIZ_BANK_VERSION,
        }
    )


def ensure_quiz_rotation_state():
    """게임 재시작과 브라우저 새로고침에도 이어지는 퀴즈 덱 상태를 준비합니다."""
    # 문제 은행이 바뀐 첫 실행에서는 기존 국어 30문의 사용 기록만 비우고
    # 상식·과학·영어·수수께끼의 기록은 그대로 유지합니다.
    if st.session_state.get("quiz_bank_version") != QUIZ_BANK_VERSION:
        persisted_used, persisted_recent = _read_persistent_quiz_state()
        st.session_state.quiz_used_indices = sorted(persisted_used)
        st.session_state.quiz_recent_indices = persisted_recent
        st.session_state.quiz_decks = {}
        st.session_state.quiz_category_cycle = []
        st.session_state.quiz_bank_version = QUIZ_BANK_VERSION
        _write_persistent_quiz_state()

    if "quiz_decks" not in st.session_state or not isinstance(st.session_state.quiz_decks, dict):
        st.session_state.quiz_decks = {}
    if "quiz_category_cycle" not in st.session_state or not isinstance(st.session_state.quiz_category_cycle, list):
        st.session_state.quiz_category_cycle = []

    # 새 세션이면 URL에 저장된 사용 기록을 먼저 복원합니다.
    if "quiz_used_indices" not in st.session_state:
        persisted_used, persisted_recent = _read_persistent_quiz_state()
        st.session_state.quiz_used_indices = sorted(persisted_used)
        st.session_state.quiz_recent_indices = persisted_recent
    elif "quiz_recent_indices" not in st.session_state or not isinstance(st.session_state.quiz_recent_indices, list):
        _, persisted_recent = _read_persistent_quiz_state()
        st.session_state.quiz_recent_indices = persisted_recent

    valid_by_category = {
        cat: {i for i, q in enumerate(QUIZZES) if q["category"] == cat}
        for cat in QUIZ_CATEGORIES
    }

    # 코드 업데이트로 문제 수/카테고리가 바뀐 경우 오래된 세션 덱을 안전하게 정리합니다.
    cleaned = {}
    for cat, deck in st.session_state.quiz_decks.items():
        if cat not in valid_by_category or not isinstance(deck, list):
            continue
        valid = valid_by_category[cat]
        if all(isinstance(i, int) and i in valid for i in deck) and len(deck) == len(set(deck)):
            cleaned[cat] = deck
    st.session_state.quiz_decks = cleaned

    st.session_state.quiz_used_indices = sorted({
        i for i in st.session_state.quiz_used_indices
        if isinstance(i, int) and 0 <= i < len(QUIZZES)
    })
    st.session_state.quiz_recent_indices = [
        i for i in st.session_state.quiz_recent_indices
        if isinstance(i, int) and 0 <= i < len(QUIZZES)
    ][-QUIZ_RECENT_MEMORY:]


def refill_quiz_deck(category):
    """해당 영역에서 아직 안 나온 문제만 섞습니다. 30개 소진 후에만 새 순환을 시작합니다."""
    indices = [i for i, q in enumerate(QUIZZES) if q["category"] == category]
    if not indices:
        return []

    used = set(st.session_state.quiz_used_indices)
    unused = [i for i in indices if i not in used]

    # 이 카테고리의 30문제를 모두 본 경우에만 해당 영역의 사용 표시를 지웁니다.
    if not unused:
        category_set = set(indices)
        used -= category_set
        st.session_state.quiz_used_indices = sorted(used)
        unused = indices[:]
        _write_persistent_quiz_state()

    recent = set(st.session_state.quiz_recent_indices)
    fresh = [i for i in unused if i not in recent]
    delayed = [i for i in unused if i in recent]
    random.shuffle(fresh)
    random.shuffle(delayed)

    # 새 순환을 시작하더라도 방금 본 문제는 가능한 한 뒤쪽으로 보냅니다.
    deck = fresh + delayed
    st.session_state.quiz_decks[category] = deck
    return deck


def next_quiz_category(categories):
    """선택한 카테고리를 한 사이클에 한 번씩 사용해 영역 쏠림을 막습니다."""
    selected = list(dict.fromkeys(categories))
    if not selected:
        selected = QUIZ_CATEGORIES[:]

    cycle = [c for c in st.session_state.quiz_category_cycle if c in selected]
    missing = [c for c in selected if c not in cycle]
    random.shuffle(missing)
    cycle.extend(missing)

    if not cycle:
        cycle = selected[:]
        random.shuffle(cycle)

    category = cycle.pop(0)
    st.session_state.quiz_category_cycle = cycle
    return category


def get_random_quiz():
    """영역 균형 + 비복원 덱 + 새로고침 지속 기록으로 다음 퀴즈를 반환합니다."""
    ensure_quiz_rotation_state()
    categories = selected_categories()
    category = next_quiz_category(categories)

    # 세션에 남은 덱이 있더라도 이미 URL 사용 기록에 들어간 문제는 제거합니다.
    used = set(st.session_state.quiz_used_indices)
    deck = [i for i in st.session_state.quiz_decks.get(category, []) if i not in used]
    if not deck:
        deck = refill_quiz_deck(category)

    if not deck:
        fallback = [i for i, q in enumerate(QUIZZES) if q["category"] in categories and i not in used]
        if not fallback:
            fallback = [i for i, q in enumerate(QUIZZES) if q["category"] in categories]
        if not fallback:
            fallback = list(range(len(QUIZZES)))
        random.shuffle(fallback)
        deck = fallback

    idx = deck.pop(0)
    st.session_state.quiz_decks[category] = deck

    used = set(st.session_state.quiz_used_indices)
    used.add(idx)
    st.session_state.quiz_used_indices = sorted(used)

    recent = list(st.session_state.quiz_recent_indices)
    if idx in recent:
        recent.remove(idx)
    recent.append(idx)
    st.session_state.quiz_recent_indices = recent[-QUIZ_RECENT_MEMORY:]
    _write_persistent_quiz_state()

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
    # 이전 버전 세션에 남아 있을 수 있는 삭제된 아이템을 정리합니다.
    st.session_state.hand_items = [i for i in st.session_state.hand_items if i in ITEMS]
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



def begin_treasure_minigame(station_name, resume, puzzle=None):
    """보물상자 칸에 도착하면 조작형 퍼즐을 시작합니다."""
    puzzle = puzzle or build_treasure_puzzle(station_name)
    st.session_state.treasure_game = {
        "id": random.randint(100000, 999999),
        "station": station_name,
        "puzzle": puzzle,
        "attempts": 0,
        "feedback": "",
        "resume": resume,
    }
    st.session_state.game_phase = "treasure_minigame"
    st.session_state.play_sound = "treasure"
    st.session_state.last_message = (
        resume.get("base_msg", "")
        + f"\n\n🎁 **{station_name}역 보물상자 발견!** 퍼즐을 직접 조작해 완성하면 점수를 얻습니다."
    )
    add_event_log(f"🎁 {station_name}역 보물상자 퍼즐 시작!")


def complete_treasure_minigame():
    """현재 보물 퍼즐을 성공 처리하고 보상을 지급합니다."""
    game = st.session_state.get("treasure_game")
    if not game:
        return
    puzzle = game.get("puzzle", {})
    attempts = int(game.get("attempts", 0))
    reward = TREASURE_REWARD if attempts == 0 else TREASURE_RETRY_REWARD
    st.session_state.score += reward

    result_msg = f"🎉 {puzzle.get('title', '보물 퍼즐')} 클리어! 보물상자에서 **+{reward}점** 획득!"
    st.session_state.treasure_effect = {
        "id": random.randint(100000, 999999),
        "message": f"퍼즐 성공! +{reward}점!",
    }
    st.session_state.play_sound = "treasure"
    add_event_log(f"🏆 {game.get('station', '보물상자')} 퍼즐 성공! +{reward}점")

    resume = game.get("resume", {})
    st.session_state.treasure_game = None
    base_msg = resume.get("base_msg", "") + f"\n\n{result_msg}"
    continue_after_forward(
        base_msg,
        bool(resume.get("double_quiz", False)),
        bool(resume.get("did_win", False)),
    )


def fail_treasure_attempt(feedback):
    """검사형 퍼즐의 한 번의 실패를 처리합니다. 마지막 기회가 끝나면 0점으로 종료합니다."""
    game = st.session_state.get("treasure_game")
    if not game:
        return
    puzzle = game.get("puzzle", {})
    max_attempts = int(puzzle.get("max_attempts", TREASURE_MAX_ATTEMPTS))
    game["attempts"] = int(game.get("attempts", 0)) + 1

    if game["attempts"] < max_attempts:
        game["feedback"] = feedback
        st.session_state.play_sound = "wrong"
        st.session_state.last_message = (
            game.get("resume", {}).get("base_msg", "")
            + f"\n\n🧩 아직 완성되지 않았어요. 조작을 바꿔 다시 시도해 보세요. "
              f"남은 검사 기회: {max_attempts - game['attempts']}회"
        )
        return

    resume = game.get("resume", {})
    station = game.get("station", "보물상자")
    st.session_state.treasure_game = None
    st.session_state.play_sound = "wrong"
    add_event_log(f"📦 {station} 보물 퍼즐 미완성 — 점수 없음")
    base_msg = (
        resume.get("base_msg", "")
        + "\n\n💨 검사 기회를 모두 사용했습니다. 이번 보물상자는 **0점**입니다."
    )
    continue_after_forward(
        base_msg,
        bool(resume.get("double_quiz", False)),
        bool(resume.get("did_win", False)),
    )


def check_treasure_minigame():
    """현재 퍼즐 상태가 목표를 만족하는지 검사합니다."""
    game = st.session_state.get("treasure_game")
    if not game:
        return
    puzzle = game.get("puzzle", {})
    kind = puzzle.get("game_type")

    if kind in ("car_sort", "switch_route", "signal_grid", "track_rotate", "mastermind"):
        if list(puzzle.get("state", [])) == list(puzzle.get("goal", [])):
            complete_treasure_minigame()
        else:
            fail_treasure_attempt("❌ 아직 목표 모양과 다릅니다. 현재 상태를 다시 살펴보세요.")
        return

    if kind == "cargo_balance":
        weights = puzzle.get("weights", [])
        sides = puzzle.get("state", [])
        left = sum(w for w, side in zip(weights, sides) if side == 0)
        right = sum(w for w, side in zip(weights, sides) if side == 1)
        if left == right:
            complete_treasure_minigame()
        else:
            fail_treasure_attempt(f"⚖️ 현재는 왼쪽 {left}kg / 오른쪽 {right}kg입니다.")
        return


def treasure_puzzle_action(action, index=None):
    """버튼 조작형 퍼즐의 상태를 한 단계 변경합니다."""
    game = st.session_state.get("treasure_game")
    if not game:
        return
    puzzle = game.get("puzzle", {})
    kind = puzzle.get("game_type")

    if kind == "car_sort":
        state = puzzle["state"]
        i = int(index)
        if action == "up" and i > 0:
            state[i - 1], state[i] = state[i], state[i - 1]
        elif action == "down" and i < len(state) - 1:
            state[i + 1], state[i] = state[i], state[i + 1]
        return

    if kind == "switch_route":
        i = int(index)
        puzzle["state"][i] = 1 - int(puzzle["state"][i])
        return

    if kind == "signal_grid":
        i = int(index)
        colors = puzzle.get("colors", ["🔴", "🟡", "🟢"])
        puzzle["state"][i] = (int(puzzle["state"][i]) + 1) % len(colors)
        return

    if kind == "track_rotate":
        i = int(index)
        puzzle["state"][i] = (int(puzzle["state"][i]) + 1) % len(puzzle.get("cycle", ["─","╲","│","╱"]))
        return

    if kind == "memory_pairs":
        cards = puzzle["cards"]
        revealed = puzzle.setdefault("revealed", [])
        matched = puzzle.setdefault("matched", [])

        if action == "hide_mismatch":
            puzzle["revealed"] = []
            puzzle["mismatch"] = False
            return

        i = int(index)
        if puzzle.get("mismatch") or i in matched or i in revealed:
            return
        revealed.append(i)
        if len(revealed) == 2:
            puzzle["moves"] = int(puzzle.get("moves", 0)) + 1
            a, b = revealed
            if cards[a] == cards[b]:
                matched.extend([a, b])
                puzzle["revealed"] = []
                if len(matched) == len(cards):
                    complete_treasure_minigame()
            else:
                puzzle["mismatch"] = True
        return

    if kind == "maze":
        r, c = puzzle.get("position", [0, 0])
        delta = {
            "up": (-1, 0), "down": (1, 0),
            "left": (0, -1), "right": (0, 1),
        }.get(action, (0, 0))
        rr, cc = r + delta[0], c + delta[1]
        walls = {tuple(v) for v in puzzle.get("walls", [])}
        if 0 <= rr < int(puzzle.get("rows", 5)) and 0 <= cc < int(puzzle.get("cols", 5)) and (rr, cc) not in walls:
            puzzle["position"] = [rr, cc]
            puzzle["moves"] = int(puzzle.get("moves", 0)) + 1
        if puzzle.get("position") == puzzle.get("goal"):
            complete_treasure_minigame()
        return

    if kind == "cargo_balance":
        i = int(index)
        puzzle["state"][i] = 1 - int(puzzle["state"][i])
        return

    if kind == "mastermind":
        # 색깔 객차 사이의 버튼을 누르면 이웃한 두 객차만 서로 자리를 바꿉니다.
        i = int(index)
        state = puzzle.get("state", [])
        if action == "swap" and 0 <= i < len(state) - 1:
            state[i], state[i + 1] = state[i + 1], state[i]
        return

    if kind == "sliding_tiles":
        # 쉬운 숫자 선로 연결: 화면의 숫자 위치와 관계없이 1→6 순서로 누릅니다.
        i = int(index)
        tiles = puzzle.get("state", [])
        if i < 0 or i >= len(tiles):
            return
        value = int(tiles[i])
        expected = int(puzzle.get("next_number", 1))
        completed = puzzle.setdefault("completed_numbers", [])

        if value < expected:
            # 이미 맞힌 숫자는 다시 눌러도 아무 일도 일어나지 않습니다.
            return
        if value == expected:
            if value not in completed:
                completed.append(value)
            puzzle["last_wrong"] = None
            puzzle["next_number"] = expected + 1
            if expected >= 6:
                complete_treasure_minigame()
        else:
            # 틀려도 점수 감점이나 초기화 없이, 다음에 눌러야 할 숫자만 알려 줍니다.
            puzzle["last_wrong"] = value
        return


GHOST_ROUTE_PUZZLES = [
    # 결과를 숨겨 놓고 찍는 사다리가 아니라, 아래 탈출구 위치가 처음부터 보이는
    # 시각적 경로 추적 퍼즐입니다. 퍼즐은 이 고정 순서대로 순환하므로 결과에 운 요소가 없습니다.
    {"name": "A", "lefts": [0, 2, 1, 0, 2, 1, 2, 0, 1, 2, 0], "escape_end": 0},
    {"name": "B", "lefts": [1, 0, 2, 1, 0, 1, 2, 0, 2, 1, 0], "escape_end": 3},
    {"name": "C", "lefts": [2, 1, 0, 2, 1, 0, 1, 2, 0, 1, 2], "escape_end": 3},
    {"name": "D", "lefts": [0, 1, 2, 1, 0, 2, 0, 1, 2, 0, 1], "escape_end": 3},
    {"name": "E", "lefts": [1, 2, 0, 1, 2, 0, 2, 1, 0, 2, 1], "escape_end": 0},
    {"name": "F", "lefts": [2, 0, 1, 2, 0, 1, 0, 2, 1, 0, 2], "escape_end": 2},
]


def build_ghost_route_puzzle(puzzle_index):
    """고정된 순서의 유령 선로 퍼즐을 반환합니다. 결과에는 난수 요소가 없습니다."""
    idx = int(puzzle_index) % len(GHOST_ROUTE_PUZZLES)
    spec = GHOST_ROUTE_PUZZLES[idx]
    rungs = [{"row": row, "left": left} for row, left in enumerate(spec["lefts"])]
    bottom_outcomes = ["caught"] * 4
    bottom_outcomes[int(spec["escape_end"])] = "escape"
    return rungs, bottom_outcomes, idx


def ladder_endpoint(start_index, rungs):
    """선택한 출발 번호가 선로를 따라 도착하는 끝점 번호를 계산합니다."""
    col = int(start_index)
    for rung in sorted(rungs, key=lambda r: r.get("row", 0)):
        left = int(rung.get("left", -1))
        if col == left:
            col += 1
        elif col == left + 1:
            col -= 1
    return max(0, min(col, 3))


def render_ladder_preview(game):
    """탈출구와 유령 위치를 공개한 선로 추적 퍼즐을 사이드바에 표시합니다."""
    if not game:
        return
    rungs = game.get("rungs", [])
    outcomes = game.get("bottom_outcomes", ["caught", "caught", "caught", "caught"])
    data = json.dumps({"rungs": rungs, "outcomes": outcomes}, ensure_ascii=False)
    preview_html = f"""
    <div style="font-family:'Noto Sans KR',sans-serif;background:#16072a;border:1px solid #6741a8;border-radius:12px;padding:8px 6px 7px;color:white">
      <div style="text-align:center;font-size:12px;font-weight:800;margin-bottom:2px">🚪 탈출구로 이어지는 출발 번호를 찾아요!</div>
      <div style="text-align:center;font-size:10px;color:#cfc2e5;margin-bottom:3px">위의 1~4번 중 하나에서 시작해 가로 선을 만날 때마다 옆 선로로 이동하세요.</div>
      <svg id="ghost-route-preview" viewBox="0 0 360 285" style="width:100%;height:255px;display:block" aria-label="먹보유령 탈출 선로 퍼즐"></svg>
    </div>
    <script>
    (()=>{{
      const d={data};
      const svg=document.getElementById('ghost-route-preview');
      const ns='http://www.w3.org/2000/svg';
      const xs=[45,135,225,315], y0=34, y1=226;
      const add=(tag,attrs,text)=>{{const e=document.createElementNS(ns,tag);Object.entries(attrs||{{}}).forEach(([k,v])=>e.setAttribute(k,v));if(text!=null)e.textContent=text;svg.appendChild(e);return e;}};
      xs.forEach((x,i)=>{{
        add('circle',{{cx:x,cy:17,r:14,fill:'#3d2861',stroke:'#a98bd5','stroke-width':'2'}});
        add('text',{{x,y:22,'text-anchor':'middle',fill:'#fff','font-size':'14','font-weight':'900'}},String(i+1));
        add('line',{{x1:x,y1:y0,x2:x,y2:y1,stroke:'#eee5ff','stroke-width':'5','stroke-linecap':'round'}});
      }});
      (d.rungs||[]).forEach((r,idx)=>{{
        const y=y0+((idx+1)/((d.rungs||[]).length+1))*(y1-y0);
        const l=Math.max(0,Math.min(2,Number(r.left)||0));
        add('line',{{x1:xs[l],y1:y,x2:xs[l+1],y2:y,stroke:'#ffd166','stroke-width':'6','stroke-linecap':'round'}});
      }});
      xs.forEach((x,i)=>{{
        const escaped=(d.outcomes||[])[i]==='escape';
        add('circle',{{cx:x,cy:251,r:20,fill:escaped?'#17795c':'#742a4d',stroke:escaped?'#84f3cf':'#ff93b8','stroke-width':'3'}});
        add('text',{{x,y:258,'text-anchor':'middle','font-size':'20'}},escaped?'🚪':'👿');
        add('text',{{x,y:280,'text-anchor':'middle',fill:escaped?'#8ff8d7':'#ffbad0','font-size':'10','font-weight':'800'}},escaped?'탈출':'유령');
      }});
    }})();
    </script>
    """
    components.html(preview_html, height=290, scrolling=False)



GHOST_MAZE_PUZZLES = [
    {
        "name": "A", "rows": 5, "cols": 5, "start": [4, 0], "exit": [0, 4],
        "walls": [[3, 1], [3, 2], [3, 3], [1, 0], [1, 1], [1, 3], [1, 4], [2, 3], [4, 2]],
        "ghost": [4, 1],
        "ghosts": [[4, 4], [2, 4], [0, 0]],
    },
    {
        "name": "B", "rows": 5, "cols": 5, "start": [4, 4], "exit": [0, 0],
        "walls": [[3, 3], [3, 2], [3, 1], [1, 4], [1, 3], [1, 1], [1, 0], [2, 1], [4, 2]],
        "ghost": [4, 3],
        "ghosts": [[4, 0], [2, 0], [0, 4]],
    },
    {
        "name": "C", "rows": 5, "cols": 5, "start": [0, 0], "exit": [4, 4],
        "walls": [[1, 1], [1, 2], [1, 3], [3, 0], [3, 1], [3, 3], [3, 4], [2, 3], [0, 2]],
        "ghost": [0, 1],
        "ghosts": [[0, 4], [2, 4], [4, 0]],
    },
    {
        "name": "D", "rows": 5, "cols": 5, "start": [0, 4], "exit": [4, 0],
        "walls": [[1, 3], [1, 2], [1, 1], [3, 4], [3, 3], [3, 1], [3, 0], [2, 1], [0, 2]],
        "ghost": [0, 3],
        "ghosts": [[0, 0], [2, 0], [4, 4]],
    },
    {
        "name": "E", "rows": 5, "cols": 5, "start": [4, 2], "exit": [0, 2],
        "walls": [[3, 1], [3, 2], [3, 3], [1, 1], [1, 3]],
        "ghost": [3, 4],
        "ghosts": [[3, 4], [1, 0], [1, 2]],
    },
    {
        "name": "F", "rows": 5, "cols": 5, "start": [4, 2], "exit": [0, 2],
        "walls": [[3, 1], [3, 2], [3, 3], [1, 1], [1, 3]],
        "ghost": [3, 0],
        "ghosts": [[3, 0], [1, 4], [1, 2]],
    },
]


def build_ghost_maze_puzzle(puzzle_index):
    """고정된 벽 안에서 플레이어와 먹보유령이 함께 움직이는 추격 미로를 반환합니다."""
    idx = int(puzzle_index) % len(GHOST_MAZE_PUZZLES)
    spec = GHOST_MAZE_PUZZLES[idx]
    # 벽 배치는 그대로 유지하되, 유령은 플레이어와 같은 연결 통로에 있는
    # 검증된 시작점에서 출발합니다. (이전 버전의 일부 시작점은 벽 너머의
    # 분리된 구역에 있어 최단 경로가 존재하지 않아 유령이 움직이지 않았습니다.)
    ghost_start = list(spec.get("ghost", (spec.get("ghosts") or [[0, 0]])[0]))
    return {
        "maze_index": idx,
        "maze_name": spec["name"],
        "rows": int(spec["rows"]),
        "cols": int(spec["cols"]),
        "start": list(spec["start"]),
        "exit": list(spec["exit"]),
        "walls": [list(x) for x in spec["walls"]],
        "ghost": ghost_start[:],
        "ghost_start": ghost_start[:],
        "player": list(spec["start"]),
        "moves": 0,
        "ghost_moves": 0,
        "feedback": "🚄 한 칸 움직일 때마다 👿 먹보유령도 벽을 피해 한 칸 추격합니다.",
    }


def render_ghost_maze_preview(game):
    """고정 벽, 현재 열차, 움직이는 먹보유령, 탈출구를 잘림 없이 표시합니다."""
    if not game:
        return
    rows = int(game.get("rows", 5))
    cols = int(game.get("cols", 5))
    walls = {tuple(x) for x in game.get("walls", [])}
    legacy_ghosts = game.get("ghosts", [])
    ghost = tuple(game.get("ghost", legacy_ghosts[0] if legacy_ghosts else [0, cols - 1]))
    player = tuple(game.get("player", game.get("start", [rows - 1, 0])))
    start = tuple(game.get("start", player))
    exit_pos = tuple(game.get("exit", [0, cols - 1]))

    cells = []
    for r in range(rows):
        for c in range(cols):
            pos = (r, c)
            bg = "#25133f"
            border = "#5c477e"
            icon = ""
            label = ""
            if pos in walls:
                bg, border, icon = "#4a4451", "#81798b", "🧱"
            elif pos == exit_pos:
                bg, border, icon, label = "#124d3d", "#55d7ae", "🚪", "탈출"
            elif pos == ghost:
                bg, border, icon, label = "#5e1737", "#ff79a5", "👿", "추격"
            elif pos == start:
                bg, border, label = "#243f62", "#6fb5ff", "출발"
            if pos == player:
                bg, border, icon, label = "#735b16", "#ffd166", "🚄", "현재"
            cells.append(
                f"<div style='height:43px;border:2px solid {border};border-radius:8px;background:{bg};"
                f"display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0;min-width:0'>"
                f"<div style='font-size:20px;line-height:21px'>{icon or '·'}</div>"
                f"<div style='font-size:8px;color:#e9def7;font-weight:800;height:10px'>{label}</div></div>"
            )

    moves = int(game.get("moves", 0))
    ghost_moves = int(game.get("ghost_moves", 0))
    html = (
        "<div style=\"font-family:'Noto Sans KR',sans-serif;background:#16072a;border:1px solid #6741a8;"
        "border-radius:12px;padding:9px 9px 11px;color:white;box-sizing:border-box;overflow:visible\">"
        "<div style='text-align:center;font-size:12px;font-weight:900;margin-bottom:3px'>🧭 먹보유령 추격 미로</div>"
        "<div style='text-align:center;font-size:10px;line-height:1.35;color:#d5c8e9;margin-bottom:7px'>"
        "벽 🧱은 그대로입니다. 내가 한 칸 움직이면 👿도 나를 향해 한 칸 움직입니다.</div>"
        f"<div style='display:grid;grid-template-columns:repeat({cols},minmax(0,1fr));gap:4px'>" + "".join(cells) + "</div>"
        f"<div style='margin-top:8px;text-align:center;font-size:9px;color:#cdbfe4'>🚄 {moves}칸 이동 · 👿 {ghost_moves}칸 추격 · 🚪 먼저 도착하면 탈출!</div>"
        "</div>"
    )
    # 사이드바의 iframe 높이에 여유를 두어 마지막 행/하단 안내가 잘리지 않도록 합니다.
    components.html(html, height=350, scrolling=False)


def ghost_maze_next_step(game, ghost_pos, target_pos):
    """먹보유령이 벽을 피해 플레이어까지의 최단 경로로 정확히 한 칸 이동합니다."""
    rows = int(game.get("rows", 5))
    cols = int(game.get("cols", 5))
    walls = {tuple(x) for x in game.get("walls", [])}
    ghost_pos = tuple(ghost_pos)
    target_pos = tuple(target_pos)

    if ghost_pos == target_pos:
        return ghost_pos

    # 동률일 때도 결과가 매번 같도록 고정 순서를 사용합니다. 즉, 유령 이동에는 랜덤이 없습니다.
    directions = [(-1, 0), (0, -1), (1, 0), (0, 1)]  # 위 → 왼쪽 → 아래 → 오른쪽
    queue = [ghost_pos]
    previous = {ghost_pos: None}
    head = 0
    while head < len(queue):
        current = queue[head]
        head += 1
        if current == target_pos:
            break
        for dr, dc in directions:
            nxt = (current[0] + dr, current[1] + dc)
            if not (0 <= nxt[0] < rows and 0 <= nxt[1] < cols):
                continue
            if nxt in walls or nxt in previous:
                continue
            previous[nxt] = current
            queue.append(nxt)

    if target_pos not in previous:
        return ghost_pos

    step = target_pos
    while previous.get(step) is not None and previous[step] != ghost_pos:
        step = previous[step]
    return step if previous.get(step) == ghost_pos else ghost_pos


def choose_ghost_game_type():
    """첫 게임은 무작위로 정하고, 이후에는 같은 종류가 연속되지 않도록 번갈아 선택합니다."""
    kinds = ["route", "maze"]
    last = st.session_state.get("last_ghost_game_type")
    choices = [k for k in kinds if k != last] if last in kinds else kinds
    chosen = random.choice(choices)
    st.session_state.last_ghost_game_type = chosen
    return chosen

def begin_ghost_minigame(penalty, resume):
    """유령 접촉 시 선로 추적 또는 미니 미로 중 하나의 퍼즐을 시작합니다."""
    penalty = max(0, int(penalty))
    st.session_state.binbou_pos = st.session_state.position
    st.session_state.binbou_attached = True

    game_type = choose_ghost_game_type()
    game_id = random.randint(100000, 999999)
    # 이전 유령 퍼즐의 결과 애니메이션이 새 퍼즐에 남지 않도록 초기화합니다.
    st.session_state.ladder_animation = None

    if game_type == "maze":
        maze_counter = int(st.session_state.get("ghost_maze_counter", 0))
        maze = build_ghost_maze_puzzle(maze_counter)
        st.session_state.ghost_maze_counter = maze_counter + 1
        st.session_state.ghost_game = {
            "id": game_id,
            "game_type": "maze",
            "penalty": penalty,
            "resume": resume,
            **maze,
        }
        challenge_message = "👿 먹보유령 추격 미로! 벽을 이용해 움직이는 유령을 피하면서 🚪 탈출구까지 이동하세요!"
        st.session_state.last_message = (
            resume.get("base_msg", "")
            + "\n\n👿 **먹보유령 추격 미로!** 벽 🧱은 움직이지 않지만, 열차가 한 칸 움직일 때마다 👿도 벽을 피해 한 칸 추격합니다. "
              "유령의 현재 위치를 보면서 방향 버튼으로 피하고 🚪 탈출구에 먼저 도착하세요!"
        )
        add_event_log("🧭 먹보유령 추격 미로 시작!")
    else:
        puzzle_counter = int(st.session_state.get("ghost_puzzle_counter", 0))
        rungs, bottom_outcomes, puzzle_index = build_ghost_route_puzzle(puzzle_counter)
        st.session_state.ghost_puzzle_counter = puzzle_counter + 1
        st.session_state.ghost_game = {
            "id": game_id,
            "game_type": "route",
            "rungs": rungs,
            "bottom_outcomes": bottom_outcomes,
            "puzzle_index": puzzle_index,
            "penalty": penalty,
            "resume": resume,
        }
        challenge_message = "👿 먹보유령 선로 퍼즐! 눈으로 경로를 따라 탈출구와 연결되는 출발 번호를 찾으세요!"
        st.session_state.last_message = (
            resume.get("base_msg", "")
            + "\n\n👿 **먹보유령 선로 탈출 퍼즐!** 아래의 🚪 탈출구 위치는 공개되어 있습니다. "
              "선로를 눈으로 따라가서 탈출구에 도착하는 위쪽 번호를 선택하세요. 운 요소는 없습니다!"
        )
        add_event_log("🛤️ 먹보유령 선로 탈출 퍼즐 시작!")

    st.session_state.game_phase = "ghost_minigame"
    st.session_state.binbou_effect = {
        "id": random.randint(100000, 999999),
        "type": "challenge",
        "message": challenge_message,
        "penalty": 0,
    }
    st.session_state.play_sound = "ghost"


def continue_after_forward(base_msg, double_quiz, did_win):
    """이동·이벤트·유령·보물상자 처리가 끝난 뒤 승리 또는 퀴즈 단계로 이어갑니다."""
    pending_treasure = st.session_state.get("pending_treasure")
    if pending_treasure:
        st.session_state.pending_treasure = None
        if isinstance(pending_treasure, dict):
            treasure_station = pending_treasure.get("station", STATIONS[st.session_state.position])
            treasure_puzzle = pending_treasure.get("puzzle")
        else:
            # 이전 버전 세션 호환
            treasure_station = pending_treasure
            treasure_puzzle = None
        begin_treasure_minigame(
            treasure_station,
            {
                "kind": "forward",
                "base_msg": base_msg,
                "double_quiz": double_quiz,
                "did_win": did_win,
            },
            puzzle=treasure_puzzle,
        )
        return

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


def finish_ghost_puzzle(game, success, result_msg, ladder_payload=None):
    """유령 퍼즐의 성공/실패를 공통 처리하고 원래 게임 흐름으로 복귀합니다."""
    if not game:
        return
    penalty = int(game.get("penalty", 10))
    resume = game.get("resume", {})
    ghost_start = st.session_state.position

    if success:
        show_binbou_effect(result_msg, 0, "escaped")
        st.session_state.play_sound = "escape"
        reset_binbou_after_catch(distance=8)
    else:
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
    st.session_state.ladder_animation = ladder_payload
    st.session_state.ghost_game = None

    base_msg = resume.get("base_msg", "") + f"\n\n{result_msg}"
    if resume.get("kind") == "forward":
        continue_after_forward(base_msg, bool(resume.get("double_quiz", False)), did_win)
    else:
        st.session_state.game_phase = "ready_to_roll"
        st.session_state.last_message = base_msg + "\n\n다시 주사위를 굴려 보세요."


def resolve_ghost_minigame(choice_index):
    """선로 추적 퍼즐의 선택 결과를 판정합니다."""
    game = st.session_state.get("ghost_game")
    if not game or game.get("game_type", "route") != "route":
        return

    choice_index = int(choice_index)
    if not 0 <= choice_index < 4:
        return

    rungs = game.get("rungs")
    bottom_outcomes = game.get("bottom_outcomes")
    if not isinstance(rungs, list) or not rungs or not isinstance(bottom_outcomes, list) or len(bottom_outcomes) != 4:
        rungs, bottom_outcomes, puzzle_index = build_ghost_route_puzzle(game.get("puzzle_index", 0))
        game["rungs"] = rungs
        game["bottom_outcomes"] = bottom_outcomes
        game["puzzle_index"] = puzzle_index

    end_index = ladder_endpoint(choice_index, rungs)
    success = bottom_outcomes[end_index] == "escape"
    penalty = int(game.get("penalty", 10))

    if success:
        result_msg = (
            f"💨 {choice_index + 1}번 선로를 따라 {end_index + 1}번 끝점의 🚪 탈출구에 도착! 퍼즐 성공! "
            "먹보유령이 8칸 뒤로 물러납니다."
        )
    else:
        result_msg = (
            f"😵 {choice_index + 1}번 선로를 따라가니 {end_index + 1}번 끝점의 👿 유령에게 도착했어요! 점수 -{penalty}점! "
            "먹보유령은 6칸 뒤에서 다시 따라옵니다."
        )

    ladder_payload = {
        "id": game.get("id", random.randint(100000, 999999)),
        "rungs": rungs,
        "selected": choice_index,
        "end": end_index,
        "bottom_outcomes": bottom_outcomes,
        "success": success,
        "message": result_msg,
    }
    finish_ghost_puzzle(game, success, result_msg, ladder_payload=ladder_payload)


def ghost_maze_positions_connected(game, start_pos, target_pos):
    """두 위치가 현재 벽 배치에서 같은 통로로 연결되어 있는지 확인합니다."""
    rows = int(game.get("rows", 5))
    cols = int(game.get("cols", 5))
    walls = {tuple(x) for x in game.get("walls", [])}
    start_pos = tuple(start_pos)
    target_pos = tuple(target_pos)
    if start_pos in walls or target_pos in walls:
        return False
    queue = [start_pos]
    seen = {start_pos}
    head = 0
    while head < len(queue):
        r, c = queue[head]
        head += 1
        if (r, c) == target_pos:
            return True
        for dr, dc in [(-1, 0), (0, -1), (1, 0), (0, 1)]:
            nxt = (r + dr, c + dc)
            if not (0 <= nxt[0] < rows and 0 <= nxt[1] < cols):
                continue
            if nxt in walls or nxt in seen:
                continue
            seen.add(nxt)
            queue.append(nxt)
    return False


def repair_legacy_ghost_maze_position(game):
    """이전 코드에서 분리된 구역에 생성된 유령을 현재 미로의 검증된 위치로 옮깁니다."""
    rows = int(game.get("rows", 5))
    cols = int(game.get("cols", 5))
    player = tuple(game.get("player", game.get("start", [rows - 1, 0])))
    current = tuple(game.get("ghost", [0, cols - 1]))
    if ghost_maze_positions_connected(game, current, player):
        return False

    idx = int(game.get("maze_index", 0)) % len(GHOST_MAZE_PUZZLES)
    spec = GHOST_MAZE_PUZZLES[idx]
    preferred = tuple(spec.get("ghost", (spec.get("ghosts") or [[0, cols - 1]])[0]))
    if preferred != player and ghost_maze_positions_connected(game, preferred, player):
        game["ghost"] = list(preferred)
        game["ghost_start"] = list(preferred)
        game["feedback"] = "👿 먹보유령이 연결된 통로로 이동했습니다. 이제 열차가 움직일 때마다 한 칸씩 추격합니다."
        return True
    return False


def resolve_ghost_maze_move(direction):
    """플레이어가 한 칸 이동하면 먹보유령도 최단 경로로 한 칸 추격합니다."""
    game = st.session_state.get("ghost_game")
    if not game or game.get("game_type") != "maze":
        return

    deltas = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
    if direction not in deltas:
        return

    rows = int(game.get("rows", 5))
    cols = int(game.get("cols", 5))
    r, c = map(int, game.get("player", game.get("start", [rows - 1, 0])))
    dr, dc = deltas[direction]
    nr, nc = r + dr, c + dc
    walls = {tuple(x) for x in game.get("walls", [])}
    # 코드 업데이트 전에 생성된 미로가 세션에 남아 있어도, 분리된 구역의 유령을
    # 검증된 연결 통로로 한 번 보정합니다.
    repair_legacy_ghost_maze_position(game)
    legacy_ghosts = game.get("ghosts", [])
    ghost_before = tuple(game.get("ghost", legacy_ghosts[0] if legacy_ghosts else [0, cols - 1]))
    exit_pos = tuple(game.get("exit", [0, cols - 1]))

    # 벽이나 화면 밖을 누른 것은 실제 한 칸 이동으로 세지 않습니다. 따라서 유령도 움직이지 않습니다.
    if not (0 <= nr < rows and 0 <= nc < cols):
        game["feedback"] = "🚧 미로 밖으로는 갈 수 없어요. 이 시도에서는 👿도 움직이지 않습니다."
        st.session_state.ghost_game = game
        return
    if (nr, nc) in walls:
        game["feedback"] = "🧱 벽에 막혔어요. 이 시도에서는 👿도 움직이지 않습니다."
        st.session_state.ghost_game = game
        return

    game["player"] = [nr, nc]
    game["moves"] = int(game.get("moves", 0)) + 1
    penalty = int(game.get("penalty", 10))

    # 플레이어가 유령의 현재 칸으로 직접 들어가면 즉시 잡힙니다.
    if (nr, nc) == ghost_before:
        result_msg = (
            f"😵 먹보유령이 기다리던 칸으로 들어갔어요! 점수 -{penalty}점! "
            "먹보유령은 6칸 뒤에서 다시 따라옵니다."
        )
        finish_ghost_puzzle(game, False, result_msg)
        return

    # 탈출구에 먼저 들어간 순간 게임 종료. 도착한 뒤 유령에게 추가 턴을 주지 않습니다.
    if (nr, nc) == exit_pos:
        moves = int(game.get("moves", 0))
        result_msg = (
            f"💨 {moves}번 움직여 🚪 탈출구에 먼저 도착! 추격 미로 탈출 성공! "
            "먹보유령이 8칸 뒤로 물러납니다."
        )
        finish_ghost_puzzle(game, True, result_msg)
        return

    # 유령은 랜덤 이동이 아니라 벽을 고려한 최단 경로로 딱 한 칸 추격합니다.
    ghost_after = ghost_maze_next_step(game, ghost_before, (nr, nc))
    game["ghost"] = list(ghost_after)
    if ghost_after != ghost_before:
        game["ghost_moves"] = int(game.get("ghost_moves", 0)) + 1

    if ghost_after == (nr, nc):
        result_msg = (
            f"😵 한 칸 이동한 뒤 먹보유령이 바로 따라잡았어요! 점수 -{penalty}점! "
            "먹보유령은 6칸 뒤에서 다시 따라옵니다."
        )
        finish_ghost_puzzle(game, False, result_msg)
        return

    game["feedback"] = (
        "🚄 열차가 한 칸 이동했고 👿 먹보유령도 벽을 피해 한 칸 추격했습니다. "
        "현재 위치를 보고 다음 방향을 선택하세요."
    )
    # Streamlit rerun 뒤에도 변경된 중첩 dict가 확실히 유지되도록 다시 대입합니다.
    st.session_state.ghost_game = game


def apply_square_event(station_name, pos):
    """파란 칸과 보물상자 칸 이벤트만 처리합니다."""
    sq = SQUARE_TYPES.get(station_name, "normal")
    messages = []
    double_quiz = False
    ghost_penalty = 10

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

    elif sq == "treasure":
        # 보물상자 위치와 퍼즐 유형은 분리합니다. 같은 역에 다시 도착해도
        # 9종 퍼즐 중 하나가 새로 랜덤 선택됩니다. 이동 애니메이션이 끝난 뒤 이 퍼즐을 엽니다.
        puzzle = build_treasure_puzzle(station_name)
        game_name = st.session_state.get("last_treasure_game_type", "car_sort")
        st.session_state.pending_treasure = {
            "station": station_name,
            "game_type": game_name,
            "puzzle": puzzle,
        }
        messages.append(
            f"🎁 보물상자 발견! 이번에는 **{TREASURE_GAME_LABELS.get(game_name, '랜덤 퍼즐')}**이 나왔어요. "
            "말이 도착하면 도전할 수 있습니다."
        )
        add_event_log(
            f"🎁 {station_name}역 보물상자 발견 — {TREASURE_GAME_LABELS.get(game_name, '랜덤 퍼즐')} 대기"
        )

    return "\n\n".join(messages) if messages else None, double_quiz, ghost_penalty

def get_move_animation_delay(event):
    """브라우저 보드의 주사위·플레이어·유령 이동 애니메이션 시간을 계산합니다.

    Streamlit 위젯은 Python rerun 시 즉시 갱신되지만 components.html 안의 이동 애니메이션은
    브라우저에서 비동기로 재생됩니다. 따라서 미니게임이 필요한 경우 이 시간 동안
    game_phase를 ``moving``으로 유지한 뒤 미니게임 화면을 엽니다.
    """
    event = event or {}
    path = event.get("path_indices") or []
    ghost_path = event.get("binbou_path_indices") or []

    # JavaScript runDiceAnim: 900ms 회전 + 600ms 결과 표시
    dice_seconds = 1.50 if event.get("dice") is not None else 0.0
    # JavaScript animateToken: min(path 길이 × 220ms, 2000ms)
    player_seconds = min(len(path) * 0.220, 2.0) if len(path) > 1 else 0.0
    # JavaScript animateGhostToken: min(path 길이 × 170ms, 1500ms)
    ghost_seconds = min(len(ghost_path) * 0.170, 1.5) if len(ghost_path) > 1 else 0.0

    # 이미지 로드/프레임 타이밍 차이를 위한 작은 여유 시간을 둡니다.
    return dice_seconds + player_seconds + ghost_seconds + 0.35


def queue_post_move_action(action, payload, event):
    """말 이동이 끝난 뒤 실행할 미니게임/후속 처리를 예약합니다."""
    st.session_state.pending_post_move = {
        "action": action,
        "payload": payload,
    }
    st.session_state.post_move_delay = get_move_animation_delay(event)
    st.session_state.game_phase = "moving"
    base_source = payload.get("resume", payload) if isinstance(payload, dict) else {}
    base_msg = base_source.get("base_msg", "") if isinstance(base_source, dict) else ""
    if base_msg:
        st.session_state.last_message = base_msg + "\n\n🚃 말이 칸까지 이동하는 중입니다..."
    else:
        st.session_state.last_message = "🚃 말이 칸까지 이동하는 중입니다..."


def activate_pending_post_move():
    """이동 애니메이션이 끝난 뒤 예약된 화면을 실제로 활성화합니다."""
    pending = st.session_state.get("pending_post_move")
    if not pending:
        return False

    st.session_state.pending_post_move = None
    st.session_state.post_move_delay = 0.0
    action = pending.get("action")
    payload = pending.get("payload") or {}

    if action == "ghost":
        begin_ghost_minigame(
            int(payload.get("penalty", 10)),
            payload.get("resume", {}),
        )
        return True

    if action == "forward_continue":
        continue_after_forward(
            payload.get("base_msg", ""),
            bool(payload.get("double_quiz", False)),
            bool(payload.get("did_win", False)),
        )
        return True

    return False


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
    st.session_state.pending_treasure = None
    st.session_state.pending_post_move = None
    st.session_state.post_move_delay = 0.0

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

    # 유령 사다리/보물상자 퍼즐은 말과 유령의 이동 애니메이션이 모두 끝난 뒤 엽니다.
    if touching_ghost:
        if st.session_state.play_sound is None:
            st.session_state.play_sound = "dice"
        queue_post_move_action(
            "ghost",
            {
                "penalty": ghost_penalty,
                "resume": {
                    "kind": "forward",
                    "base_msg": base_msg,
                    "double_quiz": double_quiz,
                    "did_win": did_win,
                },
            },
            st.session_state.animation_event,
        )
        return

    if st.session_state.get("pending_treasure"):
        if st.session_state.play_sound is None:
            st.session_state.play_sound = "dice"
        queue_post_move_action(
            "forward_continue",
            {
                "base_msg": base_msg,
                "double_quiz": double_quiz,
                "did_win": did_win,
            },
            st.session_state.animation_event,
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
    # 오답 직후의 "아쉬워요" 효과는 제출 직후 한 번만 표시합니다.
    # 뒤로 가기 주사위를 굴리는 단계에서는 다시 표시하지 않습니다.
    st.session_state.answer_effect = None
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
        st.session_state.play_sound = "wrong"
        queue_post_move_action(
            "ghost",
            {
                "penalty": 10,
                "resume": {"kind": "backward", "base_msg": base_msg, "did_win": False},
            },
            st.session_state.animation_event,
        )
        return

    st.session_state.play_sound = "wrong"
    st.session_state.game_phase = "ready_to_roll"
    st.session_state.last_message = base_msg + "\n\n다시 주사위를 굴려 보세요."



def continue_after_correct_answer(gained, bonus_msg="", streak_reward_msg=""):
    """정답 처리 또는 연속 정답 보물상자 종료 뒤 원래 게임 흐름으로 복귀합니다."""
    summary = f"✅ 정답! (+{gained}점{bonus_msg})"
    if streak_reward_msg:
        summary += f"\n\n{streak_reward_msg}"

    if st.session_state.quiz_queue:
        st.session_state.current_quiz = st.session_state.quiz_queue.pop(0)
        st.session_state.game_phase = "answering_quiz"
        st.session_state.last_message = summary + "\n\n📝 다음 퀴즈!"
    elif st.session_state.extra_roll:
        st.session_state.extra_roll = False
        st.session_state.game_phase = "ready_to_roll"
        st.session_state.last_message = summary + "\n\n🎲 보너스 주사위 발동!"
    else:
        st.session_state.game_phase = "ready_to_roll"
        st.session_state.last_message = summary + "\n\n주사위를 굴려 보세요."


def begin_streak_treasure(streak, gained, bonus_msg=""):
    """5연속 또는 10연속 정답 달성 시 네 개의 보물상자를 엽니다."""
    rewards = STREAK_TREASURE_REWARDS[:]
    random.shuffle(rewards)
    st.session_state.streak_treasure_game = {
        "id": random.randint(100000, 999999),
        "streak": int(streak),
        "rewards": rewards,
        "selected": None,
        "reward": None,
        "gained": int(gained),
        "bonus_msg": bonus_msg,
    }
    st.session_state.game_phase = "streak_treasure"
    st.session_state.play_sound = "treasure"
    st.session_state.last_message = (
        f"🔥 **{streak}연속 정답 달성!** 특별 보물상자가 열렸습니다!\n\n"
        "🎁 네 개 중 마음에 드는 보물상자 하나를 골라 보세요."
    )
    add_event_log(f"🎁 {streak}연속 정답 특별 보물상자 등장!")


def open_streak_treasure(index):
    """선택한 연속 정답 보물상자를 한 번만 열고 즉시 보상을 지급합니다."""
    game = st.session_state.get("streak_treasure_game")
    if not game or game.get("selected") is not None:
        return
    rewards = list(game.get("rewards", []))
    i = int(index)
    if i < 0 or i >= len(rewards):
        return

    reward = int(rewards[i])
    game["selected"] = i
    game["reward"] = reward
    st.session_state.streak_treasure_game = game

    if reward > 0:
        st.session_state.score += reward
        reward_text = f"+{reward}점"
        result = f"🎉 {i + 1}번 보물상자에서 **{reward_text}** 획득!"
    else:
        reward_text = "꽝"
        result = f"💨 {i + 1}번 보물상자는 **꽝!** 다음 기회를 노려 보세요."

    # 기존 보드의 보물 오버레이를 재사용해 상자를 연 순간 짧은 시각 효과를 보여 줍니다.
    st.session_state.treasure_effect = {
        "id": random.randint(100000, 999999),
        "message": f"보물상자 결과: {reward_text}!",
    }
    st.session_state.play_sound = "treasure"
    st.session_state.last_message = result + "\n\n다른 상자에 무엇이 있었는지도 확인해 보세요."
    add_event_log(f"🎁 연속 정답 보물상자: {reward_text}")


def finish_streak_treasure():
    """상자 결과를 확인한 뒤 퀴즈/추가 주사위/다음 턴으로 이어갑니다."""
    game = st.session_state.get("streak_treasure_game")
    if not game or game.get("selected") is None:
        return
    reward = int(game.get("reward", 0))
    reward_msg = "🎁 특별 보물상자: 꽝" if reward == 0 else f"🎁 특별 보물상자: +{reward}점"
    gained = int(game.get("gained", 10))
    bonus_msg = game.get("bonus_msg", "")
    st.session_state.streak_treasure_game = None
    continue_after_correct_answer(gained, bonus_msg, reward_msg)

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
        # 모든 정답에 짧은 시각 효과를 한 번 표시합니다.
        st.session_state.answer_effect = {
            "id": random.randint(100000, 999999),
            "type": "correct",
            "message": f"정답! +{gained}점",
        }
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

        # 5연속/10연속 정답에서는 다음 단계로 바로 넘어가지 않고 특별 보물상자를 먼저 엽니다.
        st.session_state.quiz_key += 1
        if streak in STREAK_TREASURE_MILESTONES:
            begin_streak_treasure(streak, gained, bonus_msg)
        else:
            continue_after_correct_answer(gained, bonus_msg)
    else:
        st.session_state.correct_streak = 0
        st.session_state.celebration_event = None
        st.session_state.answer_effect = {
            "id": random.randint(100000, 999999),
            "type": "wrong",
            "message": "아쉬워요...",
        }
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
    image_data_uri = f"data:image/{img_mime};base64,{image_b64}"

    payload = {
        "stations":        STATIONS,
        "points":          STATION_POINTS,
        "position":        st.session_state.position,
        "binbou_pos":      st.session_state.binbou_pos,
        "binbou_attached": st.session_state.binbou_attached,
        "binbouEffect":    st.session_state.get("binbou_effect"),
        "goal_index":      GOAL_INDEX,
        "playerName":      st.session_state.player_name,
        "trainKey":        st.session_state.get("selected_train", "KTX 청룡"),
        "train":           TRAIN_TYPES.get(st.session_state.get("selected_train", "KTX 청룡"), TRAIN_TYPES["KTX 청룡"]),
        "lastDice":        st.session_state.last_dice_value,
        "phase":           st.session_state.game_phase,
        "winner":          st.session_state.winner,
        "score":           st.session_state.score,
        "turns":           st.session_state.turns,
        "streak":          st.session_state.correct_streak,
        "squareTypes":     SQUARE_TYPES,
        "soundEnabled":    st.session_state.get("sound_enabled", True),
        "playSound":       st.session_state.get("play_sound"),
        "answerEffect":    st.session_state.get("answer_effect"),
        "event":           st.session_state.animation_event,
        "eventLog":        st.session_state.event_log,
        "treasureEffect":  st.session_state.get("treasure_effect"),
        "celebrationEffect": st.session_state.get("celebration_event"),
        "ladderAnimation": st.session_state.get("ladder_animation"),
    }
    # JSON is embedded in a <script type="application/json"> tag. Escape a literal
    # closing-script sequence so a player name cannot accidentally break the board HTML.
    pj = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")

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
.token{{position:absolute;left:0;top:0;width:34px;height:34px;border-radius:50%;border:3px solid #fff;display:flex;align-items:center;justify-content:center;font-size:18px;z-index:12;pointer-events:none;transform:translate3d(-200px,-200px,0);will-change:transform;backface-visibility:hidden;contain:layout paint style}}
.train-token{{width:68px;height:38px;border-radius:18px;background:rgba(255,255,255,.96);padding:3px 5px;overflow:hidden}}
#token-player img{{width:100%;height:100%;object-fit:contain;display:block;transform:translateZ(0);backface-visibility:hidden}}
#token-player{{box-shadow:0 0 14px 4px rgba(47,128,237,.9);animation:playerPulse 1.4s ease-in-out infinite}}
#token-player.is-moving{{animation:none!important;box-shadow:0 0 9px 2px rgba(47,128,237,.65)!important}}
#token-binbou.is-moving{{animation:none!important;box-shadow:0 0 9px 2px rgba(142,68,173,.65)!important}}
#token-binbou{{background:radial-gradient(circle at 35% 35%,#ff6b6b,#8e44ad);box-shadow:0 0 14px 4px rgba(142,68,173,.9);animation:binbouPulse 1s ease-in-out infinite;z-index:11}}
@keyframes playerPulse{{0%,100%{{box-shadow:0 0 10px 3px rgba(46,204,113,.8)}}50%{{box-shadow:0 0 24px 10px rgba(46,204,113,.3)}}}}
@keyframes binbouPulse{{0%,100%{{box-shadow:0 0 10px 3px rgba(255,0,100,.8)}}50%{{box-shadow:0 0 24px 10px rgba(255,0,100,.3)}}}}
.sdot{{position:absolute;width:11px;height:11px;border-radius:50%;transform:translate(-50%,-50%);z-index:5}}
.sdot-normal{{background:rgba(255,255,255,.12)}}
.sdot-blue{{background:rgba(52,152,219,.6);box-shadow:0 0 7px rgba(52,152,219,.8)}}
.sdot-treasure{{background:#ff9f1c;box-shadow:0 0 10px 3px rgba(255,159,28,.75);width:15px;height:15px;animation:treasureDot 1.2s ease-in-out infinite}}
@keyframes treasureDot{{0%,100%{{transform:translate(-50%,-50%) scale(1) rotate(0)}}50%{{transform:translate(-50%,-50%) scale(1.35) rotate(12deg)}}}}
.sdot-goal{{background:#00ff88;box-shadow:0 0 14px 5px rgba(0,255,136,.8);width:18px;height:18px;animation:goalGlow 1s ease-in-out infinite}}
.sdot-active{{outline:3px solid #fff;outline-offset:2px}}
@keyframes goalGlow{{0%,100%{{box-shadow:0 0 10px 4px rgba(0,255,136,.8)}}50%{{box-shadow:0 0 22px 10px rgba(0,255,136,.4)}}}}
.slabel{{position:absolute;transform:translate(-50%,-215%);background:rgba(10,0,30,.9);color:#2ecc71;padding:2px 7px;border-radius:5px;font-size:11px;white-space:nowrap;z-index:16;pointer-events:none;border:1px solid #2ecc71;animation:labelPop .35s ease-out}}
@keyframes labelPop{{0%{{opacity:0;transform:translate(-50%,-185%) scale(.8)}}100%{{opacity:1;transform:translate(-50%,-215%) scale(1)}}}}
.pbar-wrap{{position:absolute;bottom:0;left:0;right:0;height:7px;background:rgba(255,255,255,.1);z-index:20}}
.pbar{{height:100%;background:linear-gradient(90deg,#2ecc71,#f1c40f,#e74c3c);transition:width .7s ease}}
#dice-overlay{{display:none;position:absolute;inset:0;background:rgba(0,0,0,.55);align-items:center;justify-content:center;z-index:40;border-radius:14px;flex-direction:column;gap:12px}}
#dice-overlay.show{{display:flex}}
#dice-canvas{{width:120px;height:120px;border-radius:18px;box-shadow:0 0 40px rgba(241,196,15,.7)}}
#dice-result-txt{{color:#f1c40f;font-size:2.2em;font-weight:900;text-shadow:0 0 14px rgba(241,196,15,.9);opacity:0;transition:opacity .3s}}
#dice-result-txt.show{{opacity:1}}
#confetti-canvas{{display:none;position:absolute;inset:0;z-index:45;pointer-events:none;border-radius:14px}}
#confetti-canvas.show{{display:block}}
#correct-overlay{{display:none;position:absolute;inset:0;background:radial-gradient(circle,rgba(44,210,130,.34),rgba(7,46,35,.50) 62%,rgba(0,0,0,.18));align-items:center;justify-content:center;flex-direction:column;gap:8px;z-index:46;border-radius:14px;pointer-events:none}}
#correct-overlay.show{{display:flex;animation:correctFade 1.15s ease both}}
#correct-emoji{{font-size:6.2em;filter:drop-shadow(0 0 16px rgba(95,255,175,.9));animation:correctPop .55s cubic-bezier(.18,1.45,.4,1)}}
#correct-txt{{color:#caffdf;font-size:1.65em;font-weight:900;text-shadow:0 0 14px rgba(55,255,155,.75);animation:correctText .65s ease-out}}
#correct-sparkles{{font-size:1.8em;letter-spacing:10px;animation:correctSparkle .8s ease-in-out infinite alternate}}
@keyframes correctPop{{0%{{transform:scale(.18) rotate(-16deg);opacity:0}}70%{{transform:scale(1.18) rotate(4deg);opacity:1}}100%{{transform:scale(1);opacity:1}}}}
@keyframes correctText{{0%{{transform:translateY(14px);opacity:0}}100%{{transform:translateY(0);opacity:1}}}}
@keyframes correctSparkle{{from{{transform:scale(.86);opacity:.55}}to{{transform:scale(1.12);opacity:1}}}}
@keyframes correctFade{{0%{{opacity:0}}15%{{opacity:1}}78%{{opacity:1}}100%{{opacity:0}}}}
#wrong-overlay{{display:none;position:absolute;inset:0;background:rgba(0,0,0,.6);align-items:center;justify-content:center;flex-direction:column;gap:10px;z-index:45;border-radius:14px}}
#wrong-overlay.show{{display:flex;animation:wrongShake .4s ease}}
@keyframes wrongShake{{0%{{transform:translateX(0)}}15%{{transform:translateX(-10px)}}30%{{transform:translateX(10px)}}45%{{transform:translateX(-8px)}}60%{{transform:translateX(8px)}}75%{{transform:translateX(-4px)}}90%{{transform:translateX(4px)}}100%{{transform:translateX(0)}}}}
#ladder-overlay{{display:none;position:absolute;inset:0;background:rgba(16,5,35,.94);align-items:center;justify-content:center;flex-direction:column;z-index:49;border-radius:14px;padding:16px}}
#ladder-overlay.show{{display:flex;animation:ladderFade .28s ease}}
#ladder-title{{color:#fff;font-size:1.35em;font-weight:900;margin-bottom:4px;text-align:center}}
#ladder-sub{{color:#d8c8ef;font-size:.92em;margin-bottom:5px;text-align:center}}
#ladder-svg{{width:min(92%,520px);height:auto;max-height:72%;overflow:visible}}
#ladder-result{{min-height:34px;margin-top:5px;color:#ffd166;font-size:1.25em;font-weight:900;text-align:center}}
@keyframes ladderFade{{from{{opacity:0}}to{{opacity:1}}}}
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
.train-badge-mini{{display:inline-flex;align-items:center;gap:6px;justify-content:flex-end}}
.train-badge-mini img{{width:48px;height:20px;object-fit:contain;background:rgba(255,255,255,.96);border-radius:10px;padding:1px 4px;box-shadow:0 0 10px rgba(0,0,0,.18)}}
.log-item{{font-size:10px;color:#ccc;padding:2px 0;border-bottom:1px solid rgba(255,255,255,.05)}}
.legend-row{{display:flex;align-items:center;gap:5px;font-size:10px;color:#ccc;margin-bottom:3px}}
.legend-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
</style></head>
<body>
<div id="wrap">
  <div id="board-col">
    <div id="board-container">
      <img id="board-img" src="{image_data_uri}" alt="서울 지하철 2호선 게임 보드">
      <div id="token-player" class="token train-token"><img id="token-player-img" alt="열차"></div>
      <div id="token-binbou" class="token" style="display:none">👿</div>
      <div id="station-label" class="slabel" style="display:none"></div>
      <div class="pbar-wrap"><div class="pbar" id="progress-bar" style="width:0%"></div></div>
      <div id="dice-overlay">
        <canvas id="dice-canvas" width="240" height="240"></canvas>
        <div id="dice-result-txt"></div>
      </div>
      <canvas id="confetti-canvas"></canvas>
      <div id="correct-overlay">
        <div id="correct-sparkles">✨ ⭐ ✨</div>
        <div id="correct-emoji">✅</div>
        <div id="correct-txt">정답!</div>
      </div>
      <div id="wrong-overlay">
        <div id="wrong-emoji">😢</div>
        <div id="wrong-txt">아쉬워요...</div>
      </div>
      <div id="treasure-overlay">
        <div id="treasure-emoji">🎁</div>
        <div id="treasure-txt">보물상자 발견!</div>
      </div>
      <div id="ladder-overlay">
        <div id="ladder-title">🛤️ 먹보유령 선로 탈출 퍼즐</div>
        <div id="ladder-sub">선택한 출발점에서 🚪 탈출구까지 경로를 확인합니다!</div>
        <svg id="ladder-svg" viewBox="0 0 440 430" aria-label="먹보유령 선로 탈출 퍼즐 애니메이션"></svg>
        <div id="ladder-result"></div>
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
      <div class="stat-row"><span>열차</span><span class="stat-val" id="s-train">KTX 청룡</span></div>
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
  const playerImg=document.getElementById('token-player-img');
  const tokenBinbou=document.getElementById('token-binbou');
  const label=document.getElementById('station-label');
  const pbar=document.getElementById('progress-bar');
  const winOverlay=document.getElementById('win-overlay');
  const diceOverlay=document.getElementById('dice-overlay');
  const diceCanvas=document.getElementById('dice-canvas');
  const diceResultTxt=document.getElementById('dice-result-txt');
  const ctx2d=diceCanvas.getContext('2d');
  const confettiCanvas=document.getElementById('confetti-canvas');
  const correctOverlay=document.getElementById('correct-overlay');
  const correctTxt=document.getElementById('correct-txt');
  const wrongOverlay=document.getElementById('wrong-overlay');
  const ladderOverlay=document.getElementById('ladder-overlay');
  const ladderSvg=document.getElementById('ladder-svg');
  const ladderResult=document.getElementById('ladder-result');
  const ghostOverlay=document.getElementById('ghost-overlay');
  const ghostTxt=document.getElementById('ghost-txt');
  const treasureOverlay=document.getElementById('treasure-overlay');
  const treasureTxt=document.getElementById('treasure-txt');
  const streakOverlay=document.getElementById('streak-overlay');
  const streakMain=document.getElementById('streak-main');

  document.getElementById('s-score').textContent=d.score||0;
  document.getElementById('s-turns').textContent=d.turns||0;
  document.getElementById('s-streak').textContent=d.streak||0;
  document.getElementById('s-train').textContent=(d.train&&d.train.name)||d.trainKey||'KTX 청룡';
  if(d.train){{
    if(playerImg){{
      playerImg.src=d.train.token_image||d.train.image||'';
      playerImg.alt=d.train.name||'열차';
    }}
    tokenPlayer.style.borderColor=d.train.color||'#2f80ed';
    tokenPlayer.style.boxShadow='0 0 14px 4px '+(d.train.glow||'rgba(47,128,237,.85)');
    tokenPlayer.title=(d.train.name||'열차')+' · '+(d.playerName||'플레이어');
    document.getElementById('s-train').innerHTML='<span class="train-badge-mini"><img src="'+(d.train.image||'')+'" alt="'+(d.train.name||'열차')+'"><span>'+(d.train.name||d.trainKey||'KTX 청룡')+'</span></span>';
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
    // left/top를 매 프레임 바꾸면 레이아웃 계산이 발생할 수 있습니다.
    // 컨테이너 픽셀 좌표로 변환해 transform만 갱신하면 합성 단계에서 훨씬 부드럽게 이동합니다.
    const w=container.clientWidth||container.offsetWidth||1;
    const h=container.clientHeight||container.offsetHeight||1;
    const x=w*(Number(xPct)||0)/100;
    const y=h*(Number(yPct)||0)/100;
    el.dataset.xPct=String(xPct);
    el.dataset.yPct=String(yPct);
    el.style.transform='translate3d('+x+'px,'+y+'px,0) translate(-50%,-50%)';
  }}

  function refreshTokenPositions(){{
    [tokenPlayer,tokenBinbou].forEach(el=>{{
      if(!el||el.dataset.xPct==null||el.dataset.yPct==null)return;
      placeTokenAt(el,Number(el.dataset.xPct),Number(el.dataset.yPct));
    }});
  }}
  if(window.ResizeObserver){{
    const ro=new ResizeObserver(refreshTokenPositions);
    ro.observe(container);
  }} else {{
    window.addEventListener('resize',refreshTokenPositions,{{passive:true}});
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
    tokenPlayer.classList.add('is-moving');
    const ctrl=buildSpline(pathIndices);
    const SAMPLES=Math.max(90,pathIndices.length*28);
    const curve=sampleSpline(ctrl,SAMPLES);
    const finalName=d.stations[pathIndices[pathIndices.length-1]];
    const TOTAL_MS=Math.min(pathIndices.length*220,2000);
    const t0=performance.now();
    function frame(now){{
      const elapsed=now-t0,rawT=Math.min(elapsed/TOTAL_MS,1),eased=easeInOut5(rawT);
      const curvePos=eased*(curve.length-1);
      const idx=Math.min(Math.floor(curvePos),curve.length-1);
      const nextIdx=Math.min(idx+1,curve.length-1);
      const frac=curvePos-idx;
      const a=curve[idx],b=curve[nextIdx];
      const pt={{x:a.x+(b.x-a.x)*frac,y:a.y+(b.y-a.y)*frac}};
      placeTokenAt(tokenPlayer,pt.x,pt.y);
      if(rawT>0.8){{
        const fp=d.points[finalName];
        if(fp){{label.textContent=finalName;label.style.left=fp.x+'%';label.style.top=fp.y+'%';label.style.display='block';}}
      }}
      if(rawT<1)requestAnimationFrame(frame);
      else{{
        const snap=d.points[finalName];
        if(snap){{placeTokenAt(tokenPlayer,snap.x,snap.y);label.textContent=finalName;label.style.left=snap.x+'%';label.style.top=snap.y+'%';label.style.display='block';}}
        tokenPlayer.classList.remove('is-moving');
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

  function runCorrectAnim(){{
    const effect=d.answerEffect||{{}};
    correctTxt.textContent=effect.message||'정답!';
    correctOverlay.classList.add('show');
    setTimeout(()=>correctOverlay.classList.remove('show'),1200);
  }}
  function runWrongAnim(){{
    const effect=d.answerEffect||{{}};
    document.getElementById('wrong-txt').textContent=effect.message||'아쉬워요...';
    wrongOverlay.classList.add('show');
    setTimeout(()=>wrongOverlay.classList.remove('show'),1800);
  }}
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
  function runLadderAnimation(onDone){{
    const effect=d.ladderAnimation;
    if(!effect||!ladderSvg){{onDone&&onDone();return;}}
    const ns='http://www.w3.org/2000/svg';
    const xs=[55,165,275,385], yTop=55, yBottom=350;
    const rungs=(effect.rungs||[]).slice().sort((a,b)=>(a.row||0)-(b.row||0));
    const add=(tag,attrs,text)=>{{const e=document.createElementNS(ns,tag);Object.entries(attrs||{{}}).forEach(([k,v])=>e.setAttribute(k,String(v)));if(text!=null)e.textContent=text;ladderSvg.appendChild(e);return e;}};
    ladderSvg.innerHTML='';
    ladderResult.textContent='';
    ladderOverlay.classList.add('show');

    add('rect',{{x:16,y:8,width:408,height:405,rx:20,fill:'rgba(255,255,255,.035)',stroke:'rgba(255,255,255,.16)','stroke-width':2}});
    xs.forEach((x,i)=>{{
      add('circle',{{cx:x,cy:31,r:18,fill:i===Number(effect.selected)?'#ffd166':'#3a245b',stroke:i===Number(effect.selected)?'#fff1a8':'#8b68bf','stroke-width':3}});
      add('text',{{x:x,y:36,'text-anchor':'middle',fill:i===Number(effect.selected)?'#2b143b':'#fff','font-size':15,'font-weight':900}},String(i+1));
      add('line',{{x1:x,y1:yTop,x2:x,y2:yBottom,stroke:'#f0e7ff','stroke-width':6,'stroke-linecap':'round'}});
    }});

    const rungYs=[];
    rungs.forEach((r,idx)=>{{
      const y=yTop+((idx+1)/(rungs.length+1))*(yBottom-yTop);
      rungYs.push(y);
      const l=Math.max(0,Math.min(2,Number(r.left)||0));
      add('line',{{x1:xs[l],y1:y,x2:xs[l+1],y2:y,stroke:'#ffd166','stroke-width':7,'stroke-linecap':'round'}});
    }});

    const bottomGroups=[];
    const visibleOutcomes=effect.bottom_outcomes||[];
    xs.forEach((x,i)=>{{
      const escaped=visibleOutcomes[i]==='escape';
      const g=add('g',{{opacity:1}});
      const circle=document.createElementNS(ns,'circle');
      circle.setAttribute('cx',x);circle.setAttribute('cy',383);circle.setAttribute('r',25);circle.setAttribute('fill',escaped?'#1f8f69':'#8a3155');circle.setAttribute('stroke',escaped?'#7dffd4':'#ff92b6');circle.setAttribute('stroke-width','2');g.appendChild(circle);
      const txt=document.createElementNS(ns,'text');
      txt.setAttribute('x',x);txt.setAttribute('y',390);txt.setAttribute('text-anchor','middle');txt.setAttribute('fill','#fff');txt.setAttribute('font-size','20');txt.textContent=escaped?'🚪':'👿';g.appendChild(txt);
      ladderSvg.appendChild(g);bottomGroups.push(g);
    }});

    let col=Math.max(0,Math.min(3,Number(effect.selected)||0));
    const pts=[{{x:xs[col],y:yTop}}];
    rungs.forEach((r,idx)=>{{
      const y=rungYs[idx], left=Math.max(0,Math.min(2,Number(r.left)||0));
      pts.push({{x:xs[col],y}});
      if(col===left){{col+=1;pts.push({{x:xs[col],y}});}}
      else if(col===left+1){{col-=1;pts.push({{x:xs[col],y}});}}
    }});
    pts.push({{x:xs[col],y:yBottom}});
    pts.push({{x:xs[col],y:374}});

    const trace=add('polyline',{{points:'','fill':'none',stroke:'#58e6ff','stroke-width':8,'stroke-linecap':'round','stroke-linejoin':'round',opacity:.92}});
    const marker=add('circle',{{cx:pts[0].x,cy:pts[0].y,r:12,fill:'#58e6ff',stroke:'#fff','stroke-width':4}});
    const markerTxt=add('text',{{x:pts[0].x,y:pts[0].y+5,'text-anchor':'middle',fill:'#14213d','font-size':12,'font-weight':900}},'▶');
    const visited=[pts[0]];
    const updateTrace=()=>trace.setAttribute('points',visited.map(p=>p.x+','+p.y).join(' '));
    updateTrace();

    let seg=0;
    function animateSegment(){{
      if(seg>=pts.length-1){{
        const outcomes=effect.bottom_outcomes||[];
        bottomGroups.forEach((g,i)=>{{
          g.setAttribute('opacity','1');
          const c=g.querySelector('circle'),t=g.querySelector('text');
          const escaped=outcomes[i]==='escape';
          c.setAttribute('fill',escaped?'#1f8f69':'#8a3155');
          c.setAttribute('stroke',escaped?'#7dffd4':'#ff92b6');
          t.textContent=escaped?'💨':'👿';
        }});
        const ok=!!effect.success;
        ladderResult.textContent=ok?'🎉 탈출 성공! 먹보유령을 따돌렸어요!':'😵 잡혔어요! 먹보유령이 기다리고 있었어요!';
        ladderResult.style.color=ok?'#83ffd3':'#ff9fbd';
        if(ok)runConfetti();
        setTimeout(()=>{{ladderOverlay.classList.remove('show');onDone&&onDone();}},1500);
        return;
      }}
      const a=pts[seg],b=pts[seg+1];
      const dist=Math.hypot(b.x-a.x,b.y-a.y);
      const dur=Math.max(120,Math.min(430,dist*3.0));
      const t0=performance.now();
      function frame(now){{
        const t=Math.min((now-t0)/dur,1);
        const e=t<.5?2*t*t:1-Math.pow(-2*t+2,2)/2;
        const x=a.x+(b.x-a.x)*e,y=a.y+(b.y-a.y)*e;
        marker.setAttribute('cx',x);marker.setAttribute('cy',y);
        markerTxt.setAttribute('x',x);markerTxt.setAttribute('y',y+5);
        if(t<1)requestAnimationFrame(frame);
        else{{visited.push(b);updateTrace();seg++;animateSegment();}}
      }}
      requestAnimationFrame(frame);
    }}
    setTimeout(animateSegment,350);
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
    tokenBinbou.classList.add('is-moving');
    const ctrl=buildSpline(pathIndices);
    const curve=sampleSpline(ctrl,Math.max(70,pathIndices.length*22));
    const finalName=d.stations[pathIndices[pathIndices.length-1]];
    const totalMs=Math.min(pathIndices.length*170,1500);
    const t0=performance.now();
    function frame(now){{
      const rawT=Math.min((now-t0)/totalMs,1),eased=easeInOut5(rawT);
      const curvePos=eased*(curve.length-1);
      const idx=Math.min(Math.floor(curvePos),curve.length-1);
      const nextIdx=Math.min(idx+1,curve.length-1);
      const frac=curvePos-idx;
      const a=curve[idx],b=curve[nextIdx];
      const pt={{x:a.x+(b.x-a.x)*frac,y:a.y+(b.y-a.y)*frac}};
      placeTokenAt(tokenBinbou,pt.x,pt.y);
      if(rawT<1)requestAnimationFrame(frame);
      else{{
        const snap=d.points[finalName];
        if(snap)placeTokenAt(tokenBinbou,snap.x,snap.y);
        tokenBinbou.classList.remove('is-moving');
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

  // 정답/오답 오버레이는 소리와 분리합니다.
  // 따라서 뒤로 가기 주사위가 wrong 사운드를 사용해도 '아쉬워요'가 다시 뜨지 않습니다.

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
      const afterLadder=()=>{{
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
      }};
      if(d.ladderAnimation)runLadderAnimation(afterLadder);else afterLadder();
      if(d.treasureEffect)runTreasureAnim();
    }}
    if(d.celebrationEffect){{
      // 3연속 이상은 기존의 더 큰 연속정답 효과가 정답 효과 역할을 합니다.
      runStreakCelebration();
    }}else if(d.answerEffect&&d.answerEffect.type==='correct'){{
      runCorrectAnim();
    }}
    if(d.answerEffect&&d.answerEffect.type==='wrong')runWrongAnim();
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

  // 맵 이미지는 HTML에서 직접 로드합니다. JavaScript 오류가 생겨도 맵 자체는 보이도록
  // 하고, 토큰/이벤트 보드는 이미지 로드가 끝난 뒤 초기화합니다.
  if(boardImg.complete && boardImg.naturalWidth>0){{initBoard();}}
  else{{boardImg.onload=initBoard;boardImg.onerror=()=>{{console.error('이미지 로드 실패');initBoard();}};}}
}})();
</script>
</body></html>"""

    st.session_state.play_sound        = None
    st.session_state.answer_effect     = None
    st.session_state.animation_event   = None
    st.session_state.binbou_effect     = None
    st.session_state.treasure_effect   = None
    st.session_state.celebration_event = None
    st.session_state.ladder_animation  = None
    components.html(html, height=820, scrolling=False)


# ═══════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🚃 지하철 2호선 게임")
    st.caption("서울 2호선 · 1인용 · 성수 → 건대입구")

    phase = st.session_state.game_phase

    # ─────────────────────────────────────────────
    # 자주 누르는 게임 조작부는 항상 사이드바 최상단에 둡니다.
    # Streamlit rerun으로 사이드바 스크롤이 위로 초기화되어도
    # 다음 행동을 위해 다시 아래로 스크롤할 필요가 없습니다.
    # ─────────────────────────────────────────────
    if phase == "moving":
        st.subheader("🚃 이동 중")
        st.info("말이 도착 칸까지 이동하고 있습니다. 이동이 끝나면 이벤트 화면이 열립니다.")

    elif phase == "ready_to_roll":
        st.subheader("🎲 지금 할 일: 주사위")
        streak = st.session_state.correct_streak
        if streak >= 3:
            st.success(f"🔥 연속 {streak}정답! 보너스 확률!")
        if st.session_state.active_item == "double_move":
            st.warning("🚄 2배 이동 활성화!")
        if st.session_state.bonus_dice > 0:
            st.info(f"⚡ 주사위 보너스 +{st.session_state.bonus_dice}")
        if st.button("🎲 주사위 굴리기!", key="top_roll_dice", use_container_width=True, type="primary"):
            move_forward(); st.rerun()

    elif phase == "streak_treasure":
        game = st.session_state.get("streak_treasure_game")
        st.subheader("🎁 연속 정답 보물상자")
        if game:
            streak = int(game.get("streak", 5))
            selected = game.get("selected")
            rewards = list(game.get("rewards", STREAK_TREASURE_REWARDS))
            st.success(f"🔥 {streak}연속 정답 보너스! 보물상자 하나를 골라 주세요.")

            if selected is None:
                chest_cols = st.columns(4)
                for i, col in enumerate(chest_cols):
                    with col:
                        if st.button(
                            f"🎁\n{i + 1}번",
                            key=f"streak_chest_{game['id']}_{i}",
                            use_container_width=True,
                            type="primary",
                        ):
                            open_streak_treasure(i); st.rerun()
                st.caption("네 상자에는 +100점, +20점, +10점, 꽝이 하나씩 무작위로 들어 있습니다.")
            else:
                reward = int(game.get("reward", 0))
                if reward > 0:
                    st.success(f"🎉 선택한 {int(selected) + 1}번 상자: +{reward}점!")
                else:
                    st.warning(f"💨 선택한 {int(selected) + 1}번 상자: 꽝!")

                reveal_cols = st.columns(4)
                for i, col in enumerate(reveal_cols):
                    label = "꽝" if int(rewards[i]) == 0 else f"+{int(rewards[i])}점"
                    picked = "✅" if i == int(selected) else ""
                    with col:
                        st.markdown(
                            f"<div style='text-align:center;border:1px solid #777;border-radius:10px;padding:8px 3px'>"
                            f"<div style='font-size:25px'>📦</div><b>{i+1}번</b><br>{label} {picked}</div>",
                            unsafe_allow_html=True,
                        )
                if st.button(
                    "➡️ 계속하기",
                    key=f"streak_chest_continue_{game['id']}",
                    use_container_width=True,
                    type="primary",
                ):
                    finish_streak_treasure(); st.rerun()

    elif phase == "ghost_minigame":
        game = st.session_state.get("ghost_game")
        game_type = game.get("game_type", "route") if game else "route"

        if game_type == "maze":
            st.subheader("👿 지금 할 일: 추격 미로 탈출")
            st.warning("🧭 벽 🧱을 이용해 추격하는 👿 먹보유령을 피하고, 열차를 🚪 탈출구까지 먼저 움직여 주세요.")
            if game:
                render_ghost_maze_preview(game)
                feedback = game.get("feedback", "")
                if feedback:
                    st.info(feedback)

                top_a, top_b, top_c = st.columns([1, 1, 1])
                with top_b:
                    if st.button("⬆️", key=f"ghost_maze_up_{game['id']}", use_container_width=True):
                        resolve_ghost_maze_move("up"); st.rerun()
                left_c, down_c, right_c = st.columns(3)
                with left_c:
                    if st.button("⬅️", key=f"ghost_maze_left_{game['id']}", use_container_width=True):
                        resolve_ghost_maze_move("left"); st.rerun()
                with down_c:
                    if st.button("⬇️", key=f"ghost_maze_down_{game['id']}", use_container_width=True):
                        resolve_ghost_maze_move("down"); st.rerun()
                with right_c:
                    if st.button("➡️", key=f"ghost_maze_right_{game['id']}", use_container_width=True):
                        resolve_ghost_maze_move("right"); st.rerun()
                st.caption(f"현재 이동: {int(game.get('moves', 0))}회 · 유령 이동: {int(game.get('ghost_moves', 0))}회 · 벽에 막힌 시도에는 유령도 움직이지 않습니다.")
            st.caption("🎯 유령은 랜덤으로 움직이지 않습니다. 벽을 피해 현재 열차까지의 최단 경로로 매번 한 칸 추격합니다.")
        else:
            st.subheader("👿 지금 할 일: 탈출 선로 찾기")
            st.warning("🛤️ 선로를 눈으로 따라가서 아래 🚪 탈출구와 이어지는 위쪽 번호를 골라 주세요.")
            if game:
                render_ladder_preview(game)
                ladder_cols = st.columns(4)
                for ladder_idx, col in enumerate(ladder_cols):
                    with col:
                        if st.button(
                            f"{ladder_idx + 1}번",
                            key=f"ghost_ladder_{game['id']}_{ladder_idx}",
                            use_container_width=True,
                            type="primary",
                        ):
                            resolve_ghost_minigame(ladder_idx)
                            st.rerun()
            st.caption("🎯 운 요소 없음: 경로를 정확히 추리하면 반드시 탈출합니다. 성공하면 먹보유령이 8칸 뒤로 물러납니다.")

    elif phase == "treasure_minigame":
        game = st.session_state.get("treasure_game")
        st.subheader("🎁 지금 할 일: 보물 퍼즐")
        if game:
            puzzle = game.get("puzzle", {})
            kind = puzzle.get("game_type", "")
            attempts = int(game.get("attempts", 0))
            max_attempts = int(puzzle.get("max_attempts", TREASURE_MAX_ATTEMPTS))

            st.warning(f"{puzzle.get('icon', '🧩')} **{puzzle.get('title', '보물 퍼즐')}**")
            st.markdown(puzzle.get("prompt", "퍼즐을 완성해 보세요."))

            feedback = game.get("feedback", "")
            if feedback:
                st.error(feedback)
                if puzzle.get("hint"):
                    st.info(f"💡 힌트: {puzzle['hint']}")

            if kind in ("car_sort", "switch_route", "signal_grid", "track_rotate", "cargo_balance", "mastermind"):
                st.caption(
                    f"검사 기회: {max(0, max_attempts - attempts)}회 · "
                    f"첫 검사에서 성공 +{TREASURE_REWARD}점 / 실패 후 성공 +{TREASURE_RETRY_REWARD}점"
                )
            else:
                st.caption(f"퍼즐을 완성하면 +{TREASURE_REWARD}점!")

            # 1) 객차 순서 맞추기
            if kind == "car_sort":
                st.markdown("**목표:** " + " → ".join(puzzle.get("goal", [])))
                for i, item in enumerate(puzzle.get("state", [])):
                    a, b, c = st.columns([1, 4, 1])
                    with a:
                        if st.button("▲", key=f"car_up_{game['id']}_{i}", disabled=(i == 0), use_container_width=True):
                            treasure_puzzle_action("up", i); st.rerun()
                    with b:
                        st.markdown(f"<div style='text-align:center;padding:8px;border:1px solid #ddd;border-radius:8px'>{item}</div>", unsafe_allow_html=True)
                    with c:
                        if st.button("▼", key=f"car_down_{game['id']}_{i}", disabled=(i == len(puzzle.get('state', [])) - 1), use_container_width=True):
                            treasure_puzzle_action("down", i); st.rerun()
                if st.button("✅ 순서 검사", key=f"treasure_check_{game['id']}_{attempts}", use_container_width=True, type="primary"):
                    check_treasure_minigame(); st.rerun()

            # 2) 선로 스위치
            elif kind == "switch_route":
                st.markdown("**보물 선로 지도**")
                for line in puzzle.get("map_lines", []):
                    st.code(line, language=None)
                cols = st.columns(3)
                for i, col in enumerate(cols):
                    direction = "◀ 왼쪽" if puzzle["state"][i] == 0 else "오른쪽 ▶"
                    with col:
                        if st.button(
                            f"{i+1}번\n{direction}",
                            key=f"switch_{game['id']}_{i}_{puzzle['state'][i]}",
                            use_container_width=True,
                        ):
                            treasure_puzzle_action("toggle", i); st.rerun()
                if st.button("🚦 선로 연결 검사", key=f"treasure_check_{game['id']}_{attempts}", use_container_width=True, type="primary"):
                    check_treasure_minigame(); st.rerun()

            # 3) 쉬운 신호등 색 맞추기 퍼즐
            elif kind == "signal_grid":
                goal = puzzle.get("goal", [])
                state = puzzle.get("state", [])
                colors = puzzle.get("colors", ["🔴", "🟡", "🟢"])
                st.markdown("**목표 신호 — 이 모양과 같게 만드세요**")
                for r in range(2):
                    cols = st.columns(3)
                    for c, col in enumerate(cols):
                        idx = r * 3 + c
                        with col:
                            st.markdown(
                                f"<div style='text-align:center;font-size:30px;padding:4px'>{colors[int(goal[idx])]}</div>",
                                unsafe_allow_html=True,
                            )
                st.markdown("**현재 신호 — 색이 다른 칸만 눌러 보세요**")
                for r in range(2):
                    cols = st.columns(3)
                    for c, col in enumerate(cols):
                        idx = r * 3 + c
                        with col:
                            if st.button(
                                colors[int(state[idx])],
                                key=f"light_{game['id']}_{idx}_{state[idx]}",
                                use_container_width=True,
                            ):
                                treasure_puzzle_action("press", idx); st.rerun()
                st.caption("💡 한 칸을 누르면 그 칸만 🔴 → 🟡 → 🟢 → 🔴 순서로 바뀝니다.")
                if st.button("✅ 신호 검사", key=f"treasure_check_{game['id']}_{attempts}", use_container_width=True, type="primary"):
                    check_treasure_minigame(); st.rerun()

            # 4) 선로 타일 회전
            elif kind == "track_rotate":
                cycle = puzzle.get("cycle", ["─", "╲", "│", "╱"])
                st.markdown("**목표 선로**")
                st.markdown("### " + "  ".join(cycle[i] for i in puzzle.get("goal", [])))
                st.markdown("**현재 선로 — 타일을 눌러 회전하세요**")
                cols = st.columns(len(puzzle.get("state", [])))
                for i, col in enumerate(cols):
                    with col:
                        rot = puzzle["state"][i]
                        if st.button(
                            cycle[rot],
                            key=f"track_{game['id']}_{i}_{rot}",
                            use_container_width=True,
                        ):
                            treasure_puzzle_action("rotate", i); st.rerun()
                if st.button("✅ 선로 검사", key=f"treasure_check_{game['id']}_{attempts}", use_container_width=True, type="primary"):
                    check_treasure_minigame(); st.rerun()

            # 5) 기억 카드 짝맞추기
            elif kind == "memory_pairs":
                cards = puzzle.get("cards", [])
                revealed = set(puzzle.get("revealed", []))
                matched = set(puzzle.get("matched", []))
                for r in range(2):
                    cols = st.columns(3)
                    for c, col in enumerate(cols):
                        idx = r * 3 + c
                        visible = idx in revealed or idx in matched
                        label = cards[idx] if visible else "❓"
                        with col:
                            if st.button(
                                label,
                                key=f"memory_{game['id']}_{idx}_{int(visible)}",
                                disabled=(idx in matched or puzzle.get("mismatch", False)),
                                use_container_width=True,
                            ):
                                treasure_puzzle_action("reveal", idx); st.rerun()
                st.caption(f"찾은 짝: {len(matched)//2}/3 · 뒤집은 횟수: {puzzle.get('moves', 0)}")
                if puzzle.get("mismatch"):
                    st.info("두 카드가 달라요. 위치를 기억한 뒤 다시 뒤집어 보세요.")
                    if st.button("↩️ 다시 뒤집기", key=f"memory_hide_{game['id']}", use_container_width=True, type="primary"):
                        treasure_puzzle_action("hide_mismatch"); st.rerun()

            # 6) 미니 선로 미로
            elif kind == "maze":
                rows, cols_n = int(puzzle.get("rows", 5)), int(puzzle.get("cols", 5))
                walls = {tuple(v) for v in puzzle.get("walls", [])}
                pos = tuple(puzzle.get("position", [0, 0]))
                goal = tuple(puzzle.get("goal", [4, 4]))
                grid_lines = []
                for r in range(rows):
                    row = []
                    for c in range(cols_n):
                        cell = (r, c)
                        if cell == pos:
                            row.append("🚂")
                        elif cell == goal:
                            row.append("🎁")
                        elif cell in walls:
                            row.append("⬛")
                        else:
                            row.append("⬜")
                    grid_lines.append(" ".join(row))
                st.markdown("### " + "  \n### ".join(grid_lines))
                st.caption(f"🚂 이동 횟수: {int(puzzle.get('moves', 0))}회 · 🎁 보물까지 길을 찾아보세요!")
                _, up_col, _ = st.columns(3)
                with up_col:
                    if st.button("⬆️", key=f"maze_up_{game['id']}", use_container_width=True):
                        treasure_puzzle_action("up"); st.rerun()
                lcol, dcol, rcol = st.columns(3)
                with lcol:
                    if st.button("⬅️", key=f"maze_left_{game['id']}", use_container_width=True):
                        treasure_puzzle_action("left"); st.rerun()
                with dcol:
                    if st.button("⬇️", key=f"maze_down_{game['id']}", use_container_width=True):
                        treasure_puzzle_action("down"); st.rerun()
                with rcol:
                    if st.button("➡️", key=f"maze_right_{game['id']}", use_container_width=True):
                        treasure_puzzle_action("right"); st.rerun()

            # 7) 화물 균형
            elif kind == "cargo_balance":
                weights = puzzle.get("weights", [])
                sides = puzzle.get("state", [])
                left_total = sum(w for w, side in zip(weights, sides) if side == 0)
                right_total = sum(w for w, side in zip(weights, sides) if side == 1)
                a, b = st.columns(2)
                a.metric("⬅️ 왼쪽 화물칸", f"{left_total} kg")
                b.metric("오른쪽 화물칸 ➡️", f"{right_total} kg")
                for i, weight in enumerate(weights):
                    side_text = "⬅️ 왼쪽" if sides[i] == 0 else "오른쪽 ➡️"
                    if st.button(
                        f"📦 {weight}kg · 현재 {side_text} — 눌러서 반대쪽으로 이동",
                        key=f"cargo_{game['id']}_{i}_{sides[i]}",
                        use_container_width=True,
                    ):
                        treasure_puzzle_action("toggle", i); st.rerun()
                if st.button("⚖️ 균형 검사", key=f"treasure_check_{game['id']}_{attempts}", use_container_width=True, type="primary"):
                    check_treasure_minigame(); st.rerun()

            # 8) 쉬운 색깔 객차 순서 맞추기
            elif kind == "mastermind":
                goal = list(puzzle.get("goal", []))
                state = list(puzzle.get("state", []))

                st.markdown("**목표 객차 순서**")
                goal_cols = st.columns(len(goal))
                for i, col in enumerate(goal_cols):
                    with col:
                        st.markdown(
                            f"<div style='text-align:center;font-size:34px;padding:5px'>{goal[i]}</div>",
                            unsafe_allow_html=True,
                        )

                st.markdown("**현재 객차 순서**")
                state_cols = st.columns(len(state))
                for i, col in enumerate(state_cols):
                    with col:
                        st.markdown(
                            f"<div style='text-align:center;font-size:34px;padding:5px'>{state[i]}</div>",
                            unsafe_allow_html=True,
                        )

                st.caption("아래 ↔ 버튼은 바로 위의 이웃한 두 객차만 서로 바꿉니다.")
                swap_cols = st.columns(max(1, len(state) - 1))
                for i, col in enumerate(swap_cols):
                    with col:
                        if st.button(
                            f"{i+1} ↔ {i+2}",
                            key=f"color_swap_{game['id']}_{i}_{''.join(state)}",
                            use_container_width=True,
                        ):
                            treasure_puzzle_action("swap", i); st.rerun()

                if st.button(
                    "✅ 순서 검사",
                    key=f"treasure_check_{game['id']}_{attempts}",
                    use_container_width=True,
                    type="primary",
                ):
                    check_treasure_minigame(); st.rerun()

            # 9) 숫자 선로 연결 — 1부터 6까지 순서대로 누르는 쉬운 퍼즐
            elif kind == "sliding_tiles":
                tiles = puzzle.get("state", [])
                completed = set(puzzle.get("completed_numbers", []))
                next_number = int(puzzle.get("next_number", 1))

                progress = "  →  ".join(
                    f"✅ {n}" if n in completed else f"⬜ {n}"
                    for n in range(1, 7)
                )
                st.markdown(f"**선로 진행:** {progress}")
                if puzzle.get("last_wrong") is not None:
                    st.warning(f"지금은 **{next_number}**을 눌러야 해요!")
                else:
                    st.caption(f"다음 숫자: {min(next_number, 6)}")

                for r in range(2):
                    cols = st.columns(3)
                    for c, col in enumerate(cols):
                        idx = r * 3 + c
                        if idx >= len(tiles):
                            continue
                        value = int(tiles[idx])
                        with col:
                            if value in completed:
                                st.button(
                                    f"✅ {value}",
                                    key=f"number_path_done_{game['id']}_{idx}_{value}",
                                    disabled=True,
                                    use_container_width=True,
                                )
                            else:
                                if st.button(
                                    f"{value}",
                                    key=f"number_path_{game['id']}_{idx}_{value}_{next_number}",
                                    use_container_width=True,
                                    type="primary" if value == next_number else "secondary",
                                ):
                                    treasure_puzzle_action("number_path", idx); st.rerun()
                st.caption("목표: 숫자의 위치는 상관없이 1 → 2 → 3 → 4 → 5 → 6 순서로 누르세요.")

    elif phase == "waiting_penalty_roll":
        st.subheader("😱 지금 할 일: 뒤로 가기")
        if "skip_penalty" in st.session_state.hand_items:
            st.success("✨ 면제 카드 보유! 자동 면제됩니다.")
        else:
            st.error("오답! 뒤로 가기 주사위 (최대 4칸 후퇴)")
        if st.button("🎲 뒤로 가기 주사위", key="top_penalty_roll", use_container_width=True, type="primary"):
            move_backward(); st.rerun()

    elif phase == "answering_quiz":
        quiz = st.session_state.current_quiz
        if quiz:
            remaining = len(st.session_state.quiz_queue)
            title = "📝 지금 할 일: 퀴즈"
            if remaining > 0:
                title += f" (이후 {remaining}문제 더!)"
            st.subheader(title)
            if st.session_state.score_x2:
                st.warning("💎 점수 2배 활성화! 정답 시 20점!")
            cat_colors = {"지명": "📍", "상식": "🟡", "과학": "🟠", "영어": "🔴", "수수께끼": "🟣"}
            icon = cat_colors.get(quiz['category'], '⚪')
            st.info(f"{icon} [{quiz['category']}]\n\n**{quiz['question']}**")
            for opt_idx, opt in enumerate(quiz["options"]):
                if st.button(
                    opt,
                    key=f"opt_{quiz['quiz_id']}_{opt_idx}_{st.session_state.quiz_key}",
                    use_container_width=True,
                ):
                    submit_answer(opt); st.rerun()

    elif phase == "game_over":
        st.balloons()
        st.success("🎉 건대입구 도착! 게임 클리어!")
        st.metric("최종 점수", st.session_state.score)
        st.metric("총 턴 수", st.session_state.turns)
        if st.button("🔄 다시 하기", key="top_play_again", use_container_width=True, type="primary"):
            init_game(keep_name=True); st.rerun()

    elif phase == "start":
        st.info("🎮 아래 **게임 설정**에서 이름·열차·퀴즈를 정한 뒤 시작해 주세요!")

    # 현재 위치도 상단 조작부 바로 아래에 두어 진행 상황을 쉽게 확인합니다.
    if phase not in ("start",):
        pos = st.session_state.position
        total = len(STATIONS)
        st.progress(pos / (total - 1) if total > 1 else 0)
        st.caption(f"📍 **{STATIONS[pos]}** ({pos+1}/{total})")

    # 아이템은 현재 행동보다 아래에 배치합니다. 최대 3장이라 사이드바를 과도하게 밀어내지 않습니다.
    hand = st.session_state.hand_items
    if hand and phase not in ("start", "game_over"):
        with st.expander(f"🃏 보유 아이템 ({len(hand)}장)", expanded=False):
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
                            elif item_key == "score_up":
                                st.session_state.score_x2 = True
                                st.session_state.hand_items.remove(item_key)
                                add_event_log("💎 점수 2배 카드 준비!")
                            st.rerun()

    st.markdown("---")

    # 게임 설정은 시작 화면에서는 펼치고, 게임 중에는 접어 둡니다.
    with st.expander("⚙️ 게임 설정", expanded=(phase == "start")):
        st.session_state.player_name = st.text_input(
            "플레이어 이름",
            value=st.session_state.get("player_name", "플레이어"),
            key="name_input",
            disabled=phase not in ("start", "game_over"),
        )

        st.subheader("🚄 내 열차 선택")
        train_keys = list(TRAIN_TYPES.keys())
        current_phase_for_train = st.session_state.get("game_phase", "start")
        train_choice_enabled = current_phase_for_train in ("start", "game_over")

        if "train_selector" not in st.session_state or st.session_state.train_selector not in train_keys:
            st.session_state.train_selector = normalize_train_key(
                st.session_state.get("selected_train", "KTX 청룡")
            )

        # 사진을 클릭하면 ?train=... 쿼리로 같은 앱이 다시 열리고, 그 값을 선택 상태로 반영합니다.
        requested_train = get_train_choice_from_query()
        if train_choice_enabled and requested_train in train_keys:
            st.session_state.train_selector = requested_train

        st.session_state.selected_train = normalize_train_key(st.session_state.train_selector)
        st.caption("아래 열차 사진을 직접 클릭해 말을 선택하세요.")
        st.markdown(
            render_train_choice_gallery(st.session_state.selected_train, enabled=train_choice_enabled),
            unsafe_allow_html=True,
        )
        if not train_choice_enabled:
            st.caption("게임 중에는 열차 선택이 잠겨 있습니다.")

        st.subheader("📚 퀴즈 카테고리")
        all_cats = QUIZ_CATEGORIES
        if "selected_categories" not in st.session_state:
            st.session_state.selected_categories = all_cats[:]
        else:
            previous_categories = list(st.session_state.selected_categories)
            if "국어" in previous_categories and "지명" not in previous_categories:
                previous_categories = ["지명" if c == "국어" else c for c in previous_categories]
            st.session_state.selected_categories = [
                c for c in previous_categories if c in all_cats
            ]
        for cat in all_cats:
            checked = cat in st.session_state.selected_categories
            if st.checkbox(cat, value=checked, key=f"cat_{cat}"):
                if cat not in st.session_state.selected_categories:
                    st.session_state.selected_categories.append(cat)
            else:
                if cat in st.session_state.selected_categories:
                    st.session_state.selected_categories.remove(cat)

        if phase == "start":
            if st.button("🎮 게임 시작", key="settings_start", use_container_width=True, type="primary"):
                start_game(); st.rerun()
        else:
            st.caption("게임 중에는 열차와 이름 변경이 잠겨 있습니다.")

        if st.button("🔄 게임 리셋", key="settings_reset", use_container_width=True):
            init_game(keep_name=True); st.rerun()

    if phase == "start":
        with st.expander("📖 게임 방법", expanded=False):
            st.markdown("""
- 🎲 주사위를 굴려 역 이동
- 📝 도착 역에서 퀴즈 풀기
- 👿 먹보유령을 만나면 공개된 선로를 눈으로 따라 🚪 탈출구로 이어지는 출발 번호를 찾기
- 🎁 주황색 보물상자 칸에서는 역마다 다른 퍼즐 미니게임 도전 (성공해야 점수 획득)
- 🔥 3연속 이상 정답이면 축하 특수 효과 등장
- 🎁 5연속·10연속 정답 달성 시 특별 보물상자 4개 중 하나 선택 (+100점 / +20점 / +10점 / 꽝)
- 🃏 아이템 카드를 전략적으로 활용!
- 🏁 건대입구역 도달이 목표!
""")

    with st.expander("🗺️ 칸 종류 설명"):
        st.caption("🔵 **파란 칸** — 보너스 (추가 주사위·점수·아이템)")
        st.caption("🟠 **보물상자 칸** — 9개 역별 퍼즐 미니게임 (클리어해야 점수 획득)")
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
elif phase in ("answering_quiz", "treasure_minigame", "streak_treasure"):
    st.warning(msg)
elif phase in ("waiting_penalty_roll", "ghost_minigame"):
    st.error(msg)
else:
    st.info(msg)

map_bytes, is_jpg = get_map_bytes()
render_board(map_bytes, is_jpg)

# Streamlit의 사이드바는 rerun 직후 갱신되는 반면 보드의 토큰 이동은 브라우저에서
# 비동기로 재생됩니다. 미니게임이 예약된 이동에서는 보드 애니메이션이 끝날 때까지
# 현재 run을 유지한 다음, 다음 rerun에서 미니게임을 표시합니다.
if phase == "moving" and st.session_state.get("pending_post_move"):
    time.sleep(max(0.0, float(st.session_state.get("post_move_delay", 0.0))))
    if activate_pending_post_move():
        st.rerun()
