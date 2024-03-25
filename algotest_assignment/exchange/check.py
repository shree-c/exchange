from exwh.crud.main import OrderCRUD
from datetime import datetime
from time import sleep
from exwh.models.db import Base
from redis import Redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

r = Redis(host="redis")
engine = create_engine("sqlite:///../orders.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
order_crud = OrderCRUD(session=session)


TODAY_BUY = f"sorted_or_buys_{datetime.now().strftime('%Y_%m_%d')}"
TODAY_SELL = f"sorted_or_sells_{datetime.now().strftime('%Y_%m_%d')}"
print(TODAY_BUY)

# print(r.zra)
orders = r.zrange(TODAY_BUY, 0, 100, withscores=True)
torders = {k[0].decode(): k[1] for k in orders}


sqorders = {
    str(x.order_id): x for x in order_crud.get_orders([x for x in torders.keys()])
}




print("\n")
for k in torders.keys():
    order = sqorders[k]
    print(
        f"{str(order.order_id)} | {round(order.price, 2)} | {datetime.fromtimestamp(order.timestamp)} | {torders[str(order.order_id)]} | {order.quantity - order.punched}"
    )


# 516.0
# 520.0
# 531.0
# 534.0
# 586.0
# 612.0
# 635.0
