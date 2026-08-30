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
    },
}


def get_train_choice_from_query():
    """사진 카드 클릭으로 전달된 열차 선택 값을 읽습니다."""
    try:
        value = st.query_params.get("train")
    except Exception:
        try:
            value = st.experimental_get_query_params().get("train")
        except Exception:
            value = None
    if isinstance(value, list):
        value = value[-1] if value else None
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
            href = f"?train={quote(key)}"
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
TREASURE_MAX_ATTEMPTS = 2

TREASURE_GAME_TYPES = [
    "number_signal",
    "code_lock",
    "odd_one_out",
    "station_order",
    "word_scramble",
    "switch_track",
    "pattern",
    "emoji_code",
    "ticket_math",
]

TREASURE_GAME_LABELS = {
    "number_signal": "숫자 신호 퍼즐",
    "code_lock": "암호 자물쇠",
    "odd_one_out": "다른 것 찾기",
    "station_order": "역 순서 퍼즐",
    "word_scramble": "글자 조립",
    "switch_track": "선로 스위치",
    "pattern": "반복 패턴",
    "emoji_code": "이모지 암호",
    "ticket_math": "티켓 계산",
}


def make_choice_puzzle(title, prompt, correct, distractors, icon="🧩", hint=""):
    """정답 위치가 매번 달라지는 객관식 퍼즐을 만듭니다."""
    options = [correct] + list(distractors)
    # 중복 선택지를 제거하면서 4개를 유지합니다.
    deduped = []
    for option in options:
        if option not in deduped:
            deduped.append(option)
    options = deduped[:4]
    random.shuffle(options)
    return {
        "title": title,
        "icon": icon,
        "prompt": prompt,
        "input_type": "choice",
        "options": options,
        "answer": options.index(correct),
        "hint": hint,
    }


def build_treasure_puzzle(station_name, game_type=None):
    """보물상자에 도착할 때마다 9종 중 하나를 랜덤으로 골라 퍼즐을 생성합니다."""
    if game_type not in TREASURE_GAME_TYPES:
        # 바로 직전에 나온 유형은 가능하면 피해서 연속 중복을 줄입니다.
        previous = st.session_state.get("last_treasure_game_type")
        candidates = [g for g in TREASURE_GAME_TYPES if g != previous] or TREASURE_GAME_TYPES
        game_type = random.choice(candidates)
    st.session_state.last_treasure_game_type = game_type

    if game_type == "number_signal":
        start_num = random.randint(1, 4)
        step = random.choice([2, 3, 4])
        seq = [start_num + step * i for i in range(4)]
        correct = seq[-1] + step
        distractors = [correct - 1, correct + 1, correct + step]
        return make_choice_puzzle(
            "🚦 숫자 신호 퍼즐",
            f"역무실 신호판에 **{' → '.join(map(str, seq))} → ?** 가 떴어요. 같은 규칙으로 다음 숫자는?",
            str(correct),
            [str(v) for v in distractors],
            icon="🚦",
            hint=f"앞 숫자에서 항상 같은 수만큼 커집니다. 차이는 {step}입니다.",
        )

    if game_type == "code_lock":
        # 2호선 번호(2), 선로의 두 진행 방향(2), 신호등 기본색 3개(3)
        return {
            "title": "🔐 역무실 암호 자물쇠",
            "icon": "🔐",
            "prompt": (
                "보물상자 자물쇠는 세 자리예요. 첫째 숫자는 **2호선의 번호**, "
                "둘째는 **선로의 진행 방향 수(앞/뒤)**, 셋째는 **신호등 기본색 수**예요. "
                "세 자리 암호를 입력하세요."
            ),
            "input_type": "text",
            "answer": "223",
            "placeholder": "예: 123",
            "hint": "2호선 → 2, 앞/뒤 → 2, 빨강·노랑·초록 → 3",
        }

    if game_type == "odd_one_out":
        return make_choice_puzzle(
            "🔎 철도 친구 중 다른 하나",
            "네 친구 중 **철길 위를 달리지 않는 것** 하나가 숨어 있어요. 누구일까요?",
            "시내버스",
            ["KTX", "SRT", "무궁화호"],
            icon="🔎",
            hint="레일을 따라 달리는 탈것인지 생각해 보세요.",
        )

    if game_type == "station_order":
        return make_choice_puzzle(
            "🗺️ 역 순서 퍼즐",
            "게임 진행 방향으로 **당산 → 영등포구청 → ?** 입니다. 빈칸에 들어갈 역은?",
            "문래",
            ["합정", "신도림", "대림"],
            icon="🗺️",
            hint="현재 게임의 2호선 진행 순서를 떠올려 보세요.",
        )

    if game_type == "word_scramble":
        words = [
            ("장-강-승", "승강장", "기차를 타고 내리는 곳"),
            ("차-동-전", "전동차", "전기로 움직이는 지하철 차량"),
            ("역-승-환", "환승역", "다른 노선으로 갈아탈 수 있는 역"),
            ("표-차-기", "기차표", "기차를 탈 때 필요한 표"),
        ]
        scrambled, answer, clue = random.choice(words)
        return {
            "title": "🔤 철도 글자 조립",
            "icon": "🔤",
            "prompt": f"글자가 뒤섞였어요: **{scrambled}**  \n힌트: {clue}. 올바른 낱말을 입력하세요.",
            "input_type": "text",
            "answer": answer,
            "placeholder": "정답을 입력하세요",
            "hint": f"힌트의 뜻을 가진 {len(answer)}글자 낱말입니다.",
        }

    if game_type == "switch_track":
        start_track = random.choice([1, 2])
        moves = random.choice([
            [1, 1, -1],
            [1, -1, 2],
            [2, -1, 1],
        ])
        final_track = start_track + sum(moves)
        symbols = " → ".join(("오른쪽 1칸" if m == 1 else "오른쪽 2칸" if m == 2 else "왼쪽 1칸") for m in moves)
        distractors = [v for v in range(1, 6) if v != final_track][:3]
        return make_choice_puzzle(
            "🛤️ 선로 스위치 퍼즐",
            f"열차가 **{start_track}번 선로**에서 출발해요. 스위치가 **{symbols}** 순서로 바뀌면 마지막 선로는 몇 번일까요?",
            f"{final_track}번",
            [f"{v}번" for v in distractors],
            icon="🛤️",
            hint="오른쪽은 더하고, 왼쪽은 빼면 됩니다.",
        )

    if game_type == "pattern":
        patterns = [
            (["🚇", "🚆", "🚄", "🚇", "🚆"], "🚄", ["🚇", "🚆", "🚌"]),
            (["🔵", "🔵", "🟠", "🔵", "🔵"], "🟠", ["🔵", "🟢", "🔴"]),
            (["🚉", "🎫", "🚉", "🎫", "🚉"], "🎫", ["🚉", "🚦", "🛤️"]),
        ]
        seq, correct, distractors = random.choice(patterns)
        return make_choice_puzzle(
            "🧠 반복 패턴 찾기",
            f"전광판 패턴이 **{' '.join(seq)} ?** 순서로 반복됩니다. 다음 그림은?",
            correct,
            distractors,
            icon="🧠",
            hint="처음부터 반복되는 묶음을 찾아보세요.",
        )

    if game_type == "emoji_code":
        puzzles = [
            ("🚉 + 🔄", "환승역", ["종착역", "버스정류장", "매표소"]),
            ("🚆 + 🎫", "기차표", ["시간표", "승강장", "기관차"]),
            ("🚇 + 🚪", "스크린도어", ["개찰구", "터널", "철교"]),
        ]
        code, correct, distractors = random.choice(puzzles)
        return make_choice_puzzle(
            "😎 이모지 철도 암호",
            f"전광판에 **{code}** 라는 그림 암호가 나타났어요. 가장 잘 어울리는 말은?",
            correct,
            distractors,
            icon="😎",
            hint="두 그림이 뜻하는 말을 하나로 합쳐 보세요.",
        )

    # ticket_math
    coin500 = random.choice([1, 2, 3])
    coin100 = random.choice([2, 3, 4])
    total = coin500 * 500 + coin100 * 100
    return {
        "title": "🎫 보물열차 티켓 계산",
        "icon": "🎫",
        "prompt": (
            f"보물열차 표를 사려면 동전을 정확히 세어야 해요. **500원짜리 {coin500}개**와 "
            f"**100원짜리 {coin100}개**를 모두 합치면 몇 원일까요?"
        ),
        "input_type": "number",
        "answer": total,
        "hint": "500원 동전의 합과 100원 동전의 합을 각각 구한 뒤 더하세요.",
    }


ITEMS = {
    "double_move":  {"name": "🚄 2배 이동 카드", "desc": "이번 주사위 결과를 2배로!"},
    "skip_penalty": {"name": "✨ 면제 카드",     "desc": "뒤로 가기 주사위 면제"},
    "score_up":     {"name": "💎 점수 2배 카드", "desc": "다음 정답 점수 2배"},
}

QUIZ_CATEGORIES = ["국어", "상식", "과학", "영어", "수수께끼"]

QUIZZES = [
    # ══════════════ 국어 (30문제 · 8세 수준) ══════════════
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
    {'category': '국어', 'question': "'전동차가 천천히 승강장으로 들어옵니다.'에서 움직임을 나타내는 말은 무엇일까요?",
     'options': ['전동차가', '천천히', '들어옵니다', '승강장으로'], 'answer': 2},
    {'category': '국어', 'question': "'출발'과 반대되는 뜻의 말로 가장 알맞은 것은 무엇일까요?",
     'options': ['도착', '환승', '운전', '통과'], 'answer': 0},
    {'category': '국어', 'question': "'기차가 빵빵 기적을 울렸습니다.'에서 소리를 흉내 낸 말은 무엇일까요?",
     'options': ['기차가', '기적을', '울렸습니다', '빵빵'], 'answer': 3},
    {'category': '국어', 'question': "'환승'의 뜻으로 가장 알맞은 것은 무엇일까요?",
     'options': ['기차에서 잠을 자는 것', '한 교통수단에서 다른 교통수단으로 갈아타는 것', '표를 잃어버리는 것', '역 이름을 바꾸는 것'], 'answer': 1},
    {'category': '국어', 'question': '다음 중 띄어쓰기가 바르게 된 지하철 안내 문장은 무엇일까요?',
     'options': ['이번역은 시청역입니다.', '이번 역은시청역입니다.', '이번 역은 시청역입니다.', '이번역은시청역입니다.'], 'answer': 2},
    {'category': '국어', 'question': "'빠르게 달리는 급행열차'에서 '빠르게'와 반대되는 말은 무엇일까요?",
     'options': ['천천히', '높게', '가깝게', '조용히'], 'answer': 0},
    {'category': '국어', 'question': "'민지는 건대입구역에서 친구를 만났습니다.'에서 민지가 친구를 만난 곳은 어디일까요?",
     'options': ['민지네 집', '학교', '공원', '건대입구역'], 'answer': 3},
    {'category': '국어', 'question': "'전동차 문이 닫혀서 민수는 다음 열차를 기다렸습니다.'에서 민수가 다음 열차를 기다린 까닭은 무엇일까요?",
     'options': ['비가 왔기 때문에', '문이 닫혔기 때문에', '표가 너무 컸기 때문에', '열차가 너무 느렸기 때문에'], 'answer': 1},
    {'category': '국어', 'question': '지하철을 타는 순서로 가장 자연스러운 것은 무엇일까요?',
     'options': ['열차 탑승 → 승강장 도착 → 열차 기다림', '열차 기다림 → 열차 탑승 → 승강장 도착', '승강장 도착 → 열차 기다림 → 열차 탑승', '열차 탑승 → 열차 기다림 → 승강장 도착'], 'answer': 2},
    {'category': '국어', 'question': "'이번 역은 왕십리역입니다. 내리실 문은 오른쪽입니다.'에서 알 수 있는 내용은 무엇일까요?",
     'options': ['왕십리역에서 오른쪽 문이 열린다', '열차가 고장 났다', '다음 역은 부산이다', '오른쪽 문은 절대 열리지 않는다'], 'answer': 0},

    # ══════════════ 상식 (30문제 · 8세 수준) ══════════════
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
    {'category': '상식', 'question': '수도권 지하철에서 다른 노선의 열차로 갈아타는 것을 무엇이라고 할까요?',
     'options': ['주차', '세차', '환승', '횡단'], 'answer': 2},
    {'category': '상식', 'question': '지하철 노선도는 무엇을 알아보는 데 가장 도움이 될까요?',
     'options': ['역의 순서와 갈아타는 곳', '오늘의 급식', '축구 경기 점수', '날씨의 온도'], 'answer': 0},
    {'category': '상식', 'question': '승강장 안전문(스크린도어)의 중요한 역할은 무엇일까요?',
     'options': ['열차를 더 빨리 달리게 한다', '역 이름을 바꾼다', '열차 바퀴를 씻는다', '승객이 선로 쪽으로 떨어지는 사고를 막는 데 도움을 준다'], 'answer': 3},
    {'category': '상식', 'question': '서울 지하철 2호선을 노선도에서 나타내는 대표 색은 무엇일까요?',
     'options': ['보라색', '초록색', '검은색', '주황색'], 'answer': 1},
    {'category': '상식', 'question': '열차를 기다릴 때 가장 안전한 행동은 무엇일까요?',
     'options': ['선로 가까이 얼굴을 내민다', '승강장에서 뛰어다닌다', '안전선 안쪽에서 차례로 기다린다', '문이 열리기 전에 밀고 들어간다'], 'answer': 2},
    {'category': '상식', 'question': '지하철 문이 열렸을 때 사람이 많이 내리고 있다면 어떻게 하는 것이 좋을까요?',
     'options': ['내리는 사람이 먼저 내린 뒤 탄다', '먼저 밀고 탄다', '문 앞에 가방을 놓는다', '반대편으로 뛰어간다'], 'answer': 0},
    {'category': '상식', 'question': '교통카드는 주로 무엇을 위해 사용할까요?',
     'options': ['열차를 직접 운전하기 위해', '역 이름을 정하기 위해', '기차 바퀴를 고치기 위해', '대중교통 요금을 편리하게 내기 위해'], 'answer': 3},
    {'category': '상식', 'question': '기차나 지하철에서 물건을 잃어버렸을 때 도움을 요청하기 좋은 곳은 어디일까요?',
     'options': ['선로 안쪽', '역무실이나 직원', '운전실 문 앞', '터널 안'], 'answer': 1},
    {'category': '상식', 'question': '열차가 운행을 끝내는 마지막 역을 흔히 무엇이라고 할까요?',
     'options': ['환승역', '출발선', '종착역', '정류장 표지판'], 'answer': 2},
    {'category': '상식', 'question': '열차 안에서 큰 가방을 들고 있을 때 다른 승객을 배려하는 행동은 무엇일까요?',
     'options': ['다른 사람의 이동을 방해하지 않게 잘 챙긴다', '통로 한가운데 놓는다', '문 앞을 막는다', '좌석 여러 개를 가방으로 차지한다'], 'answer': 0},

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
    st.session_state.score_x2         = False
    st.session_state.event_log         = []
    st.session_state.ghost_game        = None
    st.session_state.treasure_game     = None
    st.session_state.pending_treasure  = None
    st.session_state.last_treasure_game_type = None
    st.session_state.pending_post_move = None
    st.session_state.post_move_delay   = 0.0
    st.session_state.treasure_effect   = None
    st.session_state.celebration_event = None
    st.session_state.ladder_animation  = None


if "position" not in st.session_state:
    init_game(keep_name=False)


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
    """보물상자 칸에 도착하면 도착 시 미리 랜덤 선택된 퍼즐을 시작합니다."""
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
        + f"\n\n🎁 **{station_name}역 보물상자 발견!** 미니게임을 클리어하면 점수를 얻습니다. "
          f"첫 성공은 +{TREASURE_REWARD}점, 재도전 성공은 +{TREASURE_RETRY_REWARD}점!"
    )
    add_event_log(f"🎁 {station_name}역 보물상자 미니게임 시작!")


def normalize_puzzle_text(value):
    return "".join(str(value).strip().lower().split())


def resolve_treasure_minigame(answer_value):
    """보물상자 퍼즐 답을 판정하고 성공해야만 점수를 지급합니다."""
    game = st.session_state.get("treasure_game")
    if not game:
        return
    puzzle = game.get("puzzle", {})
    input_type = puzzle.get("input_type", "choice")

    if input_type == "choice":
        is_correct = int(answer_value) == int(puzzle.get("answer", -1))
    elif input_type == "number":
        try:
            is_correct = int(answer_value) == int(puzzle.get("answer"))
        except (TypeError, ValueError):
            is_correct = False
    else:
        is_correct = normalize_puzzle_text(answer_value) == normalize_puzzle_text(puzzle.get("answer", ""))

    attempts_before = int(game.get("attempts", 0))
    resume = game.get("resume", {})
    station = game.get("station", "보물상자")

    if is_correct:
        reward = TREASURE_REWARD if attempts_before == 0 else TREASURE_RETRY_REWARD
        st.session_state.score += reward
        result_msg = f"🎉 {puzzle.get('title', '퍼즐')} 클리어! 보물상자에서 **+{reward}점** 획득!"
        st.session_state.treasure_effect = {
            "id": random.randint(100000, 999999),
            "message": f"퍼즐 성공! +{reward}점!",
        }
        st.session_state.play_sound = "treasure"
        add_event_log(f"🏆 {station}역 보물상자 퍼즐 성공! +{reward}점")
        st.session_state.treasure_game = None
        base_msg = resume.get("base_msg", "") + f"\n\n{result_msg}"
        continue_after_forward(base_msg, bool(resume.get("double_quiz", False)), bool(resume.get("did_win", False)))
        return

    game["attempts"] = attempts_before + 1
    if game["attempts"] < TREASURE_MAX_ATTEMPTS:
        game["feedback"] = "❌ 아쉽습니다! 힌트를 보고 한 번 더 도전하세요."
        st.session_state.last_message = (
            resume.get("base_msg", "")
            + "\n\n❌ 첫 번째 도전 실패! 아직 한 번의 기회가 남아 있습니다."
        )
        st.session_state.play_sound = "wrong"
        add_event_log(f"🧩 {station}역 보물 퍼즐 1차 실패 — 재도전!")
        return

    correct_answer = puzzle.get("answer")
    if input_type == "choice":
        options = puzzle.get("options", [])
        if isinstance(correct_answer, int) and 0 <= correct_answer < len(options):
            correct_answer = options[correct_answer]
    result_msg = f"💨 두 번의 도전을 모두 사용했습니다. 이번 보물상자는 **0점**입니다. 정답: {correct_answer}"
    st.session_state.treasure_game = None
    st.session_state.play_sound = "wrong"
    add_event_log(f"📦 {station}역 보물상자 미니게임 실패 — 점수 없음")
    base_msg = resume.get("base_msg", "") + f"\n\n{result_msg}"
    continue_after_forward(base_msg, bool(resume.get("double_quiz", False)), bool(resume.get("did_win", False)))


def generate_ladder_layout():
    """4줄 사다리의 가로 연결선과 아래쪽 결과를 생성합니다.

    각 가로선은 인접한 두 세로줄만 연결하며, 위에서 아래로 따라가면
    시작 위치 4개가 서로 다른 끝점 4개에 일대일로 연결됩니다.
    """
    row_count = 11
    rungs = []
    last_left = None
    for row in range(row_count):
        candidates = [0, 1, 2]
        if last_left is not None and len(candidates) > 1:
            weighted = [c for c in candidates if c != last_left]
            left = random.choice(weighted if random.random() < 0.72 else candidates)
        else:
            left = random.choice(candidates)
        rungs.append({"row": row, "left": left})
        last_left = left

    bottom_outcomes = ["escape", "escape", "caught", "caught"]
    random.shuffle(bottom_outcomes)
    return rungs, bottom_outcomes


def ladder_endpoint(start_index, rungs):
    """선택한 시작 번호가 실제 사다리를 따라 도착하는 끝점 번호를 계산합니다."""
    col = int(start_index)
    for rung in sorted(rungs, key=lambda r: r.get("row", 0)):
        left = int(rung.get("left", -1))
        if col == left:
            col += 1
        elif col == left + 1:
            col -= 1
    return max(0, min(col, 3))


def render_ladder_preview(game):
    """선택 전에는 결과를 숨긴 실제 사다리 모양을 사이드바에 보여줍니다."""
    if not game:
        return
    rungs = game.get("rungs", [])
    data = json.dumps({"rungs": rungs}, ensure_ascii=False)
    preview_html = f"""
    <div style="font-family:'Noto Sans KR',sans-serif;background:#16072a;border:1px solid #6741a8;border-radius:12px;padding:8px 6px 5px;color:white">
      <div style="text-align:center;font-size:12px;font-weight:700;margin-bottom:3px">위에서 하나를 고르고 사다리를 따라가요!</div>
      <svg id="ladder-preview" viewBox="0 0 360 255" style="width:100%;height:225px;display:block"></svg>
    </div>
    <script>
    (()=>{{
      const d={data};
      const svg=document.getElementById('ladder-preview');
      const ns='http://www.w3.org/2000/svg';
      const xs=[45,135,225,315], y0=32, y1=215;
      const add=(tag,attrs,text)=>{{const e=document.createElementNS(ns,tag);Object.entries(attrs||{{}}).forEach(([k,v])=>e.setAttribute(k,v));if(text!=null)e.textContent=text;svg.appendChild(e);return e;}};
      xs.forEach((x,i)=>{{
        add('text',{{x,y:18,'text-anchor':'middle',fill:'#fff','font-size':'14','font-weight':'700'}},String(i+1));
        add('line',{{x1:x,y1:y0,x2:x,y2:y1,stroke:'#e7d8ff','stroke-width':'5','stroke-linecap':'round'}});
        add('circle',{{cx:x,cy:y1+17,r:12,fill:'#3c245f',stroke:'#9b75d6','stroke-width':'2'}});
        add('text',{{x,y:y1+21,'text-anchor':'middle',fill:'#fff','font-size':'13','font-weight':'700'}},'?');
      }});
      (d.rungs||[]).forEach((r,idx)=>{{
        const y=y0+((idx+1)/((d.rungs||[]).length+1))*(y1-y0);
        const l=Math.max(0,Math.min(2,Number(r.left)||0));
        add('line',{{x1:xs[l],y1:y,x2:xs[l+1],y2:y,stroke:'#ffd166','stroke-width':'5','stroke-linecap':'round'}});
      }});
    }})();
    </script>
    """
    components.html(preview_html, height=250, scrolling=False)


def begin_ghost_minigame(penalty, resume):
    """유령 접촉 시 즉시 감점하지 않고 4개 사다리 미니게임을 시작합니다."""
    penalty = max(0, int(penalty))
    st.session_state.binbou_pos = st.session_state.position
    st.session_state.binbou_attached = True

    # 실제 사다리 구조를 먼저 만든 뒤, 아래쪽 결과 두 칸은 탈출 / 두 칸은 잡힘으로 정합니다.
    rungs, bottom_outcomes = generate_ladder_layout()

    st.session_state.ghost_game = {
        "id": random.randint(100000, 999999),
        "rungs": rungs,
        "bottom_outcomes": bottom_outcomes,
        "penalty": penalty,
        "resume": resume,
    }
    st.session_state.game_phase = "ghost_minigame"
    st.session_state.binbou_effect = {
        "id": random.randint(100000, 999999),
        "type": "challenge",
        "message": "👿 먹보유령과 사다리 게임! 4개 중 하나를 고르세요. 2개는 탈출, 2개는 잡힘!",
        "penalty": 0,
    }
    st.session_state.play_sound = "ghost"
    st.session_state.last_message = (
        resume.get("base_msg", "")
        + "\n\n👿 **먹보유령 사다리 게임!** 4개의 사다리 중 하나를 골라 보세요. "
          "두 사다리는 탈출, 나머지 두 사다리는 먹보유령에게 잡혀요!"
    )
    add_event_log("🪜 먹보유령 사다리 게임 시작!")


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


def resolve_ghost_minigame(choice_index):
    """4개 사다리 미니게임 결과를 처리한 뒤 원래 게임 흐름으로 복귀합니다."""
    game = st.session_state.get("ghost_game")
    if not game:
        return

    choice_index = int(choice_index)
    if not 0 <= choice_index < 4:
        return

    # 이전 버전 세션이 남아 있어도 실제 사다리 규칙으로 안전하게 전환합니다.
    rungs = game.get("rungs")
    bottom_outcomes = game.get("bottom_outcomes")
    if not isinstance(rungs, list) or not rungs or not isinstance(bottom_outcomes, list) or len(bottom_outcomes) != 4:
        rungs, bottom_outcomes = generate_ladder_layout()
        game["rungs"] = rungs
        game["bottom_outcomes"] = bottom_outcomes

    penalty = int(game.get("penalty", 10))
    resume = game.get("resume", {})
    ghost_start = st.session_state.position
    end_index = ladder_endpoint(choice_index, rungs)
    success = bottom_outcomes[end_index] == "escape"

    if success:
        result_msg = (
            f"💨 {choice_index + 1}번에서 출발해 {end_index + 1}번 끝점 도착! 탈출 성공! "
            "먹보유령이 8칸 뒤로 물러납니다."
        )
        show_binbou_effect(result_msg, 0, "escaped")
        st.session_state.play_sound = "escape"
        reset_binbou_after_catch(distance=8)
    else:
        result_msg = (
            f"😵 {choice_index + 1}번에서 출발해 {end_index + 1}번 끝점 도착! 먹보유령에게 잡혔어요! 점수 -{penalty}점! "
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
    st.session_state.ladder_animation = {
        "id": game.get("id", random.randint(100000, 999999)),
        "rungs": rungs,
        "selected": choice_index,
        "end": end_index,
        "bottom_outcomes": bottom_outcomes,
        "success": success,
        "message": result_msg,
    }
    st.session_state.ghost_game = None

    base_msg = resume.get("base_msg", "") + f"\n\n{result_msg}"
    if resume.get("kind") == "forward":
        continue_after_forward(base_msg, bool(resume.get("double_quiz", False)), did_win)
    else:
        st.session_state.game_phase = "ready_to_roll"
        st.session_state.last_message = base_msg + "\n\n다시 주사위를 굴려 보세요."


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
        game_name = st.session_state.get("last_treasure_game_type", "number_signal")
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
.token{{position:absolute;width:34px;height:34px;border-radius:50%;border:3px solid #fff;display:flex;align-items:center;justify-content:center;font-size:18px;z-index:12;pointer-events:none;transform:translate(-50%,-50%)}}
.train-token{{width:68px;height:38px;border-radius:18px;background:rgba(255,255,255,.96);padding:3px 5px;overflow:hidden}}
#token-player img{{width:100%;height:100%;object-fit:contain;display:block;filter:drop-shadow(0 1px 2px rgba(0,0,0,.25))}}
#token-player{{box-shadow:0 0 14px 4px rgba(47,128,237,.9);animation:playerPulse 1.4s ease-in-out infinite}}
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
      <div id="wrong-overlay">
        <div id="wrong-emoji">😢</div>
        <div id="wrong-txt">아쉬워요...</div>
      </div>
      <div id="treasure-overlay">
        <div id="treasure-emoji">🎁</div>
        <div id="treasure-txt">보물상자 발견!</div>
      </div>
      <div id="ladder-overlay">
        <div id="ladder-title">🪜 먹보유령 사다리 게임</div>
        <div id="ladder-sub">선택한 출발점에서 실제 사다리를 따라 내려갑니다!</div>
        <svg id="ladder-svg" viewBox="0 0 440 430" aria-label="먹보유령 사다리 게임 애니메이션"></svg>
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
      playerImg.src=d.train.image||'';
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
    xs.forEach((x,i)=>{{
      const g=add('g',{{opacity:.18}});
      const circle=document.createElementNS(ns,'circle');
      circle.setAttribute('cx',x);circle.setAttribute('cy',383);circle.setAttribute('r',25);circle.setAttribute('fill','#4a3467');circle.setAttribute('stroke','#a58acb');circle.setAttribute('stroke-width','2');g.appendChild(circle);
      const txt=document.createElementNS(ns,'text');
      txt.setAttribute('x',x);txt.setAttribute('y',389);txt.setAttribute('text-anchor','middle');txt.setAttribute('fill','#fff');txt.setAttribute('font-size','20');txt.textContent='?';g.appendChild(txt);
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

  // 맵 이미지는 HTML에서 직접 로드합니다. JavaScript 오류가 생겨도 맵 자체는 보이도록
  // 하고, 토큰/이벤트 보드는 이미지 로드가 끝난 뒤 초기화합니다.
  if(boardImg.complete && boardImg.naturalWidth>0){{initBoard();}}
  else{{boardImg.onload=initBoard;boardImg.onerror=()=>{{console.error('이미지 로드 실패');initBoard();}};}}
}})();
</script>
</body></html>"""

    st.session_state.play_sound        = None
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

    elif phase == "ghost_minigame":
        game = st.session_state.get("ghost_game")
        st.subheader("👿 지금 할 일: 사다리 선택")
        st.warning("🪜 4개의 사다리 중 하나를 골라 주세요! 2개는 탈출, 2개는 먹보유령에게 잡힙니다.")
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
        st.caption("🎯 성공 확률 50%! 탈출하면 감점 없이 먹보유령이 8칸 뒤로 물러납니다.")

    elif phase == "treasure_minigame":
        game = st.session_state.get("treasure_game")
        st.subheader("🎁 지금 할 일: 보물상자 퍼즐")
        if game:
            puzzle = game.get("puzzle", {})
            attempts = int(game.get("attempts", 0))
            remaining = TREASURE_MAX_ATTEMPTS - attempts
            st.warning(f"{puzzle.get('icon', '🧩')} **{puzzle.get('title', '보물 퍼즐')}**")
            st.markdown(puzzle.get("prompt", "퍼즐을 풀어 보세요."))
            st.caption(f"남은 기회: {remaining}회 · 첫 성공 +{TREASURE_REWARD}점 / 재도전 성공 +{TREASURE_RETRY_REWARD}점")

            feedback = game.get("feedback", "")
            if feedback:
                st.error(feedback)
                if puzzle.get("hint"):
                    st.info(f"💡 힌트: {puzzle['hint']}")

            input_type = puzzle.get("input_type", "choice")
            if input_type == "choice":
                for option_idx, option in enumerate(puzzle.get("options", [])):
                    if st.button(
                        str(option),
                        key=f"treasure_{game['id']}_{attempts}_{option_idx}",
                        use_container_width=True,
                    ):
                        resolve_treasure_minigame(option_idx)
                        st.rerun()
            elif input_type == "number":
                answer_num = st.number_input(
                    "정답 숫자",
                    min_value=0,
                    step=100,
                    key=f"treasure_number_{game['id']}_{attempts}",
                )
                if st.button("🔓 정답 확인", key=f"treasure_submit_{game['id']}_{attempts}", use_container_width=True, type="primary"):
                    resolve_treasure_minigame(answer_num)
                    st.rerun()
            else:
                answer_text = st.text_input(
                    "정답",
                    placeholder=puzzle.get("placeholder", "정답을 입력하세요"),
                    key=f"treasure_text_{game['id']}_{attempts}",
                )
                if st.button("🔓 정답 확인", key=f"treasure_submit_{game['id']}_{attempts}", use_container_width=True, type="primary"):
                    resolve_treasure_minigame(answer_text)
                    st.rerun()

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
            cat_colors = {"국어": "🟢", "상식": "🟡", "과학": "🟠", "영어": "🔴", "수수께끼": "🟣"}
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
- 👿 먹보유령에게 잡히면 4개 사다리 중 하나를 선택! 2개는 탈출, 2개는 잡힘
- 🎁 주황색 보물상자 칸에서는 역마다 다른 퍼즐 미니게임 도전 (성공해야 점수 획득)
- 🔥 3연속 이상 정답이면 축하 특수 효과 등장
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
elif phase in ("answering_quiz", "treasure_minigame"):
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
