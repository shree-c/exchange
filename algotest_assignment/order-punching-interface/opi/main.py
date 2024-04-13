from fastapi import FastAPI, WebSocket, Depends, WebSocketDisconnect, WebSocketException
from fastapi.responses import JSONResponse
from opi.models.env import env_settings
import json
from fastapi.middleware.cors import CORSMiddleware
from pydantic import UUID4
from opi.models.api.main import (
    UpdateOrder,
    ErrorResponse,
    FailResponse,
    SuccessResponse,
    MultiOrderResponse,
    OrderPunched,
    OrderPending,
    SingleOrderResponse,
    LimitAndOffset,
)
import pika
from asyncio import sleep
from crud import OrderCRUD, TradeCRUD, env_settings as crud_env_settings
from redis import Redis
from redis.asyncio import Redis as ARedis
from redis import Redis
import asyncio
from aio_pika import ExchangeType, connect, connect_robust
from aio_pika.pool import Pool
from aio_pika.abc import AbstractIncomingMessage

app = FastAPI(
    responses={
        "404": {"model": FailResponse},
        "500": {"model": ErrorResponse},
        "400": {"model": FailResponse},
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# r = Redis(host=env_settings.redis_host, password=env_settings.redis_password)
# r_async = ARedis(host=env_settings.redis_host, password=env_settings.redis_password)
# connection = pika.BlockingConnection(
#     pika.ConnectionParameters(
#         "localhost",
#     )
# )

# channel = connection.channel()
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        "localhost",
    )
)


sync_channel = connection.channel()
order_crud = OrderCRUD(rabbit_channel=sync_channel)


# async_connection = await connect(host="localhost")
async def get_connection():
    return await connect_robust()


async_rabbit_pool = Pool(
    constructor=get_connection,
    max_size=5,  # Adjust pool size based on your needs
)
async def get_channel():
    async with async_rabbit_pool.acquire() as connection:
        return await connection.channel()

async_channel_pool: Pool = Pool(get_channel, max_size=10)



@app.post("/order", response_model=SuccessResponse)
async def process_order(order: OrderPending):
    [status, data] = order_crud.create(order.model_dump())
    if status:
        return SuccessResponse(data={"order_id": data})
    if data and data.startswith("INTERNAL"):
        return JSONResponse(
            status_code=500, content=ErrorResponse(message=data).model_dump()
        )
    return JSONResponse(
        status_code=404, content=FailResponse(data={"message": data}).model_dump()
    )


# @app.put("/order", response_model=SuccessResponse)
# async def update_order(order: UpdateOrder, order_id: UUID4):
#     [status, data] = order_crud.update(
#         str(order_id), order.updated_price, order.updated_quantity
#     )
#     if status:
#         return SuccessResponse(data=None)
#     if data and data.startswith("INTERNAL"):
#         return JSONResponse(
#             status_code=500, content=ErrorResponse(message=data).model_dump()
#         )
#     return JSONResponse(
#         status_code=400, content=FailResponse(data={"message": data}).model_dump()
#     )


# @app.delete("/order", response_model=SuccessResponse)
# async def delete_order(order_id: UUID4):
#     [status, data] = order_crud.delete(str(order_id))
#     if status:
#         return SuccessResponse(data=None)
#     if data and data.startswith("INTERNAL"):
#         return JSONResponse(
#             status_code=500, content=ErrorResponse(message=data).model_dump()
#         )
#     return JSONResponse(
#         status_code=400, content=FailResponse(data={"message": data}).model_dump()
#     )


@app.get("/order", response_model=SingleOrderResponse)
async def get_order(order_id: UUID4):
    [status, data] = order_crud.get(str(order_id))
    if status:
        return SingleOrderResponse(data=OrderPunched(**data, order_id=order_id))
    if data and data.startswith("INTERNAL"):
        return JSONResponse(
            status_code=500, content=ErrorResponse(message=data).model_dump()
        )
    return JSONResponse(
        status_code=404, content=FailResponse(data={"message": data}).model_dump()
    )

@app.get("/order/all", response_model=MultiOrderResponse)
async def get_all_orders(pagination: LimitAndOffset = Depends()):
    [status, data] = order_crud.get_all(pagination.limit, pagination.offset)
    if status:
        return MultiOrderResponse(data=list(map(lambda x: OrderPunched(**x), data)))
    if data and data.startswith("INTERNAL"):
        return JSONResponse(
            status_code=500, content=ErrorResponse(message=data).model_dump()
        )
    return JSONResponse(
        status_code=404, content=FailResponse(data={"message": data}).model_dump()
    )


# channel.exchange_declare(exchange=env_settings.bid_ask_exchange, exchange_type='fanout', durable=True)



@app.websocket("/depth")
async def get_all_trades(ws: WebSocket):
    async def send_to_ws(message):
        async with message.process():
            await ws.send_json(json.loads(message.body.decode()))
            print("SEEEEEEEEEEEEEEEEENT")

    try:
        await ws.accept()
        # with async_rabbit_pool.acquire() as connection:
            # channel = await connection
        print("TRYING TO DO STUFF")
        async with async_channel_pool.acquire() as channel:
            print("ACCEPTED")
            bid_ask_exchange = await channel.declare_exchange(
                "bid_ask", ExchangeType.FANOUT, durable=True
            )
            queue = await channel.declare_queue(exclusive=True)
            await queue.bind(bid_ask_exchange)
            await queue.consume(send_to_ws)
            await asyncio.Future()
    except WebSocketDisconnect as e:
        print("WS disconnect: get all trades, ", str(e))
    except WebSocketException as e:
        print("WS Exception: get all trades, ", str(e))
    except Exception as e:
        print("/depth exception ", str(e))


@app.websocket("/trade-update")
async def get_all_trades(ws: WebSocket):
    try:
        print("connection open")
        pubsub = r_async.pubsub()
        await pubsub.subscribe(crud_env_settings.trade_channel_name)
        await ws.accept()
        while True:
            print("loop start")
            data = await pubsub.get_message()
            if data:
                print("got data", data)
            if data and data["type"] == "message":
                await ws.send_json(json.loads(data["data"].decode()))
                print("sent data")
                continue
            await sleep(env_settings.opi_trade_update_stream_interval)
    except WebSocketDisconnect as e:
        print("WS disconnect: trade update, ", str(e))
    except WebSocketException as e:
        print("WS Exception: trade update, ", str(e))
    except Exception as e:
        print("/trade update exception ", str(e))

