from state2 import State,random_action
import numpy as np

DEPTH_LIMIT = 3
INPUT_LEN = 4
MULTI_DIFFERENCE = 0.00001

def make_inputs_from_state(state) -> list:
  # 確定石の差
  my_stable, enemy_stable = state.count_stable_pieces()
  difference_stable = my_stable - enemy_stable

  #合法手数の差
  my_actions, enemy_actions = state.count_legal_actions()
  difference_actions = my_actions - enemy_actions

  #各プレイヤーの石の数の差
  my_pieces, enemy_pieces =  state.count_pieces()
  difference_pieces = my_pieces - enemy_pieces

  danger_my, danger_enemy = state.count_danger_pieces()
  difference_danger = danger_my - danger_enemy
  
  if INPUT_LEN == 4:
    list_inputs =[difference_stable, difference_actions, difference_pieces, difference_danger]
  return list_inputs

# 評価値
def use_weight_return_evaluate(state, weight_array: list) -> float:
  if state.is_done():
    if state.is_lose():
      return -1
    elif state.is_draw():
      return 0
    else:
      return 1
  inputs = make_inputs_from_state(state)
  value = 0
  for i in range(INPUT_LEN):
    value += weight_array[i]*inputs[i]
  tanh_value = np.tanh(value)
  return  tanh_value


def search_BestAction(state,weight_array) -> int:
  list_LegalActions = state.legal_actions()
  min_score = 1000000000
  best_action = -1


  for action in list_LegalActions:
    next_state = state.next(action)
    value = use_weight_return_evaluate(next_state, weight_array)
    if value < min_score:
      min_score = value
      best_action = action
  
  return best_action
    
def handmake_AI(state):
  a = 0.1 if state.depth <= 30 else 0.05 if state.depth <= 50 else 0.02
  b = 0.001 if state.depth <= 50 else 0
  c = 0 if state.depth <= 30 else 0.001 if state.depth <= 50 else 0.002
  d = -0.05 if state.depth <= 30 else -0.03 if state.depth <= 50 else -0.01
  weight_array = [a,b,c,d]
  return search_BestAction(state,weight_array)


def alpha_beta(state, alpha, beta, weight_array: list, depth = 1):
    
    # 負けは状態価値-1
    if state.is_lose():
        my_pieces, enemy_pieces =  state.count_pieces()
        difference_pieces = (my_pieces - enemy_pieces) * MULTI_DIFFERENCE
        return -1 + difference_pieces
    
    # 引き分けは状態価値0
    if state.is_draw():
        return 0
    
    if depth == DEPTH_LIMIT:
       return use_weight_return_evaluate(state, weight_array)

    # 合法手の状態価値の計算
    for action in state.legal_actions():
        score = -alpha_beta(state.next(action), -beta, -alpha, weight_array, depth + 1)
        if score > alpha:
            alpha = score
        
        # 現ノードのベストスコアが親ノードを超えたら探索終了
        if alpha >= beta:
            return alpha
        
    return alpha


def alpha_beta_action(state, weight_array, depth = 1):
    best_action = 0
    alpha = -float('inf')
    for action in state.legal_actions():
        score = -alpha_beta(state.next(action),  -float('inf'), -alpha, weight_array, depth)
        if score > alpha:
            best_action = action
            alpha = score
    return best_action


def mini_max(state, alpha, beta):
    # 負けは状態価値-1
    if state.is_lose():
        return -1
    
    # 引き分けは状態価値0
    if state.is_draw():
        return 0
    
    best_score = -float('inf')
    for action in state.legal_actions():
        score = -mini_max(state.next(action))
        if score > best_score:
            best_score = score
    return best_score

        
def mini_max_action(state):
    best_action = 0
    best_score = -float('inf')
    for action in state.legal_actions():
        score = -mini_max(state.next(action))
        if score > best_score:
            best_action = action
            best_score = score  

    return best_action