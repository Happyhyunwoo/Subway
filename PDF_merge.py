import os
import random
from PIL import Image
import streamlit as st

st.set_page_config(
    page_title="서울 지하철 2호선 퀴즈 보드게임",
    page_icon="🚇",
    layout="wide"
)

STATIONS = [
    "성수", "뚝섬", "한양대", "왕십리", "상왕십리", "신당", "동대문역사문화공원",
    "을지로4가", "을지로3가", "을지로입구", "시청", "충정로", "아현", "이대",
    "신촌", "홍대입구", "합정", "당산", "문래", "영등포구청", "신도림", "대림",
    "구로디지털단지", "신대방", "봉천", "서울대입구", "낙성대", "사당", "방배",
    "서초", "교대", "강남", "역삼", "선릉", "삼성", "종합운동장", "신천", "잠실"
]

QUIZZES = [
    {"category": "수학", "q": "3 + 2는 얼마일까요?", "choices": ["4", "5", "6", "7"], "answer": "5"},
    {"category": "수학", "q": "10에서 4를 빼면?", "choices": ["5", "6", "7", "8"], "answer": "6"},
    {"category": "수학", "q": "2 + 2 + 2는 얼마일까요?", "choices": ["4", "5", "6", "8"], "answer": "6"},
    {"category": "수학", "q": "1보다 큰 수는 무엇일까요?", "choices": ["0", "1", "2", "-1"], "answer": "2"},
    {"category": "수학", "q": "사과가 5개 있는데 1개 먹으면 몇 개 남을까요?", "choices": ["3", "4", "5", "6"], "answer": "4"},
    {"category": "수학", "q": "7 다음에 오는 수는?", "choices": ["6", "7", "8", "9"], "answer": "8"},
    {"category": "수학", "q": "가장 작은 수는?", "choices": ["9", "3", "5", "7"], "answer": "3"},
    {"category": "수학", "q": "네모의 변은 몇 개일까요?", "choices": ["2개", "3개", "4개", "5개"], "answer": "4개"},

    {"category": "국어", "q": "'가, 나, 다' 다음에 오는 글자는?", "choices": ["라", "마", "사", "아"], "answer": "라"},
    {"category": "국어", "q": "'하늘'의 첫 글자는?", "choices": ["ㅎ", "ㄴ", "ㄷ", "ㅅ"], "answer": "ㅎ"},
    {"category": "국어", "q": "'바나나'는 몇 글자일까요?", "choices": ["2글자", "3글자", "4글자", "5글자"], "answer": "3글자"},
    {"category": "국어", "q": "동물을 뜻하는 말은?", "choices": ["강아지", "의자", "연필", "가방"], "answer": "강아지"},
    {"category": "국어", "q": "'학교'와 가장 관련 있는 것은?", "choices": ["칠판", "냉장고", "침대", "자동차"], "answer": "칠판"},
    {"category": "국어", "q": "'봄'과 반대 계절은?", "choices": ["여름", "가을", "겨울", "장마"], "answer": "겨울"},
    {"category": "국어", "q": "문장을 끝낼 때 자주 쓰는 기호는?", "choices": ["쉼표", "마침표", "따옴표", "물결"], "answer": "마침표"},
    {"category": "국어", "q": "'엄마'는 누구를 부르는 말일까요?", "choices": ["친구", "가족", "선생님", "의사"], "answer": "가족"},

    {"category": "상식", "q": "우리가 숨 쉴 때 필요한 것은?", "choices": ["물", "공기", "모래", "종이"], "answer": "공기"},
    {"category": "상식", "q": "하늘에서 비가 올 때 필요한 것은?", "choices": ["선글라스", "우산", "목도리", "장갑"], "answer": "우산"},
    {"category": "상식", "q": "낮에 하늘에서 볼 수 있는 것은?", "choices": ["달", "별", "해", "북두칠성"], "answer": "해"},
    {"category": "상식", "q": "밤에 자는 곳은 보통 어디일까요?", "choices": ["놀이터", "침대", "버스", "교실"], "answer": "침대"},
    {"category": "상식", "q": "치아를 닦을 때 쓰는 것은?", "choices": ["빗", "칫솔", "수건", "비누"], "answer": "칫솔"},
    {"category": "상식", "q": "학교에 갈 때 메고 가는 것은?", "choices": ["냄비", "가방", "베개", "접시"], "answer": "가방"},
    {"category": "상식", "q": "겨울에 추울 때 입는 것은?", "choices": ["수영복", "패딩", "반바지", "샌들"], "answer": "패딩"},
    {"category": "상식", "q": "손을 씻을 때 보통 함께 쓰는 것은?", "choices": ["비누", "색연필", "풀", "지우개"], "answer": "비누"},

    {"category": "과학", "q": "식물은 무엇을 마시며 자랄까요?", "choices": ["주스", "우유", "물", "기름"], "answer": "물"},
    {"category": "과학", "q": "얼음이 녹으면 무엇이 될까요?", "choices": ["불", "연기", "물", "돌"], "answer": "물"},
    {"category": "과학", "q": "무지개는 보통 언제 잘 보일까요?", "choices": ["비 온 뒤", "눈 올 때", "밤중", "새벽 1시"], "answer": "비 온 뒤"},
    {"category": "과학", "q": "동물 중 알을 낳는 것은?", "choices": ["닭", "고양이", "강아지", "토끼"], "answer": "닭"},
    {"category": "과학", "q": "뜨거운 것을 만지면 왜 위험할까요?", "choices": ["미끄러워서", "데일 수 있어서", "차가워서", "가벼워서"], "answer": "데일 수 있어서"},
    {"category": "과학", "q": "해가 지면 보통 어떻게 될까요?", "choices": ["낮이 된다", "밤이 된다", "비가 온다", "눈이 온다"], "answer": "밤이 된다"},
    {"category": "과학", "q": "몸이 아플 때 가는 곳은?", "choices": ["도서관", "병원", "운동장", "문구점"], "answer": "병원"},
    {"category": "과학", "q": "자석에 잘 붙는 것은?", "choices": ["종이", "나무", "쇠", "물"], "answer": "쇠"}
]

CSS = """
<style>
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}
.station-grid {
    display: grid;
    grid-template-columns: repeat(6, minmax(120px, 1fr));
    gap: 10px;
    margin-top: 10px;
}
.station-card {
    border: 1px solid #d9d9d9;
    border-radius: 14px;
    padding: 10px 8px;
    background: #ffffff;
    min-height: 82px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.station-index {
    font-size: 12px;
    color: #666;
    margin-bottom: 4px;
}
.station-name {
    font-weight: 700;
    font-size: 15px;
    margin-bottom: 8px;
    line-height: 1.25;
}
.station-start {
    background: #e8f5e9;
    border: 2px solid #2e7d32;
}
.station-end {
    background: #fff3e0;
    border: 2px solid #ef6c00;
}
.player-badges {
    font-size: 22px;
    line-height: 1.2;
}
.info-box {
    padding: 14px;
    border-radius: 14px;
    background: #f7f9fc;
    border: 1px solid #dfe6ef;
    margin-bottom: 12px;
}
.big-msg {
    padding: 14px;
    border-radius: 14px;
    background: #eef7ff;
    border: 1px solid #b9d8ff;
    font-weight: 600;
}
.history-box {
    padding: 10px 12px;
    border-radius: 12px;
    background: #fafafa;
    border: 1px solid #e5e5e5;
    margin-bottom: 8px;
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

def get_random_question():
    return random.choice(QUIZZES)

def reset_game():
    st.session_state.players = [0, 0]
    st.session_state.turn = 0
    st.session_state.question = get_random_question()
    st.session_state.history = []
    st.session_state.message = "플레이어 1부터 시작합니다. 현재 역의 퀴즈를 풀어 보세요!"
    st.session_state.winner = None
    st.session_state.player_names = ["플레이어 1", "플레이어 2"]

def ensure_state():
    if "players" not in st.session_state:
        reset_game()

def move_player(player_idx, steps):
    current = st.session_state.players[player_idx]
    new_pos = max(0, min(len(STATIONS) - 1, current + steps))
    st.session_state.players[player_idx] = new_pos
    if new_pos == len(STATIONS) - 1:
        st.session_state.winner = player_idx

def add_history(text):
    st.session_state.history.insert(0, text)
    st.session_state.history = st.session_state.history[:12]

def next_turn():
    st.session_state.turn = 1 - st.session_state.turn
    st.session_state.question = get_random_question()

def render_board():
    cards = []
    for idx, station in enumerate(STATIONS):
        cls = "station-card"
        if idx == 0:
            cls += " station-start"
        elif idx == len(STATIONS) - 1:
            cls += " station-end"

        badges = []
        if st.session_state.players[0] == idx:
            badges.append("🔴")
        if st.session_state.players[1] == idx:
            badges.append("🔵")
        badge_html = "".join(badges) if badges else "·"

        card = f"""
        <div class="{cls}">
            <div class="station-index">{idx}</div>
            <div class="station-name">{station}</div>
            <div class="player-badges">{badge_html}</div>
        </div>
        """
        cards.append(card)

    board_html = '<div class="station-grid">' + "".join(cards) + "</div>"
    st.markdown(board_html, unsafe_allow_html=True)

ensure_state()

st.title("🚇 서울 지하철 2호선 퀴즈 보드게임")
st.caption("성수역에서 출발해 긴 방향으로 돌아 잠실역에 먼저 도착하면 승리합니다.")

with st.sidebar:
    st.header("게임 설정")
    p1 = st.text_input("플레이어 1 이름", value=st.session_state.player_names[0])
    p2 = st.text_input("플레이어 2 이름", value=st.session_state.player_names[1])
    st.session_state.player_names = [p1 if p1.strip() else "플레이어 1", p2 if p2.strip() else "플레이어 2"]

    st.markdown("---")
    uploaded_map = st.file_uploader("실제 2호선 노선도 이미지 업로드", type=["png", "jpg", "jpeg"])
    if st.button("새 게임 시작", use_container_width=True):
        reset_game()
        st.rerun()

left, right = st.columns([1.35, 1])

with left:
    st.subheader("실제 노선도")
    map_shown = False

    if uploaded_map is not None:
        image = Image.open(uploaded_map)
        st.image(image, use_container_width=True, caption="업로드한 실제 2호선 노선도")
        map_shown = True
    elif os.path.exists("line2_map.png"):
        image = Image.open("line2_map.png")
        st.image(image, use_container_width=True, caption="line2_map.png")
        map_shown = True

    if not map_shown:
        st.info("같은 폴더에 `line2_map.png`를 두거나, 사이드바에서 실제 2호선 노선도 이미지를 업로드하세요.")

    st.subheader("게임 진행 보드")
    render_board()

with right:
    st.subheader("현재 상황")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f"""
            <div class="info-box">
                <div style="font-size:22px;">🔴 {st.session_state.player_names[0]}</div>
                <div>현재 위치: <b>{STATIONS[st.session_state.players[0]]}</b></div>
                <div>인덱스: {st.session_state.players[0]} / {len(STATIONS)-1}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f"""
            <div class="info-box">
                <div style="font-size:22px;">🔵 {st.session_state.player_names[1]}</div>
                <div>현재 위치: <b>{STATIONS[st.session_state.players[1]]}</b></div>
                <div>인덱스: {st.session_state.players[1]} / {len(STATIONS)-1}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    current_player = st.session_state.turn
    current_name = st.session_state.player_names[current_player]
    current_station = STATIONS[st.session_state.players[current_player]]

    st.markdown(
        f"""
        <div class="big-msg">
            현재 차례: {"🔴" if current_player == 0 else "🔵"} {current_name}<br>
            퀴즈를 푸는 역: <b>{current_station}</b>
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.expander("규칙 보기", expanded=False):
        st.write("1. 자기 차례가 되면 현재 역에서 퀴즈 1문제를 풉니다.")
        st.write("2. 맞히면 주사위를 굴려 나온 수만큼 전진합니다.")
        st.write("3. 틀리면 주사위를 굴려 나온 수만큼 후퇴합니다.")
        st.write("4. 성수역 아래로는 내려가지 않고, 잠실역에 먼저 도착하면 승리합니다.")

    if st.session_state.winner is None:
        q = st.session_state.question

        st.markdown("### 오늘의 퀴즈")
        st.write(f"분야: **{q['category']}**")
        st.write(q["q"])

        form_key = f"quiz_form_{len(st.session_state.history)}_{current_player}"
        with st.form(form_key):
            selected = st.radio(
                "정답을 골라 주세요.",
                q["choices"],
                index=None
            )
            submitted = st.form_submit_button("정답 제출", use_container_width=True)

        if submitted:
            if selected is None:
                st.warning("보기 하나를 먼저 선택해 주세요.")
            else:
                dice = random.randint(1, 6)

                if selected == q["answer"]:
                    move_player(current_player, dice)
                    result = (
                        f"{'🔴' if current_player == 0 else '🔵'} {current_name} 정답! "
                        f"주사위 {dice}칸 전진 → {STATIONS[st.session_state.players[current_player]]}"
                    )
                    st.session_state.message = result
                    add_history(result)

                    if st.session_state.winner is None:
                        next_turn()
                    st.rerun()

                else:
                    move_player(current_player, -dice)
                    result = (
                        f"{'🔴' if current_player == 0 else '🔵'} {current_name} 오답 "
                        f"(정답: {q['answer']})! 주사위 {dice}칸 후퇴 → {STATIONS[st.session_state.players[current_player]]}"
                    )
                    st.session_state.message = result
                    add_history(result)

                    if st.session_state.winner is None:
                        next_turn()
                    st.rerun()

    st.markdown("### 최근 결과")
    st.success(st.session_state.message)

    if st.session_state.winner is not None:
        winner_name = st.session_state.player_names[st.session_state.winner]
        winner_icon = "🔴" if st.session_state.winner == 0 else "🔵"
        st.balloons()
        st.markdown(
            f"""
            <div class="big-msg" style="background:#fff7e6;border:1px solid #ffd27f;">
                우승: {winner_icon} <b>{winner_name}</b><br>
                잠실역에 먼저 도착했습니다!
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("### 진행 기록")
    if st.session_state.history:
        for item in st.session_state.history:
            st.markdown(f'<div class="history-box">{item}</div>', unsafe_allow_html=True)
    else:
        st.write("아직 기록이 없습니다.")
