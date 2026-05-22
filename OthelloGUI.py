import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

import tkinter as tk
from tkinter import messagebox
from state2 import State, random_action
from AI import search_BestAction, handmake_AI, alpha_beta_action



#correct_weights =[0.055980660761599445, 0.048649208664763216, 0.00919069827921864, -0.19286562234653232]
#tanh追加前[0.051851295726979385, 0.013011923541089255, -0.009678475551132368, 0.0444113617014096]

# ---------------- 盤面ロジック ---------------- #
BOARD_SIZE = 8
BOARD_LEN = BOARD_SIZE * BOARD_SIZE

# ---------------- GUI 定数 ---------------- #
SQUARE_SIZE = 64          # 1 マスのピクセルサイズ
BORDER = 12               # 盤面外枠のオフセット
AI_ENABLED = True         # False にすると 2 人対戦
HUMAN_IS_BLACK = False    # True: 先手が人
USE_AI = True             # 外部 AI を使うかどうか


class OthelloGUI:
    """Tkinter を使った簡易オセロ GUI"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("OthelloGUI")

        canvas_px = SQUARE_SIZE * BOARD_SIZE + BORDER * 2
        self.cv = tk.Canvas(
            root,
            width=canvas_px,
            height=canvas_px,
            bg="#006400",  # 濃い緑
            highlightthickness=0,
        )
        self.cv.pack(padx=10, pady=10)
        self.cv.bind("<Button-1>", self.on_click)

        self.state: State = State()
        self.last_action: int | None = None  # 直前(１手前)の着手位置

        # 先手が AI なら最初の 1 手を打たせる
        if not HUMAN_IS_BLACK and AI_ENABLED:
            self.root.after(1, self.cpu_move)

        self.draw_board()
        self.redraw()

    # ─────────────────────────────────────────
    # 盤面背景・枠・グリッド線は固定なので 1 回だけ描画
    def draw_board(self):
        size = SQUARE_SIZE * BOARD_SIZE
        # 木製の外枠
        self.cv.create_rectangle(
            BORDER - 6,
            BORDER - 6,
            BORDER + size + 6,
            BORDER + size + 6,
            fill="#8B4513",
            width=0,
        )
        # 緑の盤面
        self.cv.create_rectangle(
            BORDER,
            BORDER,
            BORDER + size,
            BORDER + size,
            fill="#006400",
            width=0,
        )

        # グリッド線
        for i in range(BOARD_SIZE + 1):
            x = BORDER + i * SQUARE_SIZE
            y = BORDER + i * SQUARE_SIZE
            self.cv.create_line(x, BORDER, x, BORDER + size, fill="black")
            self.cv.create_line(BORDER, y, BORDER + size, y, fill="black")

    # ─────────────────────────────────────────
    # 盤面上の石・合法手ハイライト・直前着手ハイライトを毎ターン描画
    def redraw(self):
        # 前回描画をクリア
        self.cv.delete("highlight")
        self.cv.delete("stone")

        # 直前(１手前)に打たれたマスを黄色い枠でハイライト
        if self.last_action is not None and self.last_action != BOARD_LEN:
            x_last = self.last_action % BOARD_SIZE
            y_last = self.last_action // BOARD_SIZE
            x1 = BORDER + x_last * SQUARE_SIZE
            y1 = BORDER + y_last * SQUARE_SIZE
            x2 = x1 + SQUARE_SIZE
            y2 = y1 + SQUARE_SIZE
            self.cv.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                outline="yellow",
                width=3,
                tags="highlight",
            )

        # --- 先手＝黒 / 後手＝白 を固定で描画 ---------------------
        if self.state.is_first_player():
            black_mask = self.state.pieces
            white_mask = self.state.enemy_pieces
        else:
            black_mask = self.state.enemy_pieces
            white_mask = self.state.pieces

        for idx in range(BOARD_LEN):
            x = idx % BOARD_SIZE
            y = idx // BOARD_SIZE
            cx = BORDER + x * SQUARE_SIZE + SQUARE_SIZE // 2
            cy = BORDER + y * SQUARE_SIZE + SQUARE_SIZE // 2
            r = SQUARE_SIZE // 2 - 4

            if black_mask[idx]:
                self.cv.create_oval(
                    cx - r,
                    cy - r,
                    cx + r,
                    cy + r,
                    fill="black",
                    outline="black",
                    tags="stone",
                )
            elif white_mask[idx]:
                self.cv.create_oval(
                    cx - r,
                    cy - r,
                    cx + r,
                    cy + r,
                    fill="white",
                    outline="black",
                    tags="stone",
                )

        # 合法手を半透明のライムグリーンで表示
        for a in [a for a in self.state.legal_actions() if a != BOARD_LEN]:
            x = a % BOARD_SIZE
            y = a // BOARD_SIZE
            cx = BORDER + x * SQUARE_SIZE + SQUARE_SIZE // 2
            cy = BORDER + y * SQUARE_SIZE + SQUARE_SIZE // 2
            r = SQUARE_SIZE // 2 - 4
            self.cv.create_oval(
                cx - r,
                cy - r,
                cx + r,
                cy + r,
                fill="#32CD32",
                outline="",
                stipple="gray25",
                tags="stone",
            )

    # ─────────────────────────────────────────
    # 着手可能手が無ければパスして手番を進める
    def auto_pass_if_needed(self) -> bool:
        if self.state.legal_actions() == [BOARD_LEN]:
            # パス
            self.state = self.state.next(BOARD_LEN)
            self.after_move()
            return True
        return False

    # ─────────────────────────────────────────
    # 人のクリック入力
    def on_click(self, event):
        # ボード座標に変換
        x = (event.x - BORDER) // SQUARE_SIZE
        y = (event.y - BORDER) // SQUARE_SIZE
        if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
            return

        action = x + y * BOARD_SIZE
        if action not in self.state.legal_actions():
            return  # 非合法手は無視

        self.last_action = action  # 直前着手を記録
        self.state = self.state.next(action)  # 人の着手
        self.after_move()

    # ─────────────────────────────────────────
    # CPU の着手
    def cpu_move(self):
        if self.state.is_done():
            return

        if USE_AI:
            if self.state.depth <= 20:
                action = handmake_AI(self.state)
            elif sum(self.state.count_pieces()) >= 54:
                # 変更前: action = alpha_beta_action(self.state, correct_weights, -10000000)   
                action = alpha_beta_action(self.state, -10000000) # correct_weightsを削除！
            else:
                # 変更前: action = alpha_beta_action(self.state, correct_weights)
                action = alpha_beta_action(self.state) # correct_weightsを削除！


        else:
            action = random_action(self.state)

        self.last_action = action  # 直前着手を記録
        self.state = self.state.next(action)
        self.after_move()

    # ─────────────────────────────────────────
    # 1 手指した後の共通処理
    def after_move(self):
        self.redraw()

        # 次プレイヤーに合法手が無ければ即パス
        if not self.state.is_done() and self.auto_pass_if_needed():
            return  # パスにより手番が進み、after_move が再帰呼び出し済み

        # ゲーム終了判定
        if self.state.is_done():
            # 盤の絶対色で数え直す
            if self.state.is_first_player():
                black = self.state.piece_count(self.state.pieces)
                white = self.state.piece_count(self.state.enemy_pieces)
            else:
                black = self.state.piece_count(self.state.enemy_pieces)
                white = self.state.piece_count(self.state.pieces)

            if self.state.is_draw():
                msg = f"Draw!\nBlack {black} - White {white}"
            elif (black > white) == HUMAN_IS_BLACK:
                msg = f"You win! 🎉\nBlack {black} - White {white}"
            else:
                msg = f"You lose…\nBlack {black} - White {white}"
            messagebox.showinfo("Game Over", msg)
            return

        # 現在の手番が AI なら自動で次の CPU 着手をスケジューリング
        if AI_ENABLED:
            ai_turn = (self.state.is_first_player() and not HUMAN_IS_BLACK) or (
                not self.state.is_first_player() and HUMAN_IS_BLACK
            )
            if ai_turn:
                self.root.after(1, self.cpu_move)


# ---------------- 実行 ---------------- #
if __name__ == "__main__":
    root = tk.Tk()
    OthelloGUI(root)
    root.mainloop()
