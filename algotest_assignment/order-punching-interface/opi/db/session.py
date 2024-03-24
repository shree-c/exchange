from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from csql import Base

engine = create_engine("sqlite:///orders.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
