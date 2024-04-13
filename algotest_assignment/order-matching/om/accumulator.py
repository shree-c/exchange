from uuid import uuid4
from om.env import env_settings
from time import sleep
from datetime import datetime
import json
from random import randint
from multiprocessing import Manager
import pika
from om.utils.priority_queue import PQManager

def get_random_order():
    return {
        "order_id": str(uuid4()),
        "quantity": randint(200, 250),
        "timestamp": datetime.now().timestamp(),
        "cancelled": False,
        "pending": 0,
    }


def create_order(body, order_book, manager):
    body["punched"] = 0
    body["cancelled"] = False
    body["timestamp"] = datetime.now().timestamp()
    ord = manager.dict()
    ord.update(body)
    order_book[body["order_id"]] = ord
    return ord


def append_list(price_table, order, manager):
    if not order["price"] in price_table:
        price_table[order["price"]] = manager.deque()
    price_table[order["price"]].append(order)


def update_order(
    body, order_book, price_table_buy, price_table_sell, manager, mutation_lock
):
    with mutation_lock:
        order_id = body["order_id"]
        if order_id in order_book:
            order = order_book[order_id]
            if order["cancelled"]:
                return [False, "Cancelled"]
            else:
                if order["punched"] != 0:
                    return [False, "Order partially executed. You cant modify it"]
                else:
                    if order["side"] == 1:
                        order["price"] = body["price"]
                        append_list(price_table_buy, order, manager)
                    else:
                        order["price"] = body["price"]
                        append_list(price_table_sell, order, manager)
                    return [True, body]
        else:
            return [False, "Couldn't find order"]


def cancel_order(
    body, order_book, price_table_buy, price_table_sell, mutation_lock, ord
):
    with mutation_lock:
        order_id = body["order_id"]
        print(order_book, order_id, "printing inside babe", order_book[order_id])
        if order_id in order_book:
            order = order_book[order_id]
            print("BIG CHECK...", ord == order)
            if order["cancelled"]:
                return [False, "Cancelled"]
            else:
                if order["punched"] != 0:
                    return [False, "Order partially executed. You cant modify it"]
                else:
                    order["cancelled"] = True
                    if order["side"] == 1:
                        price_table_buy[order["price"]].remove(order)
                    else:
                        for item in price_table_sell[order["price"]]:
                            print("SINGLE ORDER IN QUEUE", item, item == order, order)
                        price_table_sell[order["price"]].remove(order)
                        print(price_table_sell)
                        print("**************SUCCESS*****************")
                    return [True, None]
        else:
            return [False, "Couldn't find order"]


def accumulator(shared_memory, manager, mutation_lock):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            "localhost",
        )
    )
    try:
        channel = connection.channel()
        buy_pq = PQManager(
            shared_memory["price_active_set_buy"],
            shared_memory["price_priority_queue_buy"],
            -1,
        )
        sell_pq = PQManager(
            shared_memory["price_active_set_sell"],
            shared_memory["price_priority_queue_sell"],
            1,
        )
        channel.exchange_declare(exchange=env_settings.mutations_exchange_name, exchange_type="fanout", durable=True)

        def cb(ch, method, props, body):
            body_parsed = json.loads(body.decode())
            # print("-----------------------------")
            # print(body_parsed)
            # print("-----------------------------")
            if "action" in body_parsed:
                channel.basic_publish(
                    exchange="",
                    routing_key=env_settings.state_change_queue_key,
                    body=body.decode(),
                    properties=pika.BasicProperties(
                        delivery_mode=pika.DeliveryMode.Persistent
                    ),
                )
                if body_parsed["action"] == "create":
                    body_parsed.pop("action")
                    created_order = create_order(
                        body_parsed, shared_memory["order_book"], manager
                    )
                    channel.basic_publish(
                        exchange=env_settings.mutations_exchange_name,
                        routing_key="",
                        body=json.dumps(
                            {
                                "success": True,
                                "message": "Order placed for " + created_order["order_id"],
                                "body": created_order._getvalue(),
                            }
                        ),
                    )
                    if body_parsed["side"] == 1:
                        append_list(
                            shared_memory["price_table_buy"],
                            shared_memory["order_book"][body_parsed["order_id"]],
                            manager,
                        )
                        buy_pq.put(body_parsed["price"])
                    else:
                        append_list(
                            shared_memory["price_table_sell"],
                            shared_memory["order_book"][body_parsed["order_id"]],
                            manager,
                        )
                        sell_pq.put(body_parsed["price"])
                # TODO update and cancel function should return status
                # PUBLISH it to state changes queue
                elif body_parsed["action"] == "update":
                    [status, data] = update_order(
                        body_parsed,
                        shared_memory["order_book"],
                        shared_memory["price_table_buy"],
                        shared_memory["price_table_sell"],
                        manager,
                        mutation_lock,
                    )
                    channel.basic_publish(
                        exchange=env_settings.mutations_exchange_name,
                        routing_key="",
                        body=json.dumps(
                            {
                                "success": status,
                                "message": (
                                    f"Order updated successfully for {data['order_id']}"
                                    if status
                                    else data
                                ),
                                "body": None if not status else data,
                            }
                        ),
                    )
                elif body_parsed["action"] == "cancel":
                    [status, data] = cancel_order(
                        body_parsed,
                        shared_memory["order_book"],
                        shared_memory["price_table_buy"],
                        shared_memory["price_table_sell"],
                        mutation_lock,
                    )
                    channel.basic_publish(
                        exchange=env_settings.mutations_exchange_name,
                        routing_key="",
                        body=json.dumps(
                            {
                                "success": status,
                                "message": (
                                    f"Order updated successfully for {data['order_id']}"
                                    if status
                                    else data
                                ),
                                "body": None if not status else data,
                            }
                        ),
                    )


                else:
                    print("action not implemented")
            else:
                print("No action attr")
            ch.basic_ack(delivery_tag=method.delivery_tag)

        print("START")
        channel.basic_consume(env_settings.accumulator_queue_key, on_message_callback=cb)
        channel.start_consuming()
        print("Ended consuming")
    except Exception as e:
        print("ACCUMULATOR ERROR !!!!")
        print(e)
    finally:
        connection.close()