import subprocess
import time
import os
import random


# ご自身のAI関数と盤面管理クラスをインポート
from AI import search_BestAction
from state2 import State

import pygame
import sys

# --- GUI設定 ---
CELL_SIZE = 60
BOARD_SIZE = CELL_SIZE * 8
GREEN = (34, 139, 34)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Pygameの初期化
pygame.init()
screen = pygame.display.set_mode((BOARD_SIZE, BOARD_SIZE))
pygame.display.set_caption("🤖 自作AI vs 👿 Edax")

def draw_board(state):
    """ 現在の盤面をGUIに描画する関数 """
    # 画面のフリーズを防ぐためのイベント処理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.fill(GREEN)
    
    # 罫線を引く
    for i in range(9):
        pygame.draw.line(screen, BLACK, (0, i * CELL_SIZE), (BOARD_SIZE, i * CELL_SIZE), 2)
        pygame.draw.line(screen, BLACK, (i * CELL_SIZE, 0), (i * CELL_SIZE, BOARD_SIZE), 2)

    # 現在が黒番かどうか
    is_black_turn = state.is_first_player()

    # 64マスをチェックして石を描画
    for i in range(64):
        x = i % 8
        y = i // 8
        center = (x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2)

        # state.pieces は「現在の手番の人の石」
        if state.pieces[i] == 1:
            piece_color = BLACK if is_black_turn else WHITE
            pygame.draw.circle(screen, piece_color, center, CELL_SIZE // 2 - 5)
            
        # state.enemy_pieces は「相手の石」
        elif state.enemy_pieces[i] == 1:
            piece_color = WHITE if is_black_turn else BLACK
            pygame.draw.circle(screen, piece_color, center, CELL_SIZE // 2 - 5)

    pygame.display.flip() # 画面を更新
    
    # 人間が目で追えるように0.5秒（500ミリ秒）ストップする
    pygame.time.wait(500)

def to_edax_move(row, col):
    if row == 8 and col == 0:  # action 64 (パス) の場合
        return "PS"            # Edaxが理解できるパスの合図
    return chr(col + ord('a')) + str(row + 1)

def from_edax_move(move_str):
    if move_str.upper() == "PS" or move_str.upper() == "PASS":
        return 8, 0            # Python内部でのパス (action 64) に戻す
    return int(move_str[1]) - 1, ord(move_str[0].lower()) - ord('a')

def play_against_edax():
    print("⚔️ 自作AI vs Edax 対戦開始！")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    edax_path = os.path.join(script_dir, 'mEdax-4.4-x64-modern')
    
    edax_process = subprocess.Popen(
        [edax_path, '-d', '1'], 
        stdin=subprocess.PIPE, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        text=True,
        cwd=script_dir  # 🌟 ここにカンマを打って、この1行を追加！！！
    )
    
    def read_edax_output():
        output = ""
        while True:
            
            char = edax_process.stdout.read(1)
            if not char:
                break
            
            output += char
            
            # ▼▼ 修正箇所： "edax>" ではなく ">" で待機を解除する！ ▼▼
            if output.endswith("> ") or output.endswith(">"):
                break
        return output

    # 初期化の出力を読み込む
    print("Edaxの起動を待機中...")
    read_edax_output()
    print("Edax起動完了！\n")
    
    # ゲーム状態の初期化
    state = State()
    my_turn = 1 # 1: 黒(自作AI), 2: 白(Edax)
    
    while not state.is_done():
        # 🌟 ループの始まりで、毎回今の盤面を描画する！
        draw_board(state)
        if my_turn == 1:
            print("--- 🤖 自作AIのターン(黒) ---")
            
            my_pieces, enemy_pieces = state.count_pieces()
            total_pieces = my_pieces + enemy_pieces
            
            if total_pieces <= 4:
                # 序盤はランダムに選ぶ（あえて違うルートを開拓させる）
                legal_actions = list(state.legal_actions())
                best_action = random.choice(legal_actions)
                print("(序盤のためランダムに展開を分岐させました)")
            else:
                # 中盤以降はResNetの脳みそと完全読みでガチる
                best_action = search_BestAction(state, depth_limit=5)
            
            # (row, col) に変換してEdaxに伝える
            row, col = best_action // 8, best_action % 8
            move_str = to_edax_move(row, col)
            print(f"自作AIの選択: {move_str.upper()}")
            
            # Edaxに自分が打った手を教える
            edax_process.stdin.write(f"{move_str}\n")
            edax_process.stdin.flush()
            
            # Edaxの返事を読み捨てる（ここでフリーズしなくなります）
            read_edax_output() 
            
            state = state.next(best_action)
            my_turn = 2
        else:
            print("--- 👿 Edaxのターン(白) ---")
            edax_process.stdin.write("go\n")
            edax_process.stdin.flush()
            
            output = read_edax_output()
            edax_move_str = None
            
            # 🌟 修正ポイント："PS" や "PASS" も拾えるようにする
            for word in output.replace('\n', ' ').split():
                clean_word = word.strip().upper()
                if len(clean_word) == 2 and clean_word[0] in 'ABCDEFGH' and clean_word[1] in '12345678':
                    edax_move_str = clean_word
                    break
                elif clean_word in ['PS', 'PASS']:
                    edax_move_str = 'PS'
                    break
            
            if edax_move_str:
                print(f"Edaxの選択: {edax_move_str}")
                if edax_move_str == 'PS':
                    state = state.next(64) # パスを実行
                else:
                    row, col = from_edax_move(edax_move_str)
                    action = row * 8 + col
                    state = state.next(action)
            else:
                # 文字が上手く取れなかった場合も安全にパスとして処理（以前はスルーしてバグってました）
                print("Edaxがパスしました（自動判定）")
                state = state.next(64)
                
            my_turn = 1  

        

    print("\n🏁 対戦終了！")
    # 🌟 追加：最終結果の画面を3秒間（3000ミリ秒）表示したままにする
    draw_board(state)
    pygame.time.wait(3000) 
    
    p1_pieces, p2_pieces = state.count_pieces()
    
    # 🌟 修正ポイント：現在のターンが先手(黒)か後手(白)かで、受け取る色を反転させる！
    if state.is_first_player():
        black_pieces, white_pieces = p1_pieces, p2_pieces
    else:
        black_pieces, white_pieces = p2_pieces, p1_pieces
        
    print(f"黒(自作AI): {black_pieces} 枚")
    print(f"白(Edax)  : {white_pieces} 枚")
    
    edax_process.stdin.write("quit\n")
    edax_process.stdin.flush()

if __name__ == "__main__":
    play_against_edax()