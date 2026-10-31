"""Run: python -m unittest discover -s tests -v"""
import itertools
import random
import sys
import unittest
from collections import deque
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bonus_games import (
    GAME_TYPES, create_puzzle, act, check_puzzle, bonus_points, track_exits,
    track_connected, toggle_stars, maze_distance, sliding_distance,
)


def route(walls, start, end):
    q=deque([(tuple(start),[])])
    visited={tuple(start)}
    delta={"up":(-1,0),"down":(1,0),"left":(0,-1),"right":(0,1)}
    while q:
        cell,path=q.popleft()
        if cell==tuple(end): return path
        for action,(dr,dc) in delta.items():
            nex=(cell[0]+dr,cell[1]+dc)
            if 0<=nex[0]<6 and 0<=nex[1]<6 and nex not in walls and nex not in visited:
                visited.add(nex);q.append((nex,path+[action]))
    return None


def slide_route(start):
    goal=(1,2,3,4,5,0)
    q=deque([(tuple(start),[])])
    visited={tuple(start)}
    while q:
        state,path=q.popleft()
        if state==goal:return path
        empty=state.index(0)
        r,c=divmod(empty,3)
        for dr,dc in [(-1,0),(0,1),(1,0),(0,-1)]:
            rr,cc=r+dr,c+dc
            if 0<=rr<2 and 0<=cc<3:
                idx=rr*3+cc
                nxt=list(state)
                nxt[empty],nxt[idx]=nxt[idx],nxt[empty]
                nxt=tuple(nxt)
                if nxt not in visited:
                    visited.add(nxt);q.append((nxt,path+[idx]))
    return None

class BonusGameTests(unittest.TestCase):
    def test_generators_across_seeds(self):
        rng=random.Random(2026)
        for _ in range(100):
            for kind in GAME_TYPES:
                p=create_puzzle(kind,rng)
                self.assertEqual(p['game_type'],kind)
                self.assertTrue(p['title'])
                if kind=='signal_grid':
                    self.assertTrue(any(self._stars_solved(p['state'],mask) for mask in range(64)))
                if kind=='maze':
                    walls=set(map(tuple,p['walls']))
                    self.assertIsNotNone(maze_distance(6,6,walls,(0,0),p['key']))
                    self.assertIsNotNone(maze_distance(6,6,walls,p['key'],p['goal']))
                if kind=='sliding_tiles':
                    self.assertTrue(7<=sliding_distance(p['state'])<=13)
                if kind=='track_rotate':
                    self.assertFalse(track_connected(p))

    @staticmethod
    def _stars_solved(state,mask):
        a=state[:]
        for i in range(6):
            if (mask>>i)&1: toggle_stars(a,i)
        return a==[1]*6

    def test_order_logic_and_controls(self):
        p=create_puzzle('car_sort',random.Random(10))
        while p['state'] != p['goal']:
            first=next(i for i in range(5) if p['state'][i]!=p['goal'][i])
            index=p['state'].index(p['goal'][first])
            act(p,'up',index)
        self.assertTrue(check_puzzle(p)[0])
        self.assertEqual(bonus_points(p),30)

    def test_switch_logic(self):
        p=create_puzzle('switch_route',random.Random(10))
        for i in range(4):
            if p['state'][i] != p['goal'][i]:act(p,'toggle',i)
        self.assertTrue(check_puzzle(p)[0])

    def test_stars_solved_with_actual_clicks(self):
        p=create_puzzle('signal_grid',random.Random(10))
        mask=next(m for m in range(64) if self._stars_solved(p['state'],m))
        for i in range(6):
            if (mask>>i)&1:act(p,'press',i)
        self.assertTrue(check_puzzle(p)[0])

    def test_track_real_connection(self):
        p=create_puzzle('track_rotate',random.Random(3))
        expected=[('S','E'),('W','E'),('S','W'),('N','E'),('S','W'),('N','E'),('E','W'),('W','N'),None]
        for i, desired in enumerate(expected):
            if desired:
                for _ in range(4):
                    if set(track_exits(p['tiles'][i]))==set(desired):break
                    act(p,'rotate',i)
                self.assertEqual(set(track_exits(p['tiles'][i])),set(desired))
        self.assertTrue(track_connected(p))
        self.assertTrue(check_puzzle(p)[0])

    def test_memory_paired_cards(self):
        p=create_puzzle('memory_pairs',random.Random(10))
        for animal in set(p['cards']):
            indices=[i for i,c in enumerate(p['cards']) if c==animal]
            self.assertFalse(act(p,'reveal',indices[0]))
            result=act(p,'reveal',indices[1])
        self.assertTrue(result)
        self.assertEqual(p['moves'],4)
        self.assertEqual(bonus_points(p),30)

    def test_maze_key_required_and_reachable(self):
        p=create_puzzle('maze',random.Random(8))
        walls=set(map(tuple,p['walls']))
        for a in route(walls,(0,0),p['key']):act(p,a)
        self.assertTrue(p['has_key'])
        for a in route(walls,p['key'],p['goal']): result=act(p,a)
        self.assertTrue(result)
        self.assertEqual(p['position'],p['goal'])
        self.assertGreaterEqual(bonus_points(p),10)

    def test_raft_8_and_8(self):
        p=create_puzzle('cargo_balance',random.Random(10))
        target=[1,0,1,1,0] # left weights 2+6 =8
        for i in range(5):
            if p['state'][i]!=target[i]: act(p,'toggle',i)
        self.assertTrue(check_puzzle(p)[0])

    def test_codebreaker_feedback_and_win(self):
        p=create_puzzle('mastermind',random.Random(10))
        self.assertFalse(check_puzzle(p)[0])
        self.assertEqual(len(p['history']),1)
        for i in range(3):
            while p['state'][i]!=p['goal'][i]:act(p,'cycle',i)
        self.assertTrue(check_puzzle(p)[0])
        self.assertEqual(bonus_points(p),30)

    def test_sliding_solve_by_legal_steps(self):
        p=create_puzzle('sliding_tiles',random.Random(10))
        moves=slide_route(p['state'])
        self.assertTrue(moves)
        for idx in moves:result=act(p,'slide',idx)
        self.assertTrue(result)
        self.assertEqual(p['state'],p['goal'])
        self.assertGreaterEqual(bonus_points(p),20)

if __name__=='__main__':
    unittest.main()
