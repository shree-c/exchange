from csql.models.db import Order, Trade
from datetime import datetime
from redis import Redis
from datetime import datetime
import uuid


class TradeCRUD:
    def __init__(self, r: Redis) -> None:
        self.r = r
        pass

    # def create(self, trade) -> uuid.UUID:
    #     new_trade = Trade(
    #         timestamp=datetime.now().timestamp(),
    #         buy_order_id=uuid.UUID(trade["buy_order_id"]),
    #         sell_order_id=uuid.UUID(trade["sell_order_id"]),
    #         quantity=trade["quantity"],
    #         price=trade["price"],
    #     )
    #     self.session.add(new_trade)
    #     self.session.commit()
    #     return new_trade.trade_id

    # def get(self, trade_id) -> uuid.UUID:
    #     return self.session.query(Trade).get(uuid.UUID(trade_id))

    # def get_all(self, limit, offset):
    #     return self.session.query(Trade).offset(offset).limit(limit).all()

    def redis_trade_book_key():
        return f"trade_book_{datetime.now().strftime('%Y-%m-%d')}"

    def redis_trade_id_list_key():
        return f"trade_id_list{datetime.now().strftime('%Y-%m-%d')}"

    def redis_trade_id_consumption_list():
        return f"trade_id_consumption_list{datetime.now().strftime('%Y-%m-%d')}"

    def make_trade_value_string(trade):
        return f"{trade['timestamp']}|{trade['buy_order_id']}|{trade['sell_order_id']}|{trade['price']}|{trade['quantity']}"

    def split_trade_value(trade_value):
        # TODO
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

    def create_trade(self, trade):
        # Inconsistent
        trade_id = str(uuid.uuid4())
        self.r.hset(
            TradeCRUD.redis_trade_book_key(),
            trade_id,
            TradeCRUD.make_trade_value_string(trade),
        )
        self.r.lpush(TradeCRUD.redis_trade_id_list_key(), trade_id)
        self.r.lpush(TradeCRUD.redis_trade_id_consumption_list(), trade_id)
        return [True, None]

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

    def get_all(self, limit, offset):
        try:
            trade_ids = self.r.lrange(
                TradeCRUD.redis_trade_id_list_key(), offset, offset + limit - 1
            )
            if len(trade_ids) == 0:
                return [True, []]
            return self.get_these_trades(trade_ids)
        except Exception as e:
            print(e)
            return [False, f"INTERNAL-{str(e)}"]

    def get_new_trades(self, max=50):
        length = self.r.llen(TradeCRUD.redis_trade_id_consumption_list())
        trade_ids = self.r.rpop(
            TradeCRUD.redis_trade_id_consumption_list(), min(length, max)
        )
        if not trade_ids:
            return [True, []]
        return self.get_these_trades(trade_ids)


# TODO: wrap all these in trycatch block
class OrderCRUD:
    def __init__(self, r: Redis) -> None:
        self.r = r
        pass

    def redis_order_book_key():
        return f"order_book_{datetime.now().strftime('%Y-%m-%d')}"

    def redis_process_queue_key():
        return f"order_process_queue_{datetime.now().strftime('%Y-%m-%d')}"

    def redis_order_matching_queue_key(side):
        if side == 1:
            return f"sorted_or_buys_{datetime.now().strftime('%Y_%m_%d')}"
        return f"sorted_or_sells_{datetime.now().strftime('%Y_%m_%d')}"

    def redis_process_queue_score_key():
        return f"order_process_queue_score_{datetime.now().strftime('%Y_%m_%d')}"

    def redis_order_list_passive_key():
        return f"order_list_{datetime.now().strftime('%Y_%m_%d')}"

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

    def create(self, order):
        try:
            print(order.model_dump())
            order_id = uuid.uuid4()
            order_string = f"{datetime.now().timestamp()}|{order.side}|{order.quantity}|{order.price}|0|0"
            print(order_string)
            self.r.hset(OrderCRUD.redis_order_book_key(), str(order_id), order_string)
            self.r.rpush(OrderCRUD.redis_process_queue_key(), str(order_id))
            self.r.lpush(OrderCRUD.redis_order_list_passive_key(), str(order_id))
            return [True, None]
        except Exception as e:
            print(e)
            return [False, f"INTERNAL-x"]

    def delete(self, order_id):
        try:
            [status, order] = self.get(order_id)
            print(order)
            if not status:
                return [False, "Order not found"]
            if order["cancelled"] == 1:
                return [False, "Order already cancelled"]
            if order["punched"] != 0:
                return [False, "Order is pending, you can't modify it"]
            res = self.r.zrem(
                OrderCRUD.redis_order_matching_queue_key(int(order["side"])),
                str(order_id),
            )
            print("popped from matching queue")
            if res == 0:
                return [False, "Order is being processed"]
            order['cancelled'] = 1
            self.r.hset(
                OrderCRUD.redis_order_book_key(),
                str(order_id),
                OrderCRUD.make_order_book_value_string(order)
            )
            print("set")
            self.r.rpush(OrderCRUD.redis_process_queue_key(), order_id)
            return [True, None]
        except Exception as e:
            print(e)
            return [False, f"INTERNAL-{str(e)}"]

    def update_punched(self, order_id, punched):
        [status, order] = self.get(order_id)
        if status:
            order["punched"] = punched
            self.r.hset(
                OrderCRUD.redis_order_book_key(),
                order_id,
                OrderCRUD.make_order_book_value_string(order),
            )
            return [True, None]
        return [False, None]

    # TODO synchronization
    def update(self, order_id, updated_price, updated_quantity):
        try:
            print("start")
            order_string = self.r.hget(OrderCRUD.redis_order_book_key(), str(order_id))
            print("got order_string")
            if not order_string:
                return [False, "Order not found"]
            print("splitting")
            existing_order = OrderCRUD.split_order_value(order_string.decode())

            print("fetched order", existing_order)
            if existing_order["cancelled"] == 1:
                return [False, "Order already cancelled"]
            if existing_order["punched"] != 0:
                return [False, "Order is pending, you can't modify it"]
            res = self.r.zrem(
                OrderCRUD.redis_order_matching_queue_key(int(existing_order["side"])),
                str(order_id),
            )
            if res == 0:
                return [False, "Order is being processed"]
            existing_order["price"] = updated_price
            existing_order["quantity"] = updated_quantity
            print("setting")
            self.r.hset(
                OrderCRUD.redis_order_book_key(),
                str(order_id),
                OrderCRUD.make_order_book_value_string(existing_order),
            )
            print("set")
            self.r.rpush(OrderCRUD.redis_process_queue_key(), str(order_id))
            print("queued")
            return [True, None]
        except Exception as e:
            print(e)
            return [False, f"INTERNAL-{str(e)}"]

    def get(self, order_id):
        try:
            order_value = self.r.hget(OrderCRUD.redis_order_book_key(), order_id)
            if order_value:
                return [True, OrderCRUD.split_order_value(order_value.decode())]
            return [True, None]
        except Exception as e:
            return [False, f"INTERNAL-{str(e)}"]

    def get_all(self, limit, offset):
        try:
            order_ids = self.r.lrange(
                OrderCRUD.redis_order_list_passive_key(), offset, offset + limit - 1
            )
            if len(order_ids) == 0:
                return [True, []]
            return self.get_these_orders(order_ids)
        except Exception as e:
            print(e)
            return [False, f"INTERNAL-{str(e)}"]

    def get_all_queued_orders(self, max=1000):
        orders = [
            item.decode()
            for item in reversed(
                self.r.lrange(OrderCRUD.redis_process_queue_key(), 0, 10000)
            )
        ]
        return [True, orders]

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

    def delete_from_order_process_queue(self, count):
        self.r.lpop(OrderCRUD.redis_process_queue_key(), count)
        return [True, None]


# class OrderCRUD:
#     def __init__(self, session) -> None:
#         self.session = session
#         pass

#     def create(self, order) -> uuid.UUID:
#         new_order = Order(
#             timestamp=datetime.now().timestamp(),
#             side=order["side"],
#             quantity=order["quantity"],
#             price=order["price"],
#         )
#         self.session.add(new_order)
#         self.session.commit()
#         return new_order.order_id

#     def delete(self, order_id):
#         order_to_delete = self.session.query(Order).get(uuid.UUID(order_id))
#         if order_to_delete:
#             self.session.delete(order_to_delete)
#             self.session.commit()

#     def update(self, order_id, quantity, price):
#         order_to_update = self.session.query(Order).get(uuid.UUID(order_id))
#         setattr(order_to_update, "quantity", quantity)
#         setattr(order_to_update, "price", price)
#         setattr(order_to_update, "accepted", 0)
#         self.session.commit()

#     def update_punched(self, order_id, punched):
#         order_to_update = self.session.query(Order).get(uuid.UUID(order_id))
#         setattr(order_to_update, "punched", punched)
#         self.session.commit()

#     def get_all(self, limit, offset):
#         return self.session.query(Order).offset(offset).limit(limit).all()

#     def get(self, order_id):
#         return self.session.query(Order).get(uuid.UUID(order_id))

#     def get_new_orders(self):
#         return self.session.query(Order).filter_by(accepted=False).all()

#     def mark_orders_accepted(self, order_ids):
#         self.session.query(Order).filter(
#             Order.order_id.in_(map(lambda x: uuid.UUID(x), order_ids))
#         ).update({"accepted": True}, synchronize_session=False)
#         self.session.commit()

#     def get_orders(self, order_ids):
#         return (
#             self.session.query(Order)
#             .filter(Order.order_id.in_(map(lambda x: uuid.UUID(x), order_ids)))
#             .all()
#         )
