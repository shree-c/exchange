from multiprocessing import Process, Manager, Lock
from om.bid_ask_spread_broadcast import broadcast_bid_ask, broadcast_trades
from multiprocessing.managers import SyncManager
from om.env import env_settings
from queue import PriorityQueue
from om.accumulator import accumulator
from om.match_engine import match_engine
from collections import deque
import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        "localhost",
    )
)
channel = connection.channel()
channel.exchange_declare(
    exchange=env_settings.trade_updates_exchange_name,
    exchange_type='fanout',
    durable=True
)

channel.exchange_declare(
    exchange=env_settings.bid_ask_exchange,
    exchange_type='fanout',
    durable=True
)
# BID_ASK_QUEUE_CHANNEL_KEY = "bid_ask"
# TRADE_UPDATES_CHANNEL_KEY = "trade_updates"
# STATE_CHANGE_CHANNEL_KEY = "order_book_state_changes"
# ACCUMULATOR_CHANNEL_KEY = "accumulator"
DEPTH = 5

# channel.queue_declare(queue=env_settings.bid_ask_exchange, durable=False)
channel.queue_declare(queue=env_settings.trade_updates_exchange_name, durable=True)
channel.queue_declare(queue=env_settings.state_change_queue_key, durable=True)
channel.queue_declare(queue=env_settings.accumulator_queue_key, durable=True)


class MyManager(SyncManager):
    pass


MyManager.register("priority_queue", PriorityQueue)
MyManager.register("set", set)
MyManager.register("deque", deque)
with MyManager() as manager:
    shared_memory = {
        "order_book": manager.dict(),
        "price_table_buy": manager.dict(),
        "price_table_sell": manager.dict(),
        "price_priority_queue_buy": manager.priority_queue(),
        "price_priority_queue_sell": manager.priority_queue(),
        "price_active_set_buy": manager.set(),
        "price_active_set_sell": manager.set(),
    }
    trade_publish_queue = manager.Queue(maxsize=-1)
    mutation_lock = Lock()
    accumulator_p = Process(
        target=accumulator,
        args=(shared_memory, manager, mutation_lock),
    )
    matching_engine = Process(
        target=match_engine,
        args=(shared_memory, mutation_lock, trade_publish_queue),
    )
    bid_ask_broadcaster = Process(
        target=broadcast_bid_ask,
        args=(
            shared_memory["price_table_buy"],
            shared_memory["price_table_sell"],
            DEPTH,
        ),
    )

    trade_broadcaster = Process(
        target=broadcast_trades,
        args=(trade_publish_queue,),
    )
    accumulator_p.start()
    matching_engine.start()
    bid_ask_broadcaster.start()
    trade_broadcaster.start()
    accumulator_p.join()
    matching_engine.join()
    bid_ask_broadcaster.join()
    trade_broadcaster.join()
