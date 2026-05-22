import random
import multiprocessing
from tqdm import tqdm

from state2 import State, random_action
from AI import search_BestAction

# 1サイクルあたりの試合数（細切れで回すなら50〜80くらいがおすすめ）
NUM_GAMES = 80 

# ==========================================
# 1. 1試合分の自己対局を行う関数
# ==========================================
def state_logs():
    """1試合分の自己対局を行い、その履歴と勝敗ラベルを返す"""
    state = State()
    history = []
    
    # --- 対局ループ ---
    while not state.is_done():
        # 今の盤面を履歴に保存
        history.append(state)
        
        # 【思考のメリハリ（深さ調整）】
        
        # 序盤（4手目まで）：ランダムに打って多様な盤面を作る
        if state.depth <= 4:
            action = random_action(state)
            state = state.next(action)
            
        # 中盤（16〜45手目）：ここが一番大事！
        elif state.depth <= 45:
            # 20%の確率でわざと変な手（ランダム）を打って経験値を稼ぐ
            if random.random() < 0.2:
                action = random_action(state)
                state = state.next(action)
            else:
                # 残り80%は【深さ3】で相手の反撃の反撃までガチで読む！
                action = search_BestAction(state, depth_limit=2)
                state = state.next(action)
                
        # 終盤（46手目以降）：すでに勝敗ルートは決まりつつあるので直感（深さ1）でパパッと打つ
        else:
            action = search_BestAction(state, depth_limit=1)
            state = state.next(action)

    # --- 試合終了後のラベル付け（勝敗判定） ---
    # 最終的な石数を数える
    my_pieces, enemy_pieces = state.count_pieces()
    
    # この最終局面で手番だった人から見て勝ったか負けたか
    if my_pieces > enemy_pieces:
        final_reward = 1
    elif my_pieces < enemy_pieces:
        final_reward = -1
    else:
        final_reward = 0
        
    # 先手(黒)から見た勝敗を確定
    black_reward = final_reward if state.is_first_player() else -final_reward

    # 履歴に入っているすべての盤面に「この盤面の手番の人にとって、最終的に勝つか負けるか」を紐付ける
    dataset = []
    for s in history:
        reward = black_reward if s.is_first_player() else -black_reward
        dataset.append((s, reward))
        
    return dataset

# ==========================================
# 2. 並列処理（マルチプロセス）用のダミー関数
# ==========================================
def _play_single_game(dummy_index):
    """並列処理の作業員が1試合だけ担当するための関数"""
    return state_logs()

# ==========================================
# 3. 外部（optimize.pyなど）から呼ばれるメイン処理
# ==========================================
def make_state_dataset():
    dataset = []
    
    # 🌟 フリーズ対策：8コアフル稼働だとMacが息切れするので、安全に「最大6コア」に制限！
    num_cores = min(multiprocessing.cpu_count(), 6)
    
    # tqdmプログレスバーが崩れないように、余計なprintはしない
    # プログレスバー自体が「今何試合進んでいるか」を教えてくれます
    with multiprocessing.Pool(processes=num_cores) as pool:
        # 🌟 tqdm（プログレスバー）で並列処理を包み込む！
        iterator = pool.imap_unordered(_play_single_game, range(NUM_GAMES))
        results = list(tqdm(iterator, total=NUM_GAMES, desc="対局進行度", ncols=80, colour="green"))
    
    # 各試合のデータ（リストのリスト）を1つの大きなデータセットに合体させる
    for single_game_log in results:
        dataset.extend(single_game_log)
        
    return dataset