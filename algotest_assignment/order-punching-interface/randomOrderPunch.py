import requests
from time import perf_counter
import pickle
from random import random, randint
import json

url = "http://localhost:8000/order"


def generate_random_order():
    return {
        "quantity": randint(10, 100),
        "price": randint(200, 250),
        "side": 1 * (-1 if round(random() * 1) == 1 else 1),
    }


headers = {"Content-Type": "application/json"}
punching_start = perf_counter()
orders = pickle.load(open("f.pkl", "rb"))
USE_SAVED = False
RANDOM_ORDERS = 2E4

if USE_SAVED:
    for o in orders:
        response = requests.request("POST", url, headers=headers, data=json.dumps(o))
        print(response.text)
else:
    print("PUNCHING RANDOM ORDERS")
    for i in range(0, int(RANDOM_ORDERS)):
        response = requests.request(
            "POST", url, headers=headers, data=json.dumps(generate_random_order())
        )
        print(response.text, i+1)

punching_stop = perf_counter()

print(punching_stop - punching_start, "perf counter seconds")
