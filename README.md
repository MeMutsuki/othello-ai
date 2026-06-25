# Othello AI

ResNetによる評価関数とα-β探索を組み合わせたオセロAIです。

## アーキテクチャ

- **盤面表現**: 自分の石・相手の石・合法手の3チャンネル (3×8×8)
- **評価関数**: ResNet（残差ブロック5層）をPyTorchで実装
- **探索**: α-β探索（深さ5手）+ 終盤14マス以下で完全読みに切替
- **学習**: 自己対戦によるデータ生成

## ファイル構成

| ファイル | 内容 |
|---|---|
| `AI.py` | AIクラス本体（評価関数・探索） |
| `selfplay.py` | 自己対戦による学習データ生成 |
| `state2.py` | 盤面状態の管理 |
| `optimize.py` | モデルの学習ループ |
| `OthelloGUI.py` | GUIで対戦できるインターフェース |
| `battle_edax.py` | Edax（強いオセロエンジン）との対戦 |

## 実行方法

```bash
pip install torch
python OthelloGUI.py  # GUIで対戦
```

## 技術スタック

Python / PyTorch / tkinter
