# postgres://postgres.xfrdeqrzojivmjzxdbvo:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:5432/postgres
from csql import OrderCRUD

# from opi.db.session import session
# from opi.controllers.matching_controller import pluck_order_id
from redis import Redis

r = Redis(password="shreex")
order_crud = OrderCRUD(r)


def punch(order):
    order_crud.create(order)
    pass


# def update(order_id: str, quantity: int, price: float):
#     # [status, data] = order_crud.get(order_id)
#     # if not data:
#         # return "Order doesn't exist"
#     # # if order.punched != 0:
#     #     return "Order is not pending"
#     # print(order_id, quantity, price)
#     order_crud.update(order_id, quantity, price)
#     return True


# def delete(order_id: str):
#     order = order_crud.get(order_id)
#     if not order:
#         return "Order doesn't exist"
#     if order.punched != 0:
#         return "Order is not pending"
#     order_crud.delete(order_id)
#     return True


# def get(order_id):
#     return order_crud.get(order_id).to_dict()


# def get_all(limit, offset):
#     return order_crud.get_all(limit, offset)
