import random
def make_data(): 
  datas = []
  a = 2.13
  b = 100
  for _ in range(1000):
    x = random.random()*200-100
    y = a * x + b + (random.random()*10-5)
    datas.append((x,y))
  return datas
datas=make_data()
print(datas)

def Liner(x, a, b): 
  y = a * x + b
  return y

def predict_y(x,a,b,Liner=Liner):
  y = Liner(x,a,b)
  return y

def calculation_error(x, a, b, label_y,predict_y=predict_y):
  pre_y = predict_y(x,a,b)
  error = pre_y - label_y
  return error

def diff_error_a(x, a, b, label_y,calculation_error=calculation_error):
  y =  x * calculation_error(x,a,b,label_y) 
  return y

def diff_error_b( x, a, b, label_y,calculation_error=calculation_error):
  y = calculation_error(x,a,b,label_y) 
  return y

def optimize_a(x,a,b,label_y,diff_error_a=diff_error_a):
  g = diff_error_a(x,a,b,label_y)
  a -= g * 0.0001
  return a

def optimize_b(x,a,b,label_y,diff_error_b=diff_error_b):
  g = diff_error_b(x,a,b,label_y)
  b -= g * 0.0001
  return b

def one_optimize(data,a,b,optimize_a=optimize_a,optimize_b=optimize_b):
  x = data[0]
  label_y = data[1]
  one_a = optimize_a(x,a,b,label_y)
  one_b = optimize_b(x,a,b,label_y) 
  return one_a, one_b

def alldata_optimize(datas,a,b,one_optimze=one_optimize):

  for _ in range(100):
    print(a,b)
    for data in datas:
      a,b = one_optimize(data,a,b)
  return a, b

a = 3
b = 5
print(alldata_optimize(datas,a,b))