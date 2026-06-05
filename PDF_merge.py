"""
서울 지하철 2호선 주사위 퀴즈 게임
실행: streamlit run seoul_subway_quiz_game.py

게임 규칙
- 2인용입니다.
- 출발역은 2호선 성수역, 도착역은 2호선 잠실역입니다.
- 짧은 방향이 아니라 성수 → 뚝섬 → ... → 강남 → ... → 잠실로 크게 돌아가는 긴 경로를 사용합니다.
- 자기 차례에 주사위를 굴려 전진한 뒤, 도착한 역에서 객관식 퀴즈를 풉니다.
- 맞히면 같은 플레이어가 다시 주사위를 굴립니다.
- 틀리면 벌칙 주사위를 굴리고, 나온 눈만큼 후퇴한 뒤 차례가 넘어갑니다.

주의
- 기본 지도는 서울시/서울교통 관련 공개 노선도 PDF URL을 화면에 임베드합니다.
- 인터넷 연결이 없거나 PDF 임베드가 막히면, 사이드바에서 직접 보유한 실제 노선도 이미지/PDF를 업로드해 사용하세요.
"""

from __future__ import annotations

import base64
import html
import random
from dataclasses import dataclass
from typing import Dict, List, Optional

import streamlit as st
import streamlit.components.v1 as components


APP_TITLE = "🚇 서울 지하철 2호선 주사위 퀴즈 게임"
LINE_COLOR = "#00A84D"  # Seoul Subway Line 2 green
DEFAULT_MAP_URL = "https://english.seoul.go.kr/wp-content/uploads/2014/02/eng_metrolines.pdf"


# 성수 → 잠실의 짧은 방향(성수-건대입구-구의-강변-잠실나루-잠실)이 아니라,
# 2호선 본선을 크게 돌아가는 긴 방향으로 구성했습니다.
ROUTE: List[Dict[str, str]] = [
    {"code": "211", "name": "성수", "english": "Seongsu"},
    {"code": "210", "name": "뚝섬", "english": "Ttukseom"},
    {"code": "209", "name": "한양대", "english": "Hanyang Univ."},
    {"code": "208", "name": "왕십리", "english": "Wangsimni"},
    {"code": "207", "name": "상왕십리", "english": "Sangwangsimni"},
    {"code": "206", "name": "신당", "english": "Sindang"},
    {"code": "205", "name": "동대문역사문화공원", "english": "Dongdaemun History & Culture Park"},
    {"code": "204", "name": "을지로4가", "english": "Euljiro 4-ga"},
    {"code": "203", "name": "을지로3가", "english": "Euljiro 3-ga"},
    {"code": "202", "name": "을지로입구", "english": "Euljiro 1-ga"},
    {"code": "201", "name": "시청", "english": "City Hall"},
    {"code": "243", "name": "충정로", "english": "Chungjeongno"},
    {"code": "242", "name": "아현", "english": "Ahyeon"},
    {"code": "241", "name": "이대", "english": "Ewha Womans Univ."},
    {"code": "240", "name": "신촌", "english": "Sinchon"},
    {"code": "239", "name": "홍대입구", "english": "Hongik Univ."},
    {"code": "238", "name": "합정", "english": "Hapjeong"},
    {"code": "237", "name": "당산", "english": "Dangsan"},
    {"code": "236", "name": "영등포구청", "english": "Yeongdeungpo-gu Office"},
    {"code": "235", "name": "문래", "english": "Mullae"},
    {"code": "234", "name": "신도림", "english": "Sindorim"},
    {"code": "233", "name": "대림", "english": "Daerim"},
    {"code": "232", "name": "구로디지털단지", "english": "Guro Digital Complex"},
    {"code": "231", "name": "신대방", "english": "Sindaebang"},
    {"code": "230", "name": "신림", "english": "Sillim"},
    {"code": "229", "name": "봉천", "english": "Bongcheon"},
    {"code": "228", "name": "서울대입구", "english": "Seoul Nat'l Univ."},
    {"code": "227", "name": "낙성대", "english": "Nakseongdae"},
    {"code": "226", "name": "사당", "english": "Sadang"},
    {"code": "225", "name": "방배", "english": "Bangbae"},
    {"code": "224", "name": "서초", "english": "Seocho"},
    {"code": "223", "name": "교대", "english": "Seoul Nat'l Univ. of Education"},
    {"code": "222", "name": "강남", "english": "Gangnam"},
    {"code": "221", "name": "역삼", "english": "Yeoksam"},
    {"code": "220", "name": "선릉", "english": "Seolleung"},
    {"code": "219", "name": "삼성", "english": "Samseong"},
    {"code": "218", "name": "종합운동장", "english": "Sports Complex"},
    {"code": "217", "name": "잠실새내", "english": "Jamsilsaenae"},
    {"code": "216", "name": "잠실", "english": "Jamsil"},
]


QUIZZES: List[Dict[str, object]] = [
    {
        "category": "수학",
        "question": "사과 2개와 사과 3개를 합치면 모두 몇 개인가요?",
        "choices": ["4개", "5개", "6개", "7개"],
        "answer": 1,
    },
    {
        "category": "수학",
        "question": "10에서 4를 빼면 얼마인가요?",
        "choices": ["5", "6", "7", "8"],
        "answer": 1,
    },
    {
        "category": "수학",
        "question": "동그라미 3개가 있고 2개를 더 그리면 모두 몇 개인가요?",
        "choices": ["3개", "4개", "5개", "6개"],
        "answer": 2,
    },
    {
        "category": "수학",
        "question": "1, 2, 3 다음에 오는 수는 무엇인가요?",
        "choices": ["2", "4", "5", "7"],
        "answer": 1,
    },
    {
        "category": "수학",
        "question": "손가락이 한 손에 5개 있습니다. 두 손에는 몇 개인가요?",
        "choices": ["8개", "9개", "10개", "12개"],
        "answer": 2,
    },
    {
        "category": "수학",
        "question": "4와 4를 더하면 얼마인가요?",
        "choices": ["6", "7", "8", "9"],
        "answer": 2,
    },
    {
        "category": "수학",
        "question": "7보다 1 큰 수는 무엇인가요?",
        "choices": ["6", "7", "8", "9"],
        "answer": 2,
    },
    {
        "category": "수학",
        "question": "가장 큰 수는 무엇인가요?",
        "choices": ["3", "8", "5", "1"],
        "answer": 1,
    },
    {
        "category": "수학",
        "question": "12에서 2를 빼면 얼마인가요?",
        "choices": ["8", "9", "10", "11"],
        "answer": 2,
    },
    {
        "category": "수학",
        "question": "삼각형의 뾰족한 꼭짓점은 모두 몇 개인가요?",
        "choices": ["2개", "3개", "4개", "5개"],
        "answer": 1,
    },
    {
        "category": "국어",
        "question": "다음 중 동물 이름은 무엇인가요?",
        "choices": ["책상", "고양이", "연필", "신발"],
        "answer": 1,
    },
    {
        "category": "국어",
        "question": "‘나비’는 몇 글자인가요?",
        "choices": ["1글자", "2글자", "3글자", "4글자"],
        "answer": 1,
    },
    {
        "category": "국어",
        "question": "다음 중 색깔을 나타내는 말은 무엇인가요?",
        "choices": ["빨강", "달리다", "먹다", "학교"],
        "answer": 0,
    },
    {
        "category": "국어",
        "question": "‘학교’와 가장 잘 어울리는 물건은 무엇인가요?",
        "choices": ["수영복", "책가방", "냄비", "베개"],
        "answer": 1,
    },
    {
        "category": "국어",
        "question": "‘아빠가 밥을 먹어요.’에서 먹는 것은 무엇인가요?",
        "choices": ["아빠", "밥", "물", "집"],
        "answer": 1,
    },
    {
        "category": "국어",
        "question": "다음 중 받침이 있는 글자는 무엇인가요?",
        "choices": ["가", "나", "밤", "소"],
        "answer": 2,
    },
    {
        "category": "국어",
        "question": "‘크다’의 반대말은 무엇인가요?",
        "choices": ["작다", "빠르다", "높다", "길다"],
        "answer": 0,
    },
    {
        "category": "국어",
        "question": "다음 중 인사말은 무엇인가요?",
        "choices": ["안녕하세요", "바나나", "기차", "우산"],
        "answer": 0,
    },
    {
        "category": "국어",
        "question": "‘하늘’은 몇 글자인가요?",
        "choices": ["1글자", "2글자", "3글자", "4글자"],
        "answer": 1,
    },
    {
        "category": "국어",
        "question": "다음 중 탈것 이름은 무엇인가요?",
        "choices": ["자동차", "딸기", "모자", "강아지"],
        "answer": 0,
    },
    {
        "category": "상식",
        "question": "밤에 하늘에서 빛나는 것은 무엇인가요?",
        "choices": ["별", "의자", "숟가락", "양말"],
        "answer": 0,
    },
    {
        "category": "상식",
        "question": "비가 올 때 쓰면 좋은 것은 무엇인가요?",
        "choices": ["우산", "선글라스", "부채", "장갑"],
        "answer": 0,
    },
    {
        "category": "상식",
        "question": "이를 깨끗하게 닦을 때 사용하는 것은 무엇인가요?",
        "choices": ["칫솔", "연필", "공", "수건"],
        "answer": 0,
    },
    {
        "category": "상식",
        "question": "빨간불에서는 어떻게 해야 하나요?",
        "choices": ["멈춘다", "뛴다", "노래한다", "잠잔다"],
        "answer": 0,
    },
    {
        "category": "상식",
        "question": "아침, 점심 다음에는 무엇을 먹나요?",
        "choices": ["저녁", "새벽", "겨울", "바다"],
        "answer": 0,
    },
    {
        "category": "상식",
        "question": "물을 마실 때 주로 사용하는 것은 무엇인가요?",
        "choices": ["컵", "신발", "모자", "가위"],
        "answer": 0,
    },
    {
        "category": "상식",
        "question": "추운 날씨에 손을 따뜻하게 하려고 끼는 것은 무엇인가요?",
        "choices": ["장갑", "수영모", "선풍기", "슬리퍼"],
        "answer": 0,
    },
    {
        "category": "상식",
        "question": "밥을 먹기 전에 손을 어떻게 해야 하나요?",
        "choices": ["씻는다", "숨긴다", "던진다", "그린다"],
        "answer": 0,
    },
    {
        "category": "상식",
        "question": "서울 지하철 2호선의 대표 색은 무엇인가요?",
        "choices": ["초록색", "분홍색", "검은색", "갈색"],
        "answer": 0,
    },
    {
        "category": "상식",
        "question": "지하철을 탈 때 줄을 서서 기다려야 할까요?",
        "choices": ["네", "아니요", "항상 뛰어요", "문 앞을 막아요"],
        "answer": 0,
    },
    {
        "category": "과학",
        "question": "식물이 자라는 데 필요한 것은 무엇인가요?",
        "choices": ["햇빛과 물", "돌멩이만", "장난감", "색연필"],
        "answer": 0,
    },
    {
        "category": "과학",
        "question": "얼음은 따뜻해지면 무엇이 되나요?",
        "choices": ["물", "종이", "모래", "나무"],
        "answer": 0,
    },
    {
        "category": "과학",
        "question": "사람은 무엇으로 숨을 쉬나요?",
        "choices": ["코와 입", "손가락", "발", "머리카락"],
        "answer": 0,
    },
    {
        "category": "과학",
        "question": "물고기가 사는 곳은 어디인가요?",
        "choices": ["물", "하늘", "책상", "운동장"],
        "answer": 0,
    },
    {
        "category": "과학",
        "question": "해는 주로 언제 볼 수 있나요?",
        "choices": ["낮", "한밤중", "잠잘 때만", "옷장 안"],
        "answer": 0,
    },
    {
        "category": "과학",
        "question": "우리 몸에서 소리를 듣는 곳은 어디인가요?",
        "choices": ["귀", "무릎", "팔꿈치", "발가락"],
        "answer": 0,
    },
    {
        "category": "과학",
        "question": "자석은 어떤 물건을 잘 붙잡나요?",
        "choices": ["철로 된 물건", "종이", "물", "구름"],
        "answer": 0,
    },
    {
        "category": "과학",
        "question": "비가 많이 오면 땅에 무엇이 생길 수 있나요?",
        "choices": ["물웅덩이", "불꽃", "모래성", "별"],
        "answer": 0,
    },
    {
        "category": "과학",
        "question": "새는 무엇으로 하늘을 날까요?",
        "choices": ["날개", "숟가락", "신발", "연필"],
        "answer": 0,
    },
    {
        "category": "과학",
        "question": "달은 주로 어디에서 볼 수 있나요?",
        "choices": ["하늘", "책 속", "가방 안", "냉장고"],
        "answer": 0,
    },
]


@dataclass
class Player:
    name: str
    position: int = 0
    correct: int = 0
    wrong: int = 0
    score: int = 0

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "position": self.position,
            "correct": self.correct,
            "wrong": self.wrong,
            "score": self.score,
        }


def clamp_position(value: int) -> int:
    return max(0, min(value, len(ROUTE) - 1))


def station_label(index: int) -> str:
    station = ROUTE[index]
    return f"{station['name']}역 ({station['code']})"


def reset_game(player1_name: str = "플레이어 1", player2_name: str = "플레이어 2") -> None:
    st.session_state.players = [
        Player(player1_name.strip() or "플레이어 1").to_dict(),
        Player(player2_name.strip() or "플레이어 2").to_dict(),
    ]
    st.session_state.turn = 0
    st.session_state.stage = "roll"  # roll, quiz, penalty, finished
    st.session_state.current_quiz = None
    st.session_state.last_roll = None
    st.session_state.message = "새 게임을 시작합니다. 성수역에서 출발하세요!"
    st.session_state.winner = None
    st.session_state.history = []


def ensure_state() -> None:
    if "players" not in st.session_state:
        reset_game()


def active_player() -> Dict[str, object]:
    return st.session_state.players[st.session_state.turn]


def choose_quiz() -> Dict[str, object]:
    quiz = random.choice(QUIZZES).copy()
    quiz["id"] = random.randint(100000, 999999)
    return quiz


def add_history(text: str) -> None:
    st.session_state.history.insert(0, text)
    st.session_state.history = st.session_state.history[:12]


def move_player(player_index: int, steps: int) -> None:
    player = st.session_state.players[player_index]
    player["position"] = clamp_position(int(player["position"]) + steps)


def render_uploaded_map(uploaded_file) -> None:
    file_bytes = uploaded_file.getvalue()
    file_name = uploaded_file.name.lower()
    if file_name.endswith(".pdf"):
        base64_pdf = base64.b64encode(file_bytes).decode("utf-8")
        pdf_display = f"""
        <iframe
            src="data:application/pdf;base64,{base64_pdf}"
            width="100%"
            height="720"
            style="border: 1px solid #ddd; border-radius: 12px;"
            type="application/pdf">
        </iframe>
        """
        components.html(pdf_display, height=740)
    else:
        st.image(file_bytes, caption="업로드한 실제 서울 지하철 노선도", use_container_width=True)


def render_default_map(map_url: str) -> None:
    safe_url = html.escape(map_url, quote=True)
    components.html(
        f"""
        <iframe
            src="{safe_url}"
            width="100%"
            height="720"
            style="border: 1px solid #ddd; border-radius: 12px; background: #fff;"
            type="application/pdf">
        </iframe>
        """,
        height=740,
    )
    st.caption("기본값은 공개된 서울 지하철 노선도 PDF입니다. 보이지 않으면 사이드바에서 PNG/JPG/PDF 노선도 파일을 직접 올려 주세요.")


def render_board() -> None:
    p1 = st.session_state.players[0]
    p2 = st.session_state.players[1]
    p1_pos = int(p1["position"])
    p2_pos = int(p2["position"])

    station_cards = []
    for i, station in enumerate(ROUTE):
        classes = ["station-card"]
        if i == 0:
            classes.append("start")
        if i == len(ROUTE) - 1:
            classes.append("finish")
        if i == p1_pos or i == p2_pos:
            classes.append("occupied")

        markers = []
        if i == p1_pos:
            markers.append("<span class='player-chip p1'>P1</span>")
        if i == p2_pos:
            markers.append("<span class='player-chip p2'>P2</span>")
        marker_html = "".join(markers) if markers else "<span class='empty-chip'>·</span>"

        station_name = html.escape(station["name"])
        station_eng = html.escape(station["english"])
        station_code = html.escape(station["code"])
        station_cards.append(
            f"""
            <div class="{' '.join(classes)}">
                <div class="station-top">
                    <span class="station-code">{station_code}</span>
                    <span>{marker_html}</span>
                </div>
                <div class="station-name">{station_name}</div>
                <div class="station-eng">{station_eng}</div>
            </div>
            """
        )

    components.html(
        f"""
        <style>
            .route-wrap {{
                background: #f7faf8;
                border: 1px solid #d8eadf;
                border-radius: 18px;
                padding: 18px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }}
            .route-title {{
                font-weight: 800;
                color: #154f2e;
                margin-bottom: 12px;
                font-size: 19px;
            }}
            .route-subtitle {{
                color: #4b6353;
                margin-bottom: 16px;
                font-size: 13px;
            }}
            .route-grid {{
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 10px;
            }}
            .station-card {{
                position: relative;
                min-height: 88px;
                border-radius: 14px;
                border: 2px solid #dce6df;
                background: white;
                padding: 10px;
                box-sizing: border-box;
                box-shadow: 0 1px 4px rgba(0,0,0,0.04);
            }}
            .station-card::after {{
                content: '';
                position: absolute;
                height: 4px;
                background: {LINE_COLOR};
                left: 12px;
                right: 12px;
                bottom: 8px;
                border-radius: 99px;
                opacity: 0.75;
            }}
            .station-card.start {{ border-color: #2f855a; }}
            .station-card.finish {{ border-color: #d97706; }}
            .station-card.occupied {{
                box-shadow: 0 0 0 3px rgba(0,168,77,0.18);
                transform: translateY(-1px);
            }}
            .station-top {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 4px;
            }}
            .station-code {{
                font-size: 12px;
                color: white;
                background: {LINE_COLOR};
                padding: 2px 7px;
                border-radius: 999px;
                font-weight: 800;
            }}
            .station-name {{
                font-size: 15px;
                font-weight: 800;
                color: #17251c;
                line-height: 1.2;
                word-break: keep-all;
            }}
            .station-eng {{
                color: #647067;
                font-size: 11px;
                margin-top: 3px;
                line-height: 1.2;
            }}
            .player-chip, .empty-chip {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 28px;
                height: 22px;
                border-radius: 999px;
                font-size: 11px;
                font-weight: 900;
                margin-left: 3px;
            }}
            .p1 {{ background: #e0f2fe; color: #075985; }}
            .p2 {{ background: #fee2e2; color: #991b1b; }}
            .empty-chip {{ background: #f2f4f3; color: #b9c0bc; }}
            @media (max-width: 720px) {{
                .route-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
            }}
        </style>
        <div class="route-wrap">
            <div class="route-title">성수 → 잠실 긴 경로 게임판</div>
            <div class="route-subtitle">짧은 방향을 쓰지 않고 2호선 본선을 크게 돌아갑니다. 총 {len(ROUTE)}개 역, 이동 칸 수 {len(ROUTE)-1}칸.</div>
            <div class="route-grid">
                {''.join(station_cards)}
            </div>
        </div>
        """,
        height=1130,
        scrolling=True,
    )


def render_status() -> None:
    players = st.session_state.players
    cols = st.columns(2)
    for idx, col in enumerate(cols):
        player = players[idx]
        pos = int(player["position"])
        progress = pos / (len(ROUTE) - 1)
        with col:
            active_badge = " 👈 현재 차례" if idx == st.session_state.turn and st.session_state.stage != "finished" else ""
            st.subheader(f"{html.escape(str(player['name']))}{active_badge}")
            st.metric("현재 위치", station_label(pos))
            st.progress(progress)
            st.write(f"정답 {player['correct']}개 · 오답 {player['wrong']}개 · 점수 {player['score']}점")


def render_rules() -> None:
    st.markdown(
        """
        **규칙**  
        1. 플레이어는 성수역에서 출발합니다.  
        2. 자기 차례에 주사위를 굴려 나온 눈만큼 전진합니다.  
        3. 도착한 역에서 객관식 퀴즈를 풉니다.  
        4. 정답이면 10점을 얻고 같은 플레이어가 한 번 더 주사위를 굴립니다.  
        5. 오답이면 벌칙 주사위를 굴려 나온 눈만큼 후퇴하고, 차례가 상대에게 넘어갑니다.  
        6. 먼저 잠실역에 도착하면 승리합니다.
        """
    )


def main() -> None:
    st.set_page_config(page_title="서울 2호선 주사위 퀴즈 게임", page_icon="🚇", layout="wide")
    ensure_state()

    st.title(APP_TITLE)
    st.caption("6–7세 아이도 풀 수 있는 쉬운 객관식 퀴즈와 실제 서울 지하철 노선도를 함께 사용하는 2인용 보드게임입니다.")

    with st.sidebar:
        st.header("게임 설정")
        p1_name = st.text_input("1번 플레이어 이름", value=str(st.session_state.players[0]["name"]))
        p2_name = st.text_input("2번 플레이어 이름", value=str(st.session_state.players[1]["name"]))

        if st.button("🔄 새 게임 시작", use_container_width=True):
            reset_game(p1_name, p2_name)
            st.rerun()

        st.divider()
        st.header("실제 노선도")
        uploaded_map = st.file_uploader(
            "실제 서울 지하철 노선도 이미지/PDF 업로드",
            type=["png", "jpg", "jpeg", "webp", "pdf"],
            help="직접 가지고 있는 공식 노선도 이미지가 있으면 여기에 올려서 사용하세요.",
        )
        map_url = st.text_input("기본 노선도 URL", value=DEFAULT_MAP_URL)

        st.divider()
        st.header("경로 정보")
        st.write(f"출발: **{station_label(0)}**")
        st.write(f"도착: **{station_label(len(ROUTE)-1)}**")
        st.write(f"총 역 수: **{len(ROUTE)}개**")
        st.write(f"총 이동 칸 수: **{len(ROUTE)-1}칸**")

    message = st.session_state.get("message")
    if message:
        st.info(message)

    render_status()

    control_col, log_col = st.columns([1.2, 1])

    with control_col:
        st.header("🎲 게임 진행")
        stage = st.session_state.stage

        if stage == "roll":
            player = active_player()
            current_pos = int(player["position"])
            st.write(f"현재 차례: **{player['name']}**")
            st.write(f"현재 역: **{station_label(current_pos)}**")

            if st.button("주사위 굴리기", type="primary", use_container_width=True):
                dice = random.randint(1, 6)
                before = int(player["position"])
                move_player(st.session_state.turn, dice)
                after = int(player["position"])
                st.session_state.last_roll = dice

                if after >= len(ROUTE) - 1:
                    st.session_state.stage = "finished"
                    st.session_state.winner = st.session_state.turn
                    st.session_state.message = f"🎉 {player['name']}님이 주사위 {dice}을/를 굴려 {station_label(after)}에 도착했습니다. 승리!"
                    add_history(f"🏁 {player['name']}: {station_label(before)} → {station_label(after)} / 승리")
                else:
                    st.session_state.current_quiz = choose_quiz()
                    st.session_state.stage = "quiz"
                    st.session_state.message = f"{player['name']}님이 주사위 {dice}을/를 굴려 {station_label(after)}에 도착했습니다. 퀴즈를 풀어 주세요."
                    add_history(f"🎲 {player['name']}: {dice}칸 전진, {station_label(after)} 도착")
                st.rerun()

        elif stage == "quiz":
            player = active_player()
            quiz: Optional[Dict[str, object]] = st.session_state.current_quiz
            if not quiz:
                st.session_state.current_quiz = choose_quiz()
                quiz = st.session_state.current_quiz

            st.write(f"퀴즈 역: **{station_label(int(player['position']))}**")
            st.write(f"문제 분야: **{quiz['category']}**")
            st.subheader(str(quiz["question"]))

            choices = list(quiz["choices"])
            selected = st.radio(
                "정답을 고르세요.",
                options=list(range(len(choices))),
                format_func=lambda i: choices[i],
                key=f"quiz_choice_{quiz['id']}",
            )

            if st.button("정답 제출", type="primary", use_container_width=True):
                correct_answer = int(quiz["answer"])
                if selected == correct_answer:
                    player["correct"] = int(player["correct"]) + 1
                    player["score"] = int(player["score"]) + 10
                    st.session_state.stage = "roll"
                    st.session_state.current_quiz = None
                    st.session_state.message = f"✅ 정답입니다! {player['name']}님은 10점을 얻고 한 번 더 주사위를 굴립니다."
                    add_history(f"✅ {player['name']}: {station_label(int(player['position']))} 퀴즈 정답")
                else:
                    player["wrong"] = int(player["wrong"]) + 1
                    st.session_state.stage = "penalty"
                    answer_text = choices[correct_answer]
                    st.session_state.message = f"❌ 아쉽습니다. 정답은 ‘{answer_text}’입니다. 벌칙 주사위를 굴려 뒤로 이동하세요."
                    add_history(f"❌ {player['name']}: {station_label(int(player['position']))} 퀴즈 오답")
                st.rerun()

        elif stage == "penalty":
            player = active_player()
            st.write(f"벌칙 차례: **{player['name']}**")
            st.write("오답이므로 벌칙 주사위를 굴려 나온 눈만큼 뒤로 갑니다.")

            if st.button("벌칙 주사위 굴리기", type="primary", use_container_width=True):
                penalty = random.randint(1, 6)
                before = int(player["position"])
                move_player(st.session_state.turn, -penalty)
                after = int(player["position"])
                st.session_state.current_quiz = None
                st.session_state.turn = 1 - int(st.session_state.turn)
                st.session_state.stage = "roll"
                st.session_state.message = f"{player['name']}님이 벌칙 주사위 {penalty}을/를 굴려 {station_label(before)}에서 {station_label(after)}로 후퇴했습니다. 차례가 넘어갑니다."
                add_history(f"↩️ {player['name']}: 벌칙 {penalty}칸 후퇴, {station_label(after)}")
                st.rerun()

        elif stage == "finished":
            winner_index = st.session_state.winner
            if winner_index is not None:
                winner = st.session_state.players[int(winner_index)]
                st.success(f"🏆 승리자: {winner['name']}")
            st.write("새 게임을 시작하려면 사이드바의 ‘새 게임 시작’을 누르세요.")

    with log_col:
        st.header("🧾 진행 기록")
        if st.session_state.history:
            for item in st.session_state.history:
                st.write(item)
        else:
            st.write("아직 기록이 없습니다.")

        with st.expander("게임 규칙 보기", expanded=False):
            render_rules()

    st.divider()
    tab_board, tab_real_map, tab_route = st.tabs(["게임판", "실제 노선도", "긴 경로 역 목록"])

    with tab_board:
        render_board()

    with tab_real_map:
        st.subheader("실제 서울 지하철 노선도")
        if uploaded_map is not None:
            render_uploaded_map(uploaded_map)
        else:
            render_default_map(map_url)

    with tab_route:
        st.subheader("사용 중인 긴 경로")
        st.write("성수역에서 잠실역으로 바로 가지 않고, 2호선 본선을 크게 돌아가는 방향입니다.")
        route_text = " → ".join([f"{s['name']}({s['code']})" for s in ROUTE])
        st.write(route_text)

        st.download_button(
            "역 목록 CSV 다운로드",
            data="순서,역번호,역명,영문명\n" + "\n".join(
                [f"{i+1},{s['code']},{s['name']},{s['english']}" for i, s in enumerate(ROUTE)]
            ),
            file_name="seoul_line2_long_route.csv",
            mime="text/csv",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
