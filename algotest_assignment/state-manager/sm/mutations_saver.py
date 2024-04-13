import pika
from sm.env import env_settings
import json
from crud import OrderCRUD


def save_mutations():
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    try:
        order_crud = OrderCRUD(None)
        channel = connection.channel()
        channel.exchange_declare(
            exchange=env_settings.mutations_exchange_name,
            exchange_type="fanout",
            durable=True,
        )
        channel.queue_declare(
            queue=env_settings.mutation_persistent_queue_key, durable=True
        )
        channel.queue_bind(
            queue=env_settings.mutation_persistent_queue_key,
            exchange=env_settings.mutations_exchange_name,
        )

        def cb(ch, method, props, body):
            # order_crud.save_order(body.decode())
            body_parsed = json.loads(body.decode())
            # try to update order based on punched trades
            if "action" in body_parsed:
                if body_parsed["action"] == "trade":
                    order_crud.update_punched(
                        body_parsed["buy_order_id"],
                        body_parsed["quantity"],
                        body_parsed["timestamp"],
                    )
                    order_crud.update_punched(
                        body_parsed["sell_order_id"],
                        body_parsed["quantity"],
                        body_parsed["timestamp"],
                    )
                    print("UPDATED PUNCHED", body_parsed)
            else:
                body = body_parsed['body']
                if "success" in body_parsed and body_parsed["success"]:
                    if body['type'] == 'create':
                        print("CREATING")
                        order_crud.save_order(body_parsed["body"]['data'])
                        print("CREATING END")
                    elif body['type'] == 'update':
                        print("UPDATING ORDER END", body_parsed)
                        order_crud.update_order(body['data']['order_id'], body['data']['price'], body['data']['timestamp'], False)
                        print("UPDATED ORDER END")
                    elif body['type'] == 'cancel':
                        print("CANCELLING")
                        order_crud.update_order(body['data']['order_id'], body['data']['price'], body['data']['timestamp'], True)
                        print("CANCELLED ORDER")
                    else:
                        print("FUCK")
                else:
                    print(body_parsed)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        channel.basic_consume(
            queue=env_settings.mutation_persistent_queue_key, on_message_callback=cb
        )
        channel.start_consuming()
    except Exception as e:
        print(e)
    finally:
        connection.close()
