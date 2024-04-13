from datetime import datetime
import traceback
import pika.channel
from redis import Redis
import sqlite3
from datetime import datetime
from crud.env import env_settings
import pika
import json
import uuid


def dow(func):
    """
    Database operations wrapper
    """
    def wrapper(*args, **kwargs):
        try:
            x = func(*args, **kwargs)
            return x
        except Exception as e:
            print(traceback.format_exc())
            return [False, f"INTERNAL-{str(e)}"]

    return wrapper


class TradeCRUD:
    def __init__(self, r: Redis) -> None:
        self.r = r
        pass

    def redis_trade_book_key():
        return f"{env_settings.crud_trade_book_prefix}{datetime.now().strftime('%Y-%m-%d')}"

    def redis_trade_id_list_key():
        return f"{env_settings.crud_trade_id_list_prefix}{datetime.now().strftime('%Y-%m-%d')}"

    def make_trade_value_string(trade):
        return f"{trade['timestamp']}|{trade['buy_order_id']}|{trade['sell_order_id']}|{trade['price']}|{trade['quantity']}"

    def split_trade_value(trade_value):
        [timestamp, buy_order_id, sell_order_id, price, quantity] = trade_value.split(
            "|"
        )
        return {
            "timestamp": float(timestamp),
            "sell_order_id": sell_order_id,
            "buy_order_id": buy_order_id,
            "price": float(price),
            "quantity": int(quantity),
        }

    @dow
    def create_trade(self, trade):
        trade_id = str(uuid.uuid4())
        self.r.hset(
            TradeCRUD.redis_trade_book_key(),
            trade_id,
            TradeCRUD.make_trade_value_string(trade),
        )
        self.r.lpush(TradeCRUD.redis_trade_id_list_key(), trade_id)
        trade["trade_id"] = trade_id
        self.r.publish(env_settings.trade_channel_name, json.dumps(trade))
        print("published trade ...")
        return [True, None]

    @dow
    def get_these_trades(self, trade_ids):
        trades = self.r.hmget(TradeCRUD.redis_trade_book_key(), trade_ids)
        trades_collection = []
        for index, trade in enumerate(trades):
            trades_collection.append(
                {
                    "trade_id": trade_ids[index].decode(),
                    **TradeCRUD.split_trade_value(trade.decode()),
                }
            )
        return [True, trades_collection]

    @dow
    def get_all(self, limit, offset):
        trade_ids = self.r.lrange(
            TradeCRUD.redis_trade_id_list_key(), offset, offset + limit - 1
        )
        if len(trade_ids) == 0:
            return [True, []]
        return self.get_these_trades(trade_ids)

    @dow
    def get_new_trades(self, max=50):
        length = self.r.llen(TradeCRUD.redis_trade_id_consumption_list())
        trade_ids = self.r.rpop(
            TradeCRUD.redis_trade_id_consumption_list(), min(length, max)
        )
        if not trade_ids:
            return [True, []]
        return self.get_these_trades(trade_ids)


class OrderCRUD:
    SCALE_FACTOR = 1e8

    def __init__(self, rabbit_channel: pika.channel.Channel) -> None:
        self.persistent_db_con: sqlite3.Connection = sqlite3.connect(
            env_settings.state_change_log_db
        )
        self.persistent_db_cursor: sqlite3.Cursor = self.persistent_db_con.cursor()
        self.persistent_db_cursor.execute(
            "CREATE TABLE IF NOT EXISTS STATE_CHANGES (message_id INTEGER PRIMARY KEY, order_id TEXT, order_data TEXT)"
        )
        self.persistent_db_cursor.execute(
            "CREATE TABLE IF NOT EXISTS ORDER_BOOK (order_id TEXT PRIMARY KEY, side INTEGER, price FLOAT, timestamp FLOAT, punched INTEGER, quantity INTEGER, cancelled BOOL)"
        )
        self.persistent_db_con.commit()
        self.channel = rabbit_channel
        pass

    @dow
    def update_punched(self, order_id, punched_quantity, timestamp):
        self.persistent_db_cursor.execute(
            f"UPDATE ORDER_BOOK SET punched = punched + {punched_quantity}, timestamp = {timestamp} where order_id = '{order_id}'"
        )
        self.persistent_db_con.commit()
        return [True, None]

    @dow
    def update_order(self, order_id, price, timestamp, cancelled):
        self.persistent_db_cursor.execute(
            f"UPDATE ORDER_BOOK SET price = {price}, timestamp = {timestamp}, cancelled={cancelled} where  order_id = '{order_id}'"
        )
        self.persistent_db_con.commit()
        return [True, None]

    @dow
    def save_order(self, order):
        self.persistent_db_cursor.execute(
            f"INSERT INTO ORDER_BOOK (order_id, side, price, timestamp, punched, quantity, cancelled) values('{order['order_id']}', {order['side']}, {order['price']}, {order['timestamp']}, {order['punched']}, {order['quantity']}, {order['cancelled']})"
        )
        self.persistent_db_con.commit()
        return [True, None]

    @dow
    def log_state_change(self, change):
        cursor = self.persistent_db_cursor.execute(
            f"INSERT INTO STATE_CHANGES (order_id, order_data) values('{str(change['order_id'])}', '{json.dumps(change)}')"
        )
        self.persistent_db_con.commit()
        return [True, cursor.lastrowid]

    @dow
    def create(self, order):
        order["action"] = "create"
        order["order_id"] = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange="",
            routing_key=env_settings.accumulator_queue_key,
            body=json.dumps(order),
            properties=pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent),
        )
        return [True, order["order_id"]]

    @dow
    def update(self, order_id, price):
        self.channel.basic_publish(
            exchange="",
            routing_key=env_settings.accumulator_queue_key,
            body=json.dumps({"action": "update", "order_id": order_id, "price": price}),
            properties=pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent),
        )
        return [True, None]

    @dow
    def delete(self, order_id):
        self.channel.basic_publish(
            exchange="",
            routing_key=env_settings.accumulator_queue_key,
            body=json.dumps(
                {
                    "action": "cancel",
                    "order_id": order_id,
                }
            ),
            properties=pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent),
        )
        return [True, None]

    @dow
    def get(self, order_id):
        result = self.persistent_db_cursor.execute(
            f"SELECT * FROM ORDER_BOOK WHERE order_id = {order_id}"
        )
        print(result)
        return [True, result]

    def serialize_order_tuple(o_tuple):
        order = dict(
            zip(
                [
                    "order_id",
                    "side",
                    "price",
                    "timestamp",
                    "punched",
                    "quantity",
                    "cancelled",
                ],
                o_tuple,
            )
        )
        return order

    @dow
    def get_all(self, limit, offset):
        result = self.persistent_db_cursor.execute(
            f"SELECT * FROM ORDER_BOOK LIMIT {limit} OFFSET {offset}"
        ).fetchall()
        orders = [
            OrderCRUD.serialize_order_tuple(order_tuple) for order_tuple in result
        ]
        return [True, orders]
