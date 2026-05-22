import os
os.environ['OMP_NUM_THREADS'] = '1' # 🌟 NEW: 作業員の頭の中を整理するおまじない
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
import multiprocessing # 追加
multiprocessing.set_start_method('spawn', force=True) # 🌟 Mac用の安全なおまじない
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader # 🌟 追加：データローダー
import numpy as np

from AI import OthelloCNNEvaluator, make_cnn_inputs_from_state
from selfplay import make_state_dataset

LEARNING_RATE = 0.0001
NUM_EPOCHS = 5
NUM_CYCLE = 50
BATCH_SIZE = 128  # 🌟 NEW：ミニバッチのサイズ（一度に128個ずつGPUに送る）

# M1チップ(MPS)の設定
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
#print(f"使用するデバイス: {device}")

def augment_data(state_datasets):
    augmented_inputs = []
    augmented_labels = []
    
    for state, correct_value in state_datasets:
        base_input = make_cnn_inputs_from_state(state)
        for k in range(4):
            rotated = np.rot90(base_input, k, axes=(1, 2))
            
            augmented_inputs.append(rotated)
            augmented_labels.append([correct_value])
            
            flipped = np.flip(rotated, axis=2) 
            augmented_inputs.append(flipped)
            augmented_labels.append([correct_value])
            
    return augmented_inputs, augmented_labels


def optimize_with_pytorch():
    model = OthelloCNNEvaluator().to(device)
    
    if os.path.exists('othello_cnn_model.pth'):
        try:
            model.load_state_dict(torch.load('othello_cnn_model.pth', weights_only=True, map_location=device))
            print("既存のモデルを読み込みました。")
        except RuntimeError:
            print("⚠️ 脳の構造(ResNet)が変わったため、古い othello_cnn_model.pth は破棄してゼロから学習します！")

    criterion = nn.MSELoss() 
    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE)

    for cycle in range(NUM_CYCLE):
        print(f"--- Cycle {cycle + 1}/{NUM_CYCLE} ---")
        torch.save(model.state_dict(), 'othello_cnn_model.pth')

        # === 👇 ここで止まっている可能性大！ ===
        print("🤖 自己対局データを作成中...（時間がかかる場合は selfplay.py の深さ設定を見直します）")
        state_datasets = make_state_dataset()
        print("✨ データ作成完了！水増し＆学習フェーズに入ります。")

        inputs_list, labels_list = augment_data(state_datasets)
        
        # 🌟 修正ポイント：この時点ではまだGPU(device)に送らない！（メインメモリに置いとく）
        inputs_tensor = torch.tensor(np.array(inputs_list).copy(), dtype=torch.float32)
        labels_tensor = torch.tensor(labels_list, dtype=torch.float32)
        
        # 🌟 NEW：TensorDataset と DataLoader でミニバッチ化（シャッフルも自動！）
        dataset = TensorDataset(inputs_tensor, labels_tensor)
        dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
        
        model.train()
        for epoch in range(NUM_EPOCHS):
            total_loss = 0
            
            # 🌟 ベルトコンベアで64個ずつデータを取り出す
            for batch_inputs, batch_labels in dataloader:
                # 使う直前に、小分けにしたデータをGPU(device)へ送る！
                batch_inputs = batch_inputs.to(device)
                batch_labels = batch_labels.to(device)

                optimizer.zero_grad()                    
                outputs = model(batch_inputs)           
                loss = criterion(outputs, batch_labels) 
                loss.backward()                          
                optimizer.step()
                
                total_loss += loss.item()

            # エポックごとの平均Lossを表示
            avg_loss = total_loss / len(dataloader)
            print(f"  Epoch {epoch+1}/{NUM_EPOCHS} 完了 - Loss: {avg_loss:.4f}")
            
    torch.save(model.state_dict(), 'othello_cnn_model.pth')
    print("🎉 学習完了！ 新生ResNetの脳みそを保存しました！")

if __name__ == '__main__':
    optimize_with_pytorch()