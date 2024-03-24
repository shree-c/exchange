from sqlalchemy import Column, Integer, UUID, Boolean
import uuid
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def convert_row_to_dict(self):
    return {c.key: getattr(self, c.key) for c in self.__table__.columns}


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(Integer)
    side = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    accepted = Column(Boolean, default=False)
    punched = Column(Integer, default=0)

    def to_dict(self):
        return convert_row_to_dict(self)


class Trade(Base):
    __tablename__ = "trades"

    trade_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(Integer)
    buy_order_id = Column(UUID(as_uuid=True))
    sell_order_id = Column(UUID(as_uuid=True))
    price = Column(Integer)
    quantity = Column(Integer)

    def to_dict(self):
        return convert_row_to_dict(self)
