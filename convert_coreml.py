import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

import torch
import coremltools as ct

# AI.pyから作成したCNNモデルをインポート
from AI import OthelloCNNEvaluator

# 1. モデルのインスタンス化と重みのロード
model = OthelloCNNEvaluator() 
# 最適化スクリプトで保存したCNNモデルの重みを読み込む
model.load_state_dict(torch.load("othello_cnn_model.pth", weights_only=True))
model.eval() # 推論モードに切り替え

# 2. ダミー入力の作成
# CNNモデルは [バッチサイズ1, チャンネル2(自石, 敵石), 縦8, 横8] を期待している
dummy_input = torch.zeros(1, 2, 8, 8) 

# 3. JITトレース（PyTorchモデルのグラフ化）
# モデルにダミー入力を通して、内部の計算グラフを記録する
traced_model = torch.jit.trace(model, dummy_input)

# 4. Core ML形式へ変換
# Swift（Xcode）側でデータを渡す時の変数名を "board_state" に定義
# 4. Core ML形式へ変換
input_type = ct.TensorType(name="board_state", shape=dummy_input.shape)

mlmodel = ct.convert(
    traced_model,
    inputs=[input_type],
    convert_to="neuralnetwork"
    # ▼▼▼ 以下の行を削除、または先頭に # をつけてコメントアウトする ▼▼▼
    # minimum_deployment_target=ct.target.iOS16 
)

# 5. iPad用のパッケージとして保存
mlmodel.save("OthelloAI.mlmodel")
print("変換完了！ OthelloAI.mlmodel が生成されました。")