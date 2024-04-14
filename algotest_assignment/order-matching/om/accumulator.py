from om.env import env_settings
from datetime import datetime
import json
import pika
from om.utils.priority_queue import PQManager
import traceback


def create_order(body, order_book, manager):
    body["punched"] = 0
    body["cancelled"] = False
    body["timestamp"] = datetime.now().timestamp()
    ord = manager.dict()
    ord.update(body)
    order_book[body["order_id"]] = ord
    return [True, ord]


def append_list(price_table, order, manager):
    if not order["price"] in price_table:
        price_table[order["price"]] = manager.deque()
    price_table[order["price"]].append(order)


def update_order(body, order_book, mutation_lock):
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
                    else:
                        order["price"] = body["price"]
                    return [True, order]
        else:
            return [False, "Couldn't find order"]


def cancel_order(body, order_book, mutation_lock):
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
                    order["cancelled"] = True
                return [True, order]
        else:
            return [False, "Couldn't find order"]


def accumulator(shared_memory, manager, mutation_lock):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            env_settings.rabbit_mq_hostname,
        )
    )
    try:
        channel = connection.channel()
        buy_pq = PQManager(
            shared_memory["price_active_set_buy"],
            shared_memory["price_priority_queue_buy"],
            shared_memory["last_added_buy"],
            -1,
        )
        sell_pq = PQManager(
            shared_memory["price_active_set_sell"],
            shared_memory["price_priority_queue_sell"],
            shared_memory["last_added_sell"],
            1,
        )
        channel.exchange_declare(
            exchange=env_settings.mutations_exchange_name,
            exchange_type="fanout",
            durable=True,
        )
        def cb(ch, method, props, body):
            body_parsed = json.loads(body.decode())
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
                    [status, data] = create_order(
                        body_parsed, shared_memory["order_book"], manager
                    )
                    channel.basic_publish(
                        exchange=env_settings.mutations_exchange_name,
                        routing_key="",
                        body=json.dumps(
                            {
                                "success": status,
                                "message": (
                                    f"Order created successfully for {data['order_id']}"
                                    if status
                                    else data
                                ),
                                "body": (
                                    None
                                    if not status
                                    else {"type": "create", "data": data._getvalue()}
                                ),
                            }
                        ),
                    )
                    if status:
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
                elif body_parsed["action"] == "update":
                    [status, data] = update_order(
                        body_parsed,
                        shared_memory["order_book"],
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
                                "body": (
                                    None
                                    if not status
                                    else {"type": "update", "data": data._getvalue()}
                                ),
                            }
                        ),
                    )
                    if status:
                        if data["side"] == 1:
                            append_list(
                                shared_memory["price_table_buy"],
                                shared_memory["order_book"][data["order_id"]],
                                manager,
                            )
                            buy_pq.put(data["price"])
                        else:
                            append_list(
                                shared_memory["price_table_sell"],
                                shared_memory["order_book"][data["order_id"]],
                                manager,
                            )
                            sell_pq.put(data["price"])

                elif body_parsed["action"] == "cancel":
                    [status, data] = cancel_order(
                        body_parsed,
                        shared_memory["order_book"],
                        mutation_lock,
                    )
                    channel.basic_publish(
                        exchange=env_settings.mutations_exchange_name,
                        routing_key="",
                        body=json.dumps(
                            {
                                "success": status,
                                "message": (
                                    f"Order cancelled successfully for {data['order_id']}"
                                    if status
                                    else data
                                ),
                                "body": (
                                    None
                                    if not status
                                    else {"type": "cancel", "data": data._getvalue()}
                                ),
                            }
                        ),
                    )
                else:
                    print("action not implemented")
            else:
                print("No action attr")
            ch.basic_ack(delivery_tag=method.delivery_tag)

        print("START")
        channel.basic_consume(
            env_settings.accumulator_queue_key, on_message_callback=cb
        )
        channel.start_consuming()
        print("Ended consuming")
    except Exception as e:
        print(traceback.format_exc())
        print(e)
    finally:
        connection.close()
