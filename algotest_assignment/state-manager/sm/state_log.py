import pika
from sm.env import env_settings
from datetime import datetime
from crud import OrderCRUD
import json


def state_log_saver():
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()
    channel.queue_declare(queue=env_settings.state_change_queue_key, durable=True)
    order_crud = OrderCRUD(rabbit_channel=channel)

    def on_state_change(ch, method, props, body):
        body_parsed = json.loads(body.decode())
        # if "action" in body_parsed:
        #     if body_parsed["action"] == "trade":
        #         print("UPDATING order...")
        #         order_crud.update_punched(
        #             body_parsed["buy_order_id"],
        #             body_parsed["quantity"],
        #             body_parsed["timestamp"],
        #         )
        #         order_crud.update_punched(
        #             body_parsed["sell_order_id"],
        #             body_parsed["quantity"],
        #             body_parsed["timestamp"],
        #         )
        #         print("UPDATED ORDER...", body_parsed)
        #     else:
        order_crud.log_state_change(body_parsed)

    channel.basic_consume(
        queue=env_settings.state_change_queue_key,
        on_message_callback=on_state_change,
        auto_ack=True,
    )

    channel.start_consuming()
