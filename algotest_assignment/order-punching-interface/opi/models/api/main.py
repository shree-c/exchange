from pydantic import BaseModel, PositiveInt, PositiveFloat, UUID4
from typing import Literal, Any, List


class OrderPending(BaseModel):
    quantity: PositiveInt
    price: PositiveFloat
    side: Literal[1, -1]


class UpdateOrder(BaseModel):
    updated_quantity: PositiveInt
    updated_price: PositiveFloat


class ResponseBase(BaseModel):
    status: Literal["success", "fail", "error"]


class SuccessResponse(ResponseBase):
    status: Literal["success", "fail", "error"] = "success"
    data: Any


class FailResponse(ResponseBase):
    status: Literal["success", "fail", "error"] = "fail"
    data: Any


class ErrorResponse(ResponseBase):
    status: Literal["success", "fail", "error"] = "error"
    message: str


class OrderPunched(BaseModel):
    order_id: UUID4
    timestamp: float
    punched: int
    quantity: int
    price: float
    punched: float
    side: Literal[1, -1]
    cancelled: Literal[1, 0]


class MultiOrderResponse(SuccessResponse):
    data: List[OrderPunched]


class SingleOrderResponse(SuccessResponse):
    data: OrderPunched
