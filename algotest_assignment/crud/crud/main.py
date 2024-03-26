from datetime import datetime
from redis import Redis
from datetime import datetime
from crud.env import env_settings
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
        # Inconsistent
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
    SCALE_FACTOR = 1e5

    def __init__(self, r: Redis) -> None:
        self.r = r
        pass

    def redis_order_book_key():
        return f"{env_settings.crud_order_book_prefix}{datetime.now().strftime('%Y-%m-%d')}"

    def redis_order_matching_queue_key(side):
        if side == 1:
            return f"{env_settings.crud_order_match_queue_prefix}_buys_{datetime.now().strftime('%Y_%m_%d')}"
        return f"{env_settings.crud_order_match_queue_prefix}_sells_{datetime.now().strftime('%Y_%m_%d')}"

    def redis_order_list_passive_key():
        return f"{env_settings.crud_order_id_list_prefix}_{datetime.now().strftime('%Y_%m_%d')}"

    def split_order_value(order_string):
        [timestamp, side, quantity, price, punched, cancelled] = order_string.split("|")
        return {
            "timestamp": float(timestamp),
            "side": int(side),
            "quantity": int(quantity),
            "price": float(price),
            "punched": int(punched),
            "cancelled": int(cancelled),
        }

    def make_order_book_value_string(order):
        return f"{order['timestamp']}|{order['side']}|{order['quantity']}|{order['price']}|{order['punched']}|{order['cancelled']}"

    def get_score(price, timestamp, side):
        price_scaled = price * OrderCRUD.SCALE_FACTOR
        return round(price_scaled - round(timestamp)) * side * -1

    @dow
    def create(self, order):
        order_id = str(uuid.uuid4())
        timestamp = datetime.now().timestamp()
        order["timestamp"] = timestamp
        order["order_id"] = order_id
        order["punched"] = 0
        order["cancelled"] = 0
        # into order book
        self.r.hset(
            OrderCRUD.redis_order_book_key(),
            str(order_id),
            OrderCRUD.make_order_book_value_string(order),
        )
        score = OrderCRUD.get_score(order["price"], order["timestamp"], order["side"])
        # into
        res = self.r.zadd(
            OrderCRUD.redis_order_matching_queue_key(order["side"]),
            {str(order_id): score},
        )
        if res == 0:
            return [False, "Couldn't add to order match queue"]
        # for maintaining list of order ids by timestamp
        # right to left: new to old
        self.r.rpush(OrderCRUD.redis_order_list_passive_key(), str(order_id))
        return [True, order_id]

    @dow
    def pop_top_buy(self):
        res = self.r.zpopmin(OrderCRUD.redis_order_matching_queue_key(1))
        if len(res) == 0:
            return [False, "No buys available"]
        return [True, (res[0][0].decode(), res[0][1])]

    @dow
    def pop_top_sell(self):
        res = self.r.zpopmin(OrderCRUD.redis_order_matching_queue_key(-1))
        if len(res) == 0:
            return [False, "No sells available"]
        return [True, (res[0][0].decode(), res[0][1])]

    @dow
    def push_to_sell_match_queue(self, order_id, score):
        res = self.r.zadd(
            OrderCRUD.redis_order_matching_queue_key(-1), {order_id: score}
        )
        if res == 1:
            return [True, None]
        return [False, "Couldn't push to sell match queue"]

    @dow
    def push_to_buy_match_queue(self, order_id, score):
        res = self.r.zadd(
            OrderCRUD.redis_order_matching_queue_key(1), {order_id: score}
        )
        if res == 1:
            return [True, None]
        return [False, "Couldn't push to buy match queue"]

    @dow
    def update_punched(self, order_id, punched):
        [status, data] = self.get(order_id)
        if status:
            data["punched"] = punched
            self.r.hset(
                OrderCRUD.redis_order_book_key(),
                order_id,
                OrderCRUD.make_order_book_value_string(data),
            )
            return [True, None]
        return [False, data]

    # To handle race conditions for delete(cancel) and update.
    # If the order is updatable:
    #     Remove from order match list
    #     Update the order
    @dow
    def update(self, order_id, updated_price, updated_quantity):
        order_string = self.r.hget(OrderCRUD.redis_order_book_key(), str(order_id))
        if not order_string:
            return [False, "Order not found"]
        existing_order = OrderCRUD.split_order_value(order_string.decode())
        if existing_order["cancelled"] == 1:
            return [False, "Order already cancelled"]
        if existing_order["punched"] != 0:
            if existing_order["punched"] != existing_order["quantity"]:
                return [False, "Order is pending, you can't modify it"]
            else:
                return [False, "Order is filled, you can't modify it"]

        # popping from order match list
        res = self.r.zrem(
            OrderCRUD.redis_order_matching_queue_key(int(existing_order["side"])),
            str(order_id),
        )
        # if it's not in match list it's considered as being processed, it would be either in order process queue or match list
        if res == 0:
            return [False, "Order is being processed"]
        existing_order["price"] = updated_price
        existing_order["quantity"] = updated_quantity
        # updating order book
        self.r.hset(
            OrderCRUD.redis_order_book_key(),
            str(order_id),
            OrderCRUD.make_order_book_value_string(existing_order),
        )
        # pushing it back
        print("pushing it back to order m queue")
        return self.push_to_om_queue(str(order_id))

    @dow
    def delete(self, order_id):
        [status, order] = self.get(order_id)
        if not status:
            return [False, "Order not found"]
        if order["cancelled"] == 1:
            return [False, "Order already cancelled"]
        if order["punched"] != 0:
            return [False, "Order is pending, you can't modify it"]
        # popping from order match list
        res = self.r.zrem(
            OrderCRUD.redis_order_matching_queue_key(int(order["side"])),
            str(order_id),
        )
        # if it's not in match list it's considered as being processed, it would be either in order process queue or match list
        if res == 0:
            self.push_to_om_queue(str(order_id))
            return [False, "Order is being processed"]
        order["cancelled"] = 1
        self.r.hset(
            OrderCRUD.redis_order_book_key(),
            str(order_id),
            OrderCRUD.make_order_book_value_string(order),
        )
        # not pushing it back
        return [True, None]

    @dow
    def get(self, order_id):
        order_value = self.r.hget(OrderCRUD.redis_order_book_key(), order_id)
        if order_value:
            return [True, OrderCRUD.split_order_value(order_value.decode())]
        return [False, "Order doesn't exist"]

    @dow
    def get_all(self, limit, offset):
        # get all orders
        order_ids = self.r.lrange(
            OrderCRUD.redis_order_list_passive_key(), offset, offset + limit - 1
        )
        if len(order_ids) == 0:
            return [True, []]
        return self.get_these_orders(order_ids)

    @dow
    def get_these_orders(self, order_ids):
        orders = []
        order_book_value_strings = self.r.hmget(
            OrderCRUD.redis_order_book_key(), order_ids
        )
        for index, order_id in enumerate(order_ids):
            if order_book_value_strings[index]:
                orders.append(
                    {
                        "order_id": order_id,
                        **OrderCRUD.split_order_value(
                            order_book_value_strings[index].decode()
                        ),
                    }
                )
        return [
            True,
            orders,
        ]

    @dow
    def push_to_om_queue(self, order_id):
        [status, data] = self.get(order_id)
        if not status:
            return [status, data]
        score = OrderCRUD.get_score(data["price"], data["timestamp"], data["side"])
        res = self.r.zadd(
            OrderCRUD.redis_order_matching_queue_key(data["side"]),
            {order_id: score},
        )
        if res == 0:
            return [False, "Couldn't add order_id"]
        return [True, None]

    @dow
    def calculate_depth(self, depth, key):
        price_quantity = {}
        index = 0
        while True:
            card = self.r.zcard(key)
            # index is greater than cardinality
            if card == index or card == 0:
                break
            order_id = self.r.zrange(key, index, index)[0]
            [status, data] = self.get(order_id.decode())
            if not status:
                continue
            if data:
                price = data["price"]
                if len(price_quantity) == depth and str(price) not in price_quantity:
                    break
                quantity = data["quantity"] - data["punched"]
                if str(price) not in price_quantity:
                    price_quantity[str(price)] = quantity
                else:
                    price_quantity[str(price)] += quantity
                index += 1
        return [True, price_quantity]

    @dow
    def calculate_depth_buy(self, depth):
        return self.calculate_depth(depth, OrderCRUD.redis_order_matching_queue_key(1))

    @dow
    def calculate_depth_sell(self, depth):
        return self.calculate_depth(depth, OrderCRUD.redis_order_matching_queue_key(-1))
