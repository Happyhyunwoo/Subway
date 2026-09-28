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
