import random
import math


# 定数定義
BOARD_SIZE = 8
BOARD_LEN = BOARD_SIZE * BOARD_SIZE

class State:
    #初期化
    def __init__(self, pieces=None, enemy_pieces=None, depth=0):
        # 方向定数
        self.dxy = ((1, 0), (1, 1), (0, 1), (-1, 1),
                    (-1, 0), (-1, -1), (0, -1), (1, -1))
        
        # 連続パスによる終了
        self.pass_end = False

        # 石の配置
        self.pieces = pieces
        self.enemy_pieces = enemy_pieces
        self.depth = depth

        # 石の初期配置
        if pieces is None or enemy_pieces is None:
            self.pieces = [0] * BOARD_LEN
            self.enemy_pieces = [0] * BOARD_LEN
            mid = BOARD_SIZE // 2
            self.enemy_pieces[(mid - 1) + (mid - 1) * BOARD_SIZE] = 1
            self.enemy_pieces[mid + mid * BOARD_SIZE] = 1
            self.pieces[mid + (mid - 1) * BOARD_SIZE] = 1
            self.pieces[(mid - 1) + mid * BOARD_SIZE] = 1

    # 石の数の収得数 引き分けかどうかの判定
    def piece_count(self, pieces):
        return sum(1 for i in pieces if i == 1)

    #負けかどうか
    def is_lose(self):
        return self.is_done() and self.piece_count(self.pieces) < self.piece_count(self.enemy_pieces)

    #引き分けかどうか
    def is_draw(self):
        return self.is_done() and self.piece_count(self.pieces) == self.piece_count(self.enemy_pieces)

    #ゲーム終了かどうか
    def is_done(self):
        return self.piece_count(self.pieces) + self.piece_count(self.enemy_pieces) == BOARD_LEN or self.pass_end

    #次の状態の取得:actionはどこの配列に石を置くかの整数
    def next(self, action :int): 
        state = State(self.pieces.copy(), self.enemy_pieces.copy(), self.depth + 1)
        if action != BOARD_LEN:
            state.is_legal_action_xy(action % BOARD_SIZE, int(action / BOARD_SIZE), True)
        w = state.pieces
        state.pieces = state.enemy_pieces
        state.enemy_pieces = w

        # 二回連続パス判定
        if action == BOARD_LEN and state.legal_actions() == [BOARD_LEN]:
            state.pass_end = True
        return state

    # 合法手のリストの取得
    def legal_actions(self) -> list:
        actions = []
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if self.is_legal_action_xy(i, j):
                    actions.append(i + j * BOARD_SIZE)
        if not actions:
            actions.append(BOARD_LEN)  # パス
        return actions

    # 任意のマスが合法手かどうか
    def is_legal_action_xy(self, x, y, flip=False):
        # 任意のマスの任意の方向が合法手かどうか
        def is_legal_action_xy_dxy(x, y, dx, dy) -> bool:
            # 1つ目 相手の石
            x, y = x + dx, y + dy
            if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE) or \
                    self.enemy_pieces[x + y * BOARD_SIZE] != 1:
                return False

            # 2つ目以降
            for _ in range(BOARD_SIZE):
                x, y = x + dx, y + dy
                if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
                    return False
                
                # 自分の石
                index = x + y * BOARD_SIZE
                if self.pieces[index] == 1:
                    # 反転
                    if flip:
                        for _ in range(BOARD_SIZE):
                            x, y = x - dx, y - dy
                            idx = x + y * BOARD_SIZE
                            if self.pieces[idx] == 1:
                                return True
                            self.pieces[idx] = 1
                            self.enemy_pieces[idx] = 0
                    return True
                
                
                if self.pieces[index] == 0 and self.enemy_pieces[index] == 0:
                    return False
            return False
        
        #空きなし
        if self.enemy_pieces[x + y * BOARD_SIZE] == 1 or self.pieces[x + y * BOARD_SIZE] == 1:
            return False

        # 石をおく
        if flip:
            self.pieces[x + y * BOARD_SIZE] = 1

        flag = False
        for dx, dy in  self.dxy:
            if is_legal_action_xy_dxy(x, y, dx, dy):
                flag = True        
        return flag


    # 先手かどうか
    def is_first_player(self):
        return self.depth % 2 == 0


    # 文字列表示
    def __str__(self):
        ox = ('o', 'x') if self.is_first_player() else ('x', 'o')
        s = ''
        for i in range(BOARD_LEN):
            if self.pieces[i] == 1:
                s += ox[0]
            elif self.enemy_pieces[i] == 1:
                s += ox[1]
            else:
                s += '-'
            if i % BOARD_SIZE == BOARD_SIZE - 1:
                s += '\n'
        return s
    
    # 各プレイヤーの石の数を返す
    def count_pieces(self):
        return self.piece_count(self.pieces), self.piece_count(self.enemy_pieces)

    # 各プレイヤーの合法手数を返す
    def count_legal_actions(self):
        # 自分の手番での合法手数
        my_actions = len([a for a in self.legal_actions() if a != BOARD_LEN])

        # 相手の立場にしたときの合法手数
        temp_state = State(self.enemy_pieces.copy(), self.pieces.copy(), self.depth + 1)
        enemy_actions = len([a for a in temp_state.legal_actions() if a != BOARD_LEN])
        return my_actions, enemy_actions

    # 各プレイヤーの確定石（stable discs）を正確に数える
    def count_stable_pieces(self) -> tuple[int, int]:
        """
        戻り値:
            (stable_my, stable_enemy)
            └ self.pieces 側 / self.enemy_pieces 側の確定石数
        """

        # 盤を「色配列」に変換: 1 = self.pieces, -1 = enemy, 0 = empty
        color = [0] * BOARD_LEN
        for i in range(BOARD_LEN):
            if self.pieces[i]:
                color[i] = 1
            elif self.enemy_pieces[i]:
                color[i] = -1

        # 4 軸のペア（左右, 上下, 斜め, 逆斜め）
        axis_pairs = [((1, 0),  (-1, 0)),     # ⇄
                      ((0, 1),  ( 0, -1)),    # ↕
                      ((1, 1),  (-1, -1)),    # ↘↖
                      ((1, -1), (-1, 1))]     # ↗↙

        def is_solid(idx, dx, dy):
            """idx から (dx,dy) 方向が端まで同色なら True"""
            x, y = idx % BOARD_SIZE + dx, idx // BOARD_SIZE + dy
            while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
                if color[x + y * BOARD_SIZE] != color[idx]:
                    return False
                x += dx
                y += dy
            return True          # 盤外に出るまで同色

        stable = [False] * BOARD_LEN
        for idx in range(BOARD_LEN):
            if color[idx] == 0:
                continue
            # 4 軸全てで「片側だけでも solid」であれば確定
            ok = True
            for pair in axis_pairs:
                if not any(is_solid(idx, dx, dy) for dx, dy in pair):
                    ok = False
                    break
            stable[idx] = ok

        stable_my    = sum(1 for i in range(BOARD_LEN)
                           if stable[i] and color[i] == 1)
        stable_enemy = sum(1 for i in range(BOARD_LEN)
                           if stable[i] and color[i] == -1)
        return stable_my, stable_enemy
    # ──────────────────────────────────────────────────────────────
    # 隅の隣の未確定石（＝危険石）をカウント
    # ──────────────────────────────────────────────────────────────
    def count_danger_pieces(self) -> tuple[int, int]:
        """
        Returns
        -------
        (danger_my, danger_enemy) : tuple[int, int]
            self.pieces 側 / self.enemy_pieces 側が持つ
            「隅に隣接していて確定石ではない石」の個数
        """
        # 盤面を色配列へ: 1=self.pieces, -1=enemy, 0=empty
        color = [0] * BOARD_LEN
        for i in range(BOARD_LEN):
            if self.pieces[i]:
                color[i] = 1
            elif self.enemy_pieces[i]:
                color[i] = -1

        # --- まず確定石を判定（count_stable_pieces と同ロジック） ---
        axis_pairs = [((1, 0),  (-1, 0)),     # ⇄
                      ((0, 1),  ( 0, -1)),    # ↕
                      ((1, 1),  (-1, -1)),    # ↘↖
                      ((1, -1), (-1, 1))]     # ↗↙

        def is_solid(idx, dx, dy):
            x, y = idx % BOARD_SIZE + dx, idx // BOARD_SIZE + dy
            while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
                if color[x + y * BOARD_SIZE] != color[idx]:
                    return False
                x += dx
                y += dy
            return True

        stable = [False] * BOARD_LEN
        for idx in range(BOARD_LEN):
            if color[idx] == 0:
                continue
            if all(any(is_solid(idx, dx, dy) for dx, dy in pair)
                   for pair in axis_pairs):
                stable[idx] = True

        # --- 隅の隣接 12 マスのリストを作成 ---
        corner_adjacent = []
        for cx, cy in ((0, 0), (BOARD_SIZE-1, 0),
                       (0, BOARD_SIZE-1), (BOARD_SIZE-1, BOARD_SIZE-1)):
            for dx in (0, 1):
                for dy in (0, 1):
                    if dx == 0 and dy == 0:
                        continue          # 隅そのもの
                    x, y = cx + (1 if cx == 0 else -1)*dx, cy + (1 if cy == 0 else -1)*dy
                    if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
                        corner_adjacent.append(x + y * BOARD_SIZE)

        # --- 危険石をカウント ---
        danger_my = danger_enemy = 0
        for idx in corner_adjacent:
            if color[idx] == 0 or stable[idx]:
                continue           # 空きマス or 確定石は対象外
            if color[idx] == 1:
                danger_my += 1
            else:                  # -1
                danger_enemy += 1

        return danger_my, danger_enemy


def random_action(state):
    legal_actions = state.legal_actions()
    return legal_actions[random.randint(0, len(legal_actions) - 1)]
  
    

if __name__ == '__main__':
    state = State()
    while True:
        if state.is_done():
            break
    
        state = state.next(random_action(state))
        
        print(state)
        print()

        my_stable, enemy_stable = state.count_stable_pieces()
        print(f"確定石 - 自分: {my_stable}, 相手: {enemy_stable}")
        print('---')