from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, UUID4, PositiveInt
from typing import List
from opi.controllers import order_management, matching_controller
from opi.models.api.main import (
    UpdateOrder,
    ErrorResponse,
    FailResponse,
    SuccessResponse,
    OrderResponse,
    OrderPunched,
    OrderPending
)
from asyncio import sleep
from csql import OrderCRUD, TradeCRUD
from datetime import datetime
from redis import Redis
import os


app = FastAPI(
    responses={
        "404": {"model": FailResponse},
        "500": {"model": ErrorResponse},
        "401": {"model": FailResponse},
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from redis import Redis

r = Redis(password="shreex")
order_crud = OrderCRUD(r)
trade_curd = TradeCRUD(r)


# TODO: handle internal errors
@app.post("/order", response_model=SuccessResponse)
async def process_order(order: OrderPending):
    [status, data] = order_crud.create(order)
    if not status:
        return ErrorResponse(message=data)
    return SuccessResponse(data=None)


@app.put("/order", response_model=SuccessResponse)
async def update_order(order: UpdateOrder):
    # res = order_management.update(
    # str(order.order_id), order.updated_quantity, order.updated_price
    # )
    [status, data] = order_crud.update(
        order.order_id, order.updated_price, order.updated_quantity
    )
    if not status:
        return FailResponse(data={"message": data})
    return SuccessResponse(data=None)


@app.delete("/order", response_model=SuccessResponse)
async def delete_order(order_id: UUID4):
    res = order_management.delete(str(order_id))
    if type(res) == str:
        return JSONResponse(
            status_code=400, content=ErrorResponse(message=res).model_dump()
        )
    return SuccessResponse(data=None)


@app.get("/order", response_model=OrderResponse)
async def get_order(order_id: UUID4):
    order = order_management.get(str(order_id))
    return order


class LimitAndOffset(BaseModel):
    limit: int = Field(ge=1, le=50)
    offset: int = Field(ge=1)


@app.get("/order/all", response_model=OrderResponse)
async def get_all_orders(limit: int, offset: int):
    [status, data] = order_crud.get_all(limit, offset)
    print(data)
    if status:
        return OrderResponse(data=list(map(lambda x: OrderPunched(**x), data)))
    return FailResponse(data={"reason": data})


@app.get("/trade/all")
async def get_all_trades(limit: int, offset: int):
    [status, data] = trade_curd.get_all(limit, offset)
    if status:
        return data
    return FailResponse(data={"reason": data})


@app.websocket("/depth")
async def get_all_trades(ws: WebSocket):
    await ws.accept()
    while True:
        await ws.send_json(
            {
                "buy": matching_controller.calculate_depth_buy(
                    5, matching_controller.TODAY_BUY_QUEUE
                ),
                "sell": matching_controller.calculate_depth_buy(
                    5, matching_controller.TODAY_SELLS_QUEUE
                ),
            }
        )
        print("data sent")
        await sleep(1)


@app.websocket("/trade-update")
async def get_all_trades(ws: WebSocket, max: int = 50):
    await ws.accept()
    while True:
        # TODO: use blocking pop
        [status, trades] = trade_curd.get_new_trades(max)
        if status:
            await ws.send_json(trades)
        print("trades sent", len(trades))
        await sleep(1)
