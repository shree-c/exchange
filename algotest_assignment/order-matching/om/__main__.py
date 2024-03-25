from crud import OrderCRUD, TradeCRUD
from datetime import datetime
from time import sleep
from redis import Redis
from om.env import env_settings

r = Redis(host=env_settings.redis_host, password=env_settings.redis_password)
order_crud = OrderCRUD(r)
trade_crud = TradeCRUD(r)

last_buy_id = ""
last_sell_id = ""
while True:
    [status, top_buy_data] = order_crud.pop_top_buy()
    if not status:
        print(top_buy_data, "no buy data")
        if type(top_buy_data) == tuple:
            order_crud.push_to_buy_match_queue(top_buy_data[0], top_buy_data[1])
        sleep(0.5)
        continue
    top_buy_id = top_buy_data[0]

    [status, top_sell_data] = order_crud.pop_top_sell()
    if not status:
        print(top_sell_data)
        if type(top_sell_data) == tuple:
            order_crud.push_to_sell_match_queue(top_sell_data[0], top_sell_data[1])
        if type(top_buy_data) == tuple:
            order_crud.push_to_buy_match_queue(top_buy_data[0], top_buy_data[1])
        sleep(0.5)
        continue
    top_sell_id = top_sell_data[0]

    [buy_status, buy_order] = order_crud.get(top_buy_id)
    if not buy_status or not buy_order:
        print("Couldn't get order details for ", top_buy_id)
        sleep(0.5)
        continue
    [sell_status, sell_order] = order_crud.get(top_sell_id)
    if not sell_status or not sell_order:
        print("Couldn't get order details for ", top_sell_id)
        sleep(0.5)
        continue

    if buy_order["price"] >= sell_order["price"]:
        total_buy_quantity = buy_order["quantity"] - buy_order["punched"]
        total_sell_quantity = sell_order["quantity"] - sell_order["punched"]
        punched = min([total_buy_quantity, total_sell_quantity])
        buy_remaining = total_buy_quantity - punched
        sell_remaining = total_sell_quantity - punched
        price = (
            buy_order["price"]
            if buy_order["timestamp"] > sell_order["timestamp"]
            else sell_order["price"]
        )
        trade_order = {
            "timestamp": datetime.now().timestamp(),
            "buy_order_id": top_buy_id,
            "sell_order_id": top_sell_id,
            "quantity": punched,
            "price": price,
        }
        if punched > 0:
            order_crud.update_punched(top_buy_id, punched + buy_order["punched"])
            order_crud.update_punched(top_sell_id, punched + sell_order["punched"])
            trade_crud.create_trade(trade_order)

        if buy_remaining != 0:
            [status, data] = order_crud.push_to_buy_match_queue(
                top_buy_id, top_buy_data[1]
            )
            if not status:
                print(f"couldn't push {top_buy_id} to order match queue")
        if sell_remaining != 0:
            [status, data] = order_crud.push_to_sell_match_queue(
                top_sell_id, top_sell_data[1]
            )
            if not status:
                print(f"couldn't push {top_sell_id} to order match queue")
    else:
        if type(top_sell_data) == tuple:
            order_crud.push_to_sell_match_queue(top_sell_data[0], top_sell_data[1])
        if type(top_buy_data) == tuple:
            order_crud.push_to_buy_match_queue(top_buy_data[0], top_buy_data[1])
    print("next loop...")
    sleep(env_settings.order_matching_interval)
