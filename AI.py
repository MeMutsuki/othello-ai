import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from state2 import State, random_action

DEPTH_LIMIT = 5
MULTI_DIFFERENCE = 0.00001

# デバイスの設定
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

# ----------------------------------------
# 1. CNNモデルの定義 (ResNet)
# ----------------------------------------
class ResBlock(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(channels)

    def forward(self, x):
        residual = x  
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += residual  
        return F.relu(out)

class OthelloCNNEvaluator(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv_in = nn.Conv2d(in_channels=3, out_channels=64, kernel_size=3, padding=1)
        self.bn_in = nn.BatchNorm2d(64)
        
        self.res1 = ResBlock(64)
        self.res2 = ResBlock(64)
        self.res3 = ResBlock(64)
        
        self.fc1 = nn.Linear(64 * 8 * 8, 256)
        self.fc2 = nn.Linear(256, 1)

    def forward(self, x):
        x = F.relu(self.bn_in(self.conv_in(x)))
        x = self.res1(x)
        x = self.res2(x)
        x = self.res3(x)
        
        x = x.view(x.size(0), -1) 
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        
        return torch.tanh(x)

# モデルの準備とロード
model = OthelloCNNEvaluator().to(device)
if os.path.exists('othello_cnn_model.pth'):
    model.load_state_dict(torch.load('othello_cnn_model.pth', weights_only=True, map_location=device))
model.eval()

# ----------------------------------------
# 2. 盤面を画像テンソルに変換する処理
# ----------------------------------------
def make_cnn_inputs_from_state(state):
    # ① 自分の石の配置
    my_board = np.array(state.pieces, dtype=np.float32).reshape(8, 8)
    # ② 相手の石の配置
    enemy_board = np.array(state.enemy_pieces, dtype=np.float32).reshape(8, 8)
    
    # ③ 🌟 NEW：合法手（今自分が打てる場所）の配置マップ
    legal_board = np.zeros(64, dtype=np.float32)
    for action in state.legal_actions():
        if action != 64:  # パス(64)以外なら、そのマスを1.0(明るく)する
            legal_board[action] = 1.0
    legal_board = legal_board.reshape(8, 8)
    
    # 🌟 2枚から「3枚」の画像を重ねて返すように変更！
    return np.stack([my_board, enemy_board, legal_board])

# ----------------------------------------
# 3. 評価関数のPyTorch推論
# ----------------------------------------
def use_weight_return_evaluate(state) -> float:
    if state.is_done():
        if state.is_lose(): return -1
        elif state.is_draw(): return 0
        else: return 1
            
    inputs = make_cnn_inputs_from_state(state)
    inputs_tensor = torch.tensor(inputs, dtype=torch.float32).unsqueeze(0).to(device)
    
    with torch.no_grad():
        value = model(inputs_tensor)
        
    return value.item()

# ----------------------------------------
# 4. アルファベータ法による探索（完全読み対応）
# ----------------------------------------
# ----------------------------------------
# 4. アルファベータ法による探索
# ----------------------------------------
def alpha_beta(state, alpha, beta, depth_limit, current_depth=1):
    my_pieces, enemy_pieces = state.count_pieces()
    
    if state.is_lose():
        difference_pieces = (my_pieces - enemy_pieces) * MULTI_DIFFERENCE
        return -1 + difference_pieces
    if state.is_draw():
        return 0

    # 🌟 変更：未来の盤面で「12マスだ！」と暴走しないように、ここでの判定は削除！
    
    # 指定された探索深さ(5手など)に到達した場合は、CNNの勘に頼る
    if current_depth >= depth_limit:
       return use_weight_return_evaluate(state)

    for action in state.legal_actions():
        score = -alpha_beta(state.next(action), -beta, -alpha, depth_limit, current_depth + 1)
        if score > alpha:
            alpha = score
        if alpha >= beta:
            return alpha
    return alpha

def alpha_beta_action(state, depth_limit=5):
    # 🌟 NEW：現実の盤面で空きマスを数える！
    my_pieces, enemy_pieces = state.count_pieces()
    empty_squares = 64 - (my_pieces + enemy_pieces)
    
    # 🌟 NEW：現実の空きマスがn以下なら、深さ制限を「64（無限）」にして完全読み化する！
    if empty_squares <= 14:
        depth_limit = 64

    best_action = 0
    alpha = -float('inf')
    for action in state.legal_actions():
        score = -alpha_beta(state.next(action), -float('inf'), -alpha, depth_limit, 1)
        if score > alpha:
            best_action = action
            alpha = score
    return best_action

# ----------------------------------------
# 5. 外部から呼ばれるメインの行動決定関数
# ----------------------------------------
def search_BestAction(state, depth_limit=5) -> int:
    return alpha_beta_action(state, depth_limit=depth_limit)
    
def handmake_AI(state):
    return search_BestAction(state)