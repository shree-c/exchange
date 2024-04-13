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
            if "action" in body_parsed:
                if body_parsed["action"] == "trade":
                    print("UPDATING order...")
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
                    print("UPDATED ORDER...", body_parsed)
            else:
                print("SAVING CREATED order")
                order_crud.save_order(body_parsed["body"])
                print("SAVED ORDER", body_parsed)
            print("SAVED CREATED ORDER")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        channel.basic_consume(
            queue=env_settings.mutation_persistent_queue_key, on_message_callback=cb
        )
        channel.start_consuming()
    except Exception as e:
        print(e)
    finally:
        connection.close()
