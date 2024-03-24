from csql import Base, OrderCRUD, TradeCRUD
from datetime import datetime
from time import sleep
from redis import Redis
from sqlalchemy import create_engine
import json
from sqlalchemy.orm import sessionmaker

r = Redis(password="shreex")
# engine = create_engine("sqlite:///../orders.db")
# Base.metadata.create_all(engine)
# Session = sessionmaker(bind=engine)
# session = Session()
order_crud = OrderCRUD(r)
trade_crud = TradeCRUD(r)

last_buy_id = ""
last_sell_id = ""
while True:
    print('hie')
    TODAY_BUY_QUEUE = f"sorted_or_buys_{datetime.now().strftime('%Y_%m_%d')}"
    TODAY_SELLS_QUEUE = f"sorted_or_sells_{datetime.now().strftime('%Y_%m_%d')}"
    top_buy_id = r.zrange(TODAY_BUY_QUEUE, 0, 0)
    top_buy_id = "" if len(top_buy_id) == 0 else top_buy_id[0].decode()
    top_sell_id = r.zrange(TODAY_SELLS_QUEUE, 0, 0)
    top_sell_id = "" if len(top_sell_id) == 0 else top_sell_id[0].decode()
    [buy_status, buy_order] = order_crud.get(top_buy_id)
    if not buy_order:
        continue
    [sell_status, sell_order] = order_crud.get(top_sell_id)
    if not sell_order:
        continue

    if buy_order["price"] >= sell_order["price"]:
        total_buy_quantity = buy_order["quantity"] - buy_order["punched"]
        total_sell_quantity = sell_order["quantity"] - sell_order["punched"]
        punched = min([total_buy_quantity, total_sell_quantity])
        buy_remaining = total_buy_quantity - punched
        sell_remaining = total_sell_quantity - punched
        if buy_remaining == 0:
            r.zrem(TODAY_BUY_QUEUE, top_buy_id)
        if sell_remaining == 0:
            r.zrem(TODAY_SELLS_QUEUE, top_sell_id)
        # TODO look into this logic
        price = (
            buy_order["price"]
            if buy_order["timestamp"] > sell_order["timestamp"]
            else sell_order["price"]
        )
        TODAY_LTP = f"ltp_{datetime.now().strftime('%Y_%m_%d')}"
        r.set(TODAY_LTP, price)
        trade_order = {
            "timestamp": datetime.now().timestamp(),
            "buy_order_id": top_buy_id,
            "sell_order_id": top_sell_id,
            "quantity": punched,
            "price": price,
        }
        print(punched, '***************************')
        if punched > 0:
            order_crud.update_punched(top_buy_id, punched + buy_order["punched"])
            order_crud.update_punched(top_sell_id, punched + sell_order["punched"])
            trade_crud.create_trade(trade_order)
            print("created...", trade_order)
    else:
        print("couldn't match any")

    print("*************************")
    print(r.zcard(TODAY_BUY_QUEUE))
    print(r.zcard(TODAY_SELLS_QUEUE))
    print("loop complete...")
    sleep(0.5)
