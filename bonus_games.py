"""9 interactive bonus puzzles for the Seoul Line 2 Streamlit board game.

Pure Python game logic is deliberately separated from Streamlit so puzzles can be
validated and reproduced in automated tests. No external dependencies.
"""
import random
from collections import deque

GAME_TYPES = [
    "car_sort", "switch_route", "signal_grid", "track_rotate", "memory_pairs",
    "maze", "cargo_balance", "mastermind", "sliding_tiles",
]
GAME_LABELS = {
    "car_sort": "탐험 가방 순서 추리",
    "switch_route": "비밀 문 방향 암호",
    "signal_grid": "반짝이는 별자리",
    "track_rotate": "끊어진 다리 연결",
    "memory_pairs": "동물 카드 기억력",
    "maze": "열쇠를 찾는 미로",
    "cargo_balance": "동물 구조 뗏목",
    "mastermind": "비밀 색깔 암호",
    "sliding_tiles": "움직이는 숫자 퍼즐",
}


def shuffled_different(values, rng=random):
    a = list(values)
    for _ in range(30):
        rng.shuffle(a)
        if a != list(values):
            return a
    a[0], a[-1] = a[-1], a[0]
    return a


def toggle_stars(board, index):
    """Classic lights-out move on 2x3: self + orthogonal neighbors."""
    row, col = divmod(int(index), 3)
    for dr, dc in [(0, 0), (0, -1), (0, 1), (-1, 0), (1, 0)]:
        rr, cc = row + dr, col + dc
        if 0 <= rr < 2 and 0 <= cc < 3:
            board[rr * 3 + cc] ^= 1


# Each track is a 2-exit connection. Rotation is clockwise.
DIRECTIONS = 'NESW'
TRACK_BASE = {"straight": ("N", "S"), "corner": ("N", "E")}
TRACK_GLYPHS = {
    frozenset(("N", "S")): "┃",
    frozenset(("E", "W")): "━",
    frozenset(("N", "E")): "┗",
    frozenset(("E", "S")): "┏",
    frozenset(("S", "W")): "┓",
    frozenset(("W", "N")): "┛",
}
OPPOSITE = {"N": "S", "E": "W", "S": "N", "W": "E"}
DELTA = {"N": (-1, 0), "E": (0, 1), "S": (1, 0), "W": (0, -1)}


def track_exits(tile):
    if not tile:
        return ()
    base = TRACK_BASE[tile["shape"]]
    rot = int(tile["rot"])
    return tuple(DIRECTIONS[(DIRECTIONS.index(d) + rot) % 4] for d in base)


def track_symbol(tile):
    return TRACK_GLYPHS[frozenset(track_exits(tile))] if tile else "🪨"


def track_connected(puzzle):
    """Follow a continuous path from external left edge to external right edge."""
    tiles = puzzle["tiles"]
    cell = (2, 0)
    entrance = 'W'
    seen = set()
    while True:
        if cell in seen:
            return False
        seen.add(cell)
        r, c = cell
        tile = tiles[r * 3 + c]
        if not tile:
            return False
        ports = track_exits(tile)
        if entrance not in ports:
            return False
        out = ports[0] if ports[1] == entrance else ports[1]
        if cell == (1, 2) and out == 'E':
            return True
        dr, dc = DELTA[out]
        nr, nc = r + dr, c + dc
        if not (0 <= nr < 3 and 0 <= nc < 3):
            return False
        cell = nr, nc
        entrance = OPPOSITE[out]


def maze_distance(rows, cols, walls, start, goal):
    q = deque([(tuple(start), 0)])
    seen = {tuple(start)}
    while q:
        (r, c), dist = q.popleft()
        if (r, c) == tuple(goal):
            return dist
        for dr, dc in DELTA.values():
            dest = (r + dr, c + dc)
            if 0 <= dest[0] < rows and 0 <= dest[1] < cols and dest not in walls and dest not in seen:
                seen.add(dest)
                q.append((dest, dist + 1))
    return None


def sliding_distance(start):
    goal = (1, 2, 3, 4, 5, 0)
    start = tuple(start)
    q = deque([(start, 0)])
    seen = {start}
    while q:
        state, dist = q.popleft()
        if state == goal:
            return dist
        empty = state.index(0)
        r, c = divmod(empty, 3)
        for dr, dc in DELTA.values():
            rr, cc = r + dr, c + dc
            if 0 <= rr < 2 and 0 <= cc < 3:
                idx = rr * 3 + cc
                nxt = list(state)
                nxt[empty], nxt[idx] = nxt[idx], nxt[empty]
                nxt = tuple(nxt)
                if nxt not in seen:
                    seen.add(nxt)
                    q.append((nxt, dist + 1))
    return None


def make_sliding_start(rng=random):
    solved = [1, 2, 3, 4, 5, 0]
    # Explicit legal moves guarantee every generated board is solvable.
    for _ in range(150):
        board = solved[:]
        prev = -1
        for _ in range(rng.randint(9, 15)):
            empty = board.index(0)
            r, c = divmod(empty, 3)
            options = []
            for dr, dc in DELTA.values():
                rr, cc = r + dr, c + dc
                if 0 <= rr < 2 and 0 <= cc < 3:
                    options.append(rr * 3 + cc)
            allowed = [i for i in options if i != prev] or options
            idx = rng.choice(allowed)
            board[empty], board[idx] = board[idx], board[empty]
            prev = empty
        distance = sliding_distance(board)
        if distance is not None and 7 <= distance <= 13:
            return board
    # Fixed, solvable fallback (always validate in tests).
    return [5, 0, 4, 1, 3, 2]


def create_puzzle(kind, rng=random):
    if kind not in GAME_TYPES:
        raise ValueError("Unknown bonus game")

    if kind == 'car_sort':
        themes = [
            ["🧭 나침반", "🔦 손전등", "🗺️ 지도", "🥤 물병", "🎒 배낭"],
            ["🌱 씨앗", "🪴 화분", "💧 물뿌리개", "☀️ 햇빛", "🌻 꽃"],
            ["🥣 그릇", "🥛 우유", "🍓 딸기", "🥄 숟가락", "🍰 간식"],
        ]
        goal = rng.choice(themes)[:]
        rng.shuffle(goal)
        a, b, c, d, e = goal
        clues = [
            f"① {a}은(는) 맨 앞에 있어요.",
            f"② {e}은(는) 맨 마지막이에요.",
            f"③ {c}은(는) {d}의 바로 앞이에요.",
            f"④ {b}은(는) {c}보다 앞에 있어요.",
        ]
        return dict(game_type=kind, title='🎒 탐험 가방 순서 추리', icon='🎒',
                    prompt='단서 4개를 읽고 물건 5개의 순서를 찾아보세요. **정답 순서는 보이지 않아요!**',
                    clues=clues, goal=goal, state=shuffled_different(goal,rng), max_attempts=4,
                    hint='맨 앞과 맨 뒤를 먼저 고정하고, ③번 단서를 활용하세요.')

    if kind == 'switch_route':
        goal = [rng.randrange(2) for _ in range(4)]
        names = ['1번', '2번', '3번', '4번']
        word = lambda v: '왼쪽 ◀' if v == 0 else '오른쪽 ▶'
        relationship = lambda a,b: '같은 방향' if a==b else '서로 반대 방향'
        clues = [f"① 1번 문은 {word(goal[0])}이에요.",
                 f"② 1번과 3번은 {relationship(goal[0],goal[2])}이에요.",
                 f"③ 3번과 4번은 {relationship(goal[2],goal[3])}이에요.",
                 f"④ 2번과 4번은 {relationship(goal[1],goal[3])}이에요."]
        return dict(game_type=kind, title='🔐 비밀 문 방향 암호', icon='🔐',
                    prompt='**4개의 단서**를 이용해 문 4개의 방향을 찾아보세요. 단서의 연결 관계를 잘 생각해야 해요.',
                    clues=clues, state=[rng.randrange(2) for _ in range(4)], goal=goal,
                    max_attempts=4, hint='1번이 정해지면 3번 → 4번 → 2번도 차례로 정할 수 있어요.')

    if kind == 'signal_grid':
        state = [1] * 6
        presses = rng.sample(range(6), rng.randint(3, 4))
        for index in presses:
            toggle_stars(state,index)
        if state == [1] * 6:
            toggle_stars(state,0)
        return dict(game_type=kind, title='✨ 반짝이는 별자리', icon='✨',
                    prompt='별 6개를 **모두 켜세요!** 별 하나를 누르면 자기 자신과 **상·하·좌·우 이웃 별**의 불빛도 함께 바뀝니다.',
                    state=state, goal=[1]*6, max_attempts=4,
                    hint='한 별을 두 번 누르면 원래 모습으로 돌아와요. 주변까지 함께 바뀐다는 점을 이용하세요.')

    if kind == 'track_rotate':
        # Start: left of (2,0), finish: right of (1,2).
        # A continuous winding 8-tile route with one rock at (2,2).
        spec = [
            ('corner', frozenset('SE')), ('straight', frozenset('EW')), ('corner', frozenset('SW')),
            ('corner', frozenset('NE')), ('corner', frozenset('SW')), ('corner', frozenset('NE')),
            ('straight', frozenset('EW')), ('corner', frozenset('WN')), None,
        ]
        tiles=[]
        for item in spec:
            if item is None:
                tiles.append(None)
                continue
            shape, exits = item
            goal_rot = next(i for i in range(4) if frozenset(
                DIRECTIONS[(DIRECTIONS.index(d)+i)%4] for d in TRACK_BASE[shape]) == exits)
            rot = (goal_rot + rng.choice([1,2,3])) % 4
            tiles.append({'shape': shape, 'rot': rot})
        return dict(game_type=kind, title='🌉 끊어진 다리 연결', icon='🌉',
                    prompt='다리 조각을 눌러 **🚩(왼쪽 아래)에서 🎁(오른쪽 가운데)**까지 끊기지 않게 연결하세요. 바위(🪨)는 지나갈 수 없어요.',
                    tiles=tiles, max_attempts=4,
                    hint='🚩에서 시작해 다음 칸으로 나갈 수 있도록 한 조각씩 연결해 보세요.')

    if kind == 'memory_pairs':
        cards=['🐼','🦊','🐸','🦁']*2
        rng.shuffle(cards)
        return dict(game_type=kind, title='🃏 동물 카드 기억력', icon='🃏',
                    prompt='뒤집어진 동물 카드 8장 중 같은 그림 **4쌍**을 찾으세요. 한 번 본 카드 위치를 기억하면 더 높은 점수를 받을 수 있어요.',
                    cards=cards, revealed=[], matched=[], mismatch=False, moves=0,
                    hint='처음 보는 카드의 위치를 기억하고, 다음에는 아는 짝을 먼저 찾아보세요.')

    if kind == 'maze':
        rows=cols=6
        start=(0,0); goal=(5,5)
        key=rng.choice([(0,4),(4,0),(1,5),(5,1),(3,3)])
        candidates=[(r,c) for r in range(rows) for c in range(cols) if (r,c) not in (start,key,goal)]
        chosen=None
        for _ in range(1500):
            walls=set(rng.sample(candidates,rng.randint(9,12)))
            d1=maze_distance(rows,cols,walls,start,key)
            d2=maze_distance(rows,cols,walls,key,goal)
            if d1 is not None and d2 is not None and d1+d2>=13:
                chosen=walls
                break
        if chosen is None:
            key=(5,1)
            chosen={(1,1),(1,2),(2,2),(3,0),(3,3),(4,3),(4,4)}
        return dict(game_type=kind, title='🗝️ 열쇠를 찾는 미로', icon='🗝️',
                    prompt='6×6 미로에서 먼저 **🗝️ 열쇠**를 찾고, 그 다음 **🚪 출구**에 도착하세요. 벽은 통과할 수 없어요.',
                    rows=rows,cols=cols,walls=[list(p) for p in sorted(chosen)],
                    position=[0,0],key=list(key),has_key=False,goal=[5,5],moves=0,
                    hint='출구로 바로 가도 열쇠가 없으면 열리지 않아요. 열쇠부터 찾아보세요.')

    if kind == 'cargo_balance':
        weights=[1,2,3,4,6] # total = 16, so each side must weigh 8
        sides=[rng.randrange(2) for _ in weights]
        if sum(w for w,s in zip(weights,sides) if s==0)==8:
            sides[0]^=1
        return dict(game_type=kind, title='⚖️ 동물 구조 뗏목', icon='⚖️',
                    prompt='뗏목의 양쪽을 **각각 8kg**으로 맞추세요. 동물 그림을 누르면 반대쪽으로 이동해요.',
                    weights=weights, animals=['🐭','🐰','🐨','🦊','🐻'],state=sides,
                    max_attempts=4,hint='6kg과 2kg을 같은 쪽으로 모으면 8kg이 됩니다. 다른 조합도 찾아보세요.')

    if kind == 'mastermind':
        colors=['🔴','🟡','🟢','🔵']
        goal=rng.sample(colors,3)
        start=colors[:3]
        if start == goal:
            start=[colors[1],colors[0],colors[2]]
        return dict(game_type=kind, title='🕵️ 비밀 색깔 암호', icon='🕵️',
                    prompt='서로 다른 색 3개로 된 **비밀 암호**를 추리하세요. 색을 눌러 바꾸고 검사하면 **자리까지 맞힌 개수**와 **색만 맞힌 개수**를 알려 줍니다.',
                    colors=colors, goal=goal, state=start, history=[], max_attempts=7,
                    hint='색 하나는 한 번만 사용해요. 두 번째 검사부터는 이전 결과와 비교해 보세요.')

    # Actual movable 2x3 sliding puzzle (solvable, no number-tapping shortcut).
    return dict(game_type=kind, title='🔢 움직이는 숫자 퍼즐', icon='🔢',
                prompt='**빈칸 바로 옆의 숫자만** 움직일 수 있어요. 1~5를 순서대로 놓고 빈칸을 오른쪽 아래로 보내세요.',
                state=make_sliding_start(rng), goal=[1,2,3,4,5,0],moves=0,
                hint='1~2~3을 윗줄에 먼저 맞추고 아랫줄을 정리해 보세요.')


def code_feedback(guess,goal):
    exact=sum(a==b for a,b in zip(guess,goal))
    shared=len(set(guess)&set(goal))
    return exact,shared-exact


def check_puzzle(puzzle):
    """Return (is_solved, explanation) for puzzles with a 'check' button."""
    kind=puzzle['game_type']
    if kind in ('car_sort','switch_route','signal_grid'):
        won=list(puzzle['state'])==list(puzzle['goal'])
        if kind=='signal_grid':
            return won, '아직 꺼진 별이 있어요. 별을 누르면 주변도 함께 변합니다.'
        return won, '단서를 다시 읽고 방향이나 순서를 비교해 보세요.'
    if kind=='track_rotate':
        return track_connected(puzzle), '출발점 🚩부터 모든 조각이 이어지는지 살펴보세요.'
    if kind=='cargo_balance':
        w=puzzle['weights']; s=puzzle['state']
        l=sum(v for v,b in zip(w,s) if b==0)
        return l==8, f'현재 왼쪽 {l}kg / 오른쪽 {16-l}kg이에요. 양쪽 모두 8kg이어야 해요.'
    if kind=='mastermind':
        guess=list(puzzle['state'])
        if len(set(guess))!=3:
            return False, '비밀 암호에는 같은 색이 두 번 들어가지 않아요. 서로 다른 세 색을 골라 보세요.'
        exact, other=code_feedback(guess,puzzle['goal'])
        puzzle['history'].append({'guess':guess,'exact':exact,'other':other})
        return exact==3, f'🧩 정확한 자리 {exact}개 · 색만 맞은 것 {other}개! 기록을 비교해 보세요.'
    raise ValueError(f'Game {kind} has no check action')


def act(puzzle, action, index=None):
    """Change game state; return True if a non-check puzzle has just been won."""
    kind=puzzle['game_type']
    if kind=='car_sort':
        state=puzzle['state']; i=int(index)
        if action=='up' and 0<i<len(state):
            state[i-1],state[i]=state[i],state[i-1]
        if action=='down' and 0<=i<len(state)-1:
            state[i+1],state[i]=state[i],state[i+1]
    elif kind=='switch_route':
        i=int(index)
        if 0<=i<4: puzzle['state'][i]^=1
    elif kind=='signal_grid':
        toggle_stars(puzzle['state'],int(index))
    elif kind=='track_rotate':
        i=int(index)
        if 0<=i<9 and puzzle['tiles'][i]:
            puzzle['tiles'][i]['rot']=(puzzle['tiles'][i]['rot']+1)%4
    elif kind=='memory_pairs':
        cards=puzzle['cards']; revealed=puzzle['revealed']; matched=puzzle['matched']
        if action=='hide_mismatch':
            puzzle['revealed']=[]; puzzle['mismatch']=False
        else:
            i=int(index)
            if puzzle['mismatch'] or i in matched or i in revealed or not 0<=i<len(cards):
                return False
            revealed.append(i)
            if len(revealed)==2:
                puzzle['moves']+=1
                a,b=revealed
                if cards[a]==cards[b]:
                    matched.extend([a,b]); puzzle['revealed']=[]
                else:
                    puzzle['mismatch']=True
            return len(matched)==len(cards)
    elif kind=='maze':
        d={'up':(-1,0),'down':(1,0),'left':(0,-1),'right':(0,1)}.get(action,(0,0))
        r,c=puzzle['position']; nr,nc=r+d[0],c+d[1]
        walls={tuple(v) for v in puzzle['walls']}
        if 0<=nr<6 and 0<=nc<6 and (nr,nc) not in walls:
            puzzle['position']=[nr,nc]; puzzle['moves']+=1
            if puzzle['position']==puzzle['key']:
                puzzle['has_key']=True
        return puzzle['position']==puzzle['goal'] and puzzle['has_key']
    elif kind=='cargo_balance':
        i=int(index)
        if 0<=i<len(puzzle['state']): puzzle['state'][i]^=1
    elif kind=='mastermind':
        i=int(index); colors=puzzle['colors']; state=puzzle['state']
        if 0<=i<3:
            state[i]=colors[(colors.index(state[i])+1)%len(colors)]
    elif kind=='sliding_tiles':
        state=puzzle['state']; idx=int(index); empty=state.index(0)
        rr,cc=divmod(idx,3); er,ec=divmod(empty,3)
        if abs(rr-er)+abs(cc-ec)==1:
            state[empty],state[idx]=state[idx],state[empty]
            puzzle['moves']+=1
        return state==puzzle['goal']
    return False


def bonus_points(puzzle, failed_checks=0):
    """Reward careful play without punishing exploration or blocking progress."""
    kind=puzzle['game_type']
    if kind=='memory_pairs':
        return 30 if puzzle['moves']<=7 else 20 if puzzle['moves']<=11 else 10
    if kind=='maze':
        return 30 if puzzle['moves']<=18 else 20 if puzzle['moves']<=27 else 10
    if kind=='sliding_tiles':
        return 30 if puzzle['moves']<=16 else 20 if puzzle['moves']<=26 else 10
    if kind=='mastermind':
        n=len(puzzle.get('history',[]))
        return 30 if n<=3 else 20 if n<=5 else 10
    return 30 if failed_checks==0 else 20 if failed_checks<=2 else 10
