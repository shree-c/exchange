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
        env_settings.rabbit_mq_hostname,
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
DEPTH = env_settings.bid_ask_depth
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
        "last_added_buy": manager.Value('float', 0),
        "last_added_sell": manager.Value('float', 0)
    }
    trade_publish_queue = manager.Queue(maxsize=-1)
    mutation_lock = Lock()
    accumulator_p1 = Process(
        target=accumulator,
        args=(shared_memory, manager, mutation_lock),
    )
    accumulator_p2 = Process(
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
    accumulator_p1.start()
    accumulator_p2.start()
    matching_engine.start()
    bid_ask_broadcaster.start()
    trade_broadcaster.start()
    accumulator_p1.join()
    accumulator_p2.join()
    matching_engine.join()
    bid_ask_broadcaster.join()
    trade_broadcaster.join()
