from time import sleep
import json
from om.env import env_settings
import pika


def calculate_depth(table, depth, reverse = False):
    hold = {}
    # print(table._getvalue().keys())
    for price in sorted(table._getvalue().keys(), reverse=reverse):
        # print(price, value)
        if len(hold) == depth:
            break
        quantities = []
        for item in table[price]._getvalue():
            if item['price'] == price and not item['cancelled']:
                if item['punched'] > item ['quantity']:
                    print('*' * 100)
                    print('FUCK YOU THIS SHOULD NOT HAVE HAPPENED PUNCHED GREATER THAN QUANTITY IDIOT')
                    print('*' * 100)
                    raise Exception('')
                else:
                    quantities.append(
                        item['quantity'] - item['punched']
                    )
            
        summed = sum(quantities)
        if summed != 0:
            hold[price] = summed
    return hold


def bid_ask_spread(buy_price_table, sell_price_table, depth):
    x = {
        "buy": calculate_depth(buy_price_table, depth, reverse=True),
        "sell": calculate_depth(sell_price_table, depth),
    }
    # print(x)
    return x


def broadcast_bid_ask(buy_price_table, sell_price_table, depth):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            "localhost",
        )
    )
    channel = connection.channel()

    while True:
        # print("BROADCASTING BID ASK ...")
        # json_str = bid_ask_spread(buy_price_table, sell_price_table, depth)
        # print(bid_ask_spread(buy_price_table, sell_price_table, depth))
        channel.basic_publish(
            exchange=env_settings.bid_ask_exchange,
            routing_key="",
            body=json.dumps(bid_ask_spread(buy_price_table, sell_price_table, depth)),
        )
        sleep(0.3)


def broadcast_trades(trade_queue):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            "localhost",
        )
    )
    channel = connection.channel()

    while True:
        # print("BROADCASTING TRADES...")
        trade = trade_queue.get()
        # print(trade)
        trade["action"] = "trade"
        channel.basic_publish(
            exchange=env_settings.mutations_exchange_name,
            routing_key=env_settings.mutation_persistent_queue_key,
            body=json.dumps(trade),
            properties=pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent),
        )
        channel.basic_publish(
            exchange=env_settings.trade_updates_exchange_name,
            routing_key="",
            body=json.dumps(trade),
        )
