from fastapi import FastAPI, WebSocket, Depends, WebSocketDisconnect, WebSocketException
from fastapi.responses import JSONResponse
from opi.models.env import env_settings
import json
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, UUID4
from opi.models.api.main import (
    UpdateOrder,
    ErrorResponse,
    FailResponse,
    SuccessResponse,
    MultiOrderResponse,
    OrderPunched,
    OrderPending,
    SingleOrderResponse,
)
from asyncio import sleep
from crud import OrderCRUD, TradeCRUD
from redis import Redis
from redis.asyncio import Redis as ARedis
from redis import Redis

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


r = Redis(host=env_settings.redis_host, password=env_settings.redis_password)
r_async = ARedis(host=env_settings.redis_host, password=env_settings.redis_password)
order_crud = OrderCRUD(r)
trade_curd = TradeCRUD(r)


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


@app.put("/order", response_model=SuccessResponse)
async def update_order(order: UpdateOrder, order_id: UUID4):
    [status, data] = order_crud.update(
        str(order_id), order.updated_price, order.updated_quantity
    )
    if status:
        return SuccessResponse(data=None)
    if data and data.startswith("INTERNAL"):
        return JSONResponse(
            status_code=500, content=ErrorResponse(message=data).model_dump()
        )
    return JSONResponse(
        status_code=400, content=FailResponse(data={"message": data}).model_dump()
    )


@app.delete("/order", response_model=SuccessResponse)
async def delete_order(order_id: UUID4):
    [status, data] = order_crud.delete(str(order_id))
    if status:
        return SuccessResponse(data=None)
    if data and data.startswith("INTERNAL"):
        return JSONResponse(
            status_code=500, content=ErrorResponse(message=data).model_dump()
        )
    return JSONResponse(
        status_code=400, content=FailResponse(data={"message": data}).model_dump()
    )


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


class LimitAndOffset(BaseModel):
    limit: int = Field(ge=1, le=500)
    offset: int = Field(ge=0)


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


@app.websocket("/depth")
async def get_all_trades(ws: WebSocket):
    try:
        await ws.accept()
        while True:
            await ws.send_json(
                {
                    "buy": order_crud.calculate_depth_buy(5)[1],
                    "sell": order_crud.calculate_depth_sell(5)[1],
                }
            )
            await sleep(env_settings.opi_bid_ask_spread_stream_interval)
    except WebSocketDisconnect as e:
        print("WS disconnect: get all trades, ", str(e))
    except WebSocketException as e:
        print("WS Exception: get all trades, ", str(e))
    except Exception as e:
        print("/depth exception ", str(e))


@app.websocket("/trade-update")
async def get_all_trades(ws: WebSocket, max: int = 50):
    try:
        print("connection open")
        pubsub = r_async.pubsub()
        await pubsub.subscribe("trades")
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
