from AI import use_weight_return_evaluate,make_inputs_from_state,INPUT_LEN
from selfplay import make_state_dataset
from state2 import State, random_action
import numpy as np

LEARNING_RATE = 0.00001
NUM_EPOCHS = 30
NUM_CYCLE = 20

def all_optimize(weight_array: list):
  for _ in range(NUM_CYCLE):
    state_datasets = make_state_dataset(weight_array)
    for _ in range(NUM_EPOCHS):
      for state_dataset in state_datasets:
          
          optimize_weights(state_dataset[0], weight_array, state_dataset[1])
    print(weight_array)
      

# 盤面情報から評価値を出力する
def calculate_score(state, weight_array: list):
  value = use_weight_return_evaluate(state, weight_array)
  return value


# 正解との差error
def calculation_error(state, weight_array: list, correct_value):
  pre_value = calculate_score(state, weight_array)
  error_tanh = (pre_value - correct_value) * (1 - pre_value**2)
  return error_tanh


# 誤差をそれぞれの重みで微分した値をリストで出力
def diff_errors(state, weight_array: list, correct_value):
  inputs = make_inputs_from_state(state)
  delta  = calculation_error(state, weight_array, correct_value)
  return [delta * x for x in inputs] 
  # diff_errors_list = []
  # for i in range(INPUT_LEN):
  #   diff_error = inputs[i] * calculation_error(state, weight_array, correct_value) 
  #   diff_errors_list.append(diff_error)

  # return diff_errors_list


# 各重みを1回最適化
def optimize_weights(state, weight_array: list, correct_value):
  diff_errors_list = diff_errors(state, weight_array, correct_value)
  for i in range(INPUT_LEN):
    weight_array[i] -= diff_errors_list[i] * LEARNING_RATE
  return weight_array

if __name__ == '__main__':
  weight_array = [0.1, 0.1, 0.1, 0.1]
  all_optimize(weight_array)

