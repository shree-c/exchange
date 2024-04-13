import requests
from time import perf_counter
import pickle
from random import random, randint
import json

url = "http://localhost:8000/order"

headers = {"Content-Type": "application/json"}
punching_start = perf_counter()
orders = pickle.load(open('f.pkl', 'rb'))
for o in orders:
    response = requests.request("POST", url, headers=headers, data=json.dumps(o))
    print(response.text)
punching_stop = perf_counter()

print(punching_stop - punching_start, "perf counter seconds")