import requests
from random import random, randint
import json
from time import sleep

url = "http://localhost:8000/order"


def generate_random_order():
    return {
        "quantity": randint(10, 100),
        "price": randint(200, 250),
        "side": 1 * (-1 if round(random() * 1) == 1 else 1),
    }


headers = {"Content-Type": "application/json"}

while True:
  # payload = json.dumps({"quantity": 300, "price": 200.2, "side": 1})
  response = requests.request("POST", url, headers=headers, data=json.dumps(generate_random_order()))
  print(response.text)
  sleep(0.02)
