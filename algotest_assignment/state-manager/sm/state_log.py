import pika
from sm.env import env_settings
from crud import OrderCRUD
import traceback
import json


def state_log_saver():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(env_settings.rabbit_mq_hostname)
    )
    try:
        channel = connection.channel()
        channel.queue_declare(queue=env_settings.state_change_queue_key, durable=True)
        order_crud = OrderCRUD(rabbit_channel=channel)

        def on_state_change(ch, method, props, body):
            body_parsed = json.loads(body.decode())
            order_crud.log_state_change(body_parsed)

        channel.basic_consume(
            queue=env_settings.state_change_queue_key,
            on_message_callback=on_state_change,
            auto_ack=True,
        )

        channel.start_consuming()
    except Exception as e:
        print(traceback.format_exc())
        print(e)
    finally:
        connection.close()
