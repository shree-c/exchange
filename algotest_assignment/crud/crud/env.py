from pydantic_settings import BaseSettings
from pydantic import PositiveFloat

class Settings(BaseSettings):
  redis_host: str = "localhost"
  redis_password: str = ""
  crud_trade_book_prefix: str = "trade_book_"
  crud_trade_id_list_prefix: str = "trade_id_list_"
  crud_order_book_prefix: str = "order_book_"
  crud_order_match_queue_prefix: str = "sorted_or_"
  crud_order_id_list_prefix: str = "order_list_"
  trade_channel_name:str = "trades"
  om_new_state_notify_key:str = "om_new_state"

env_settings = Settings()
