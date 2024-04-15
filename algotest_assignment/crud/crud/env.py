from pydantic_settings import BaseSettings
# from pydantic import PositiveFloat
from pathlib import Path

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
  state_change_log_db:str = f"{Path.home()}/state_change_log.db"
  last_message_id:str = "last_message_id"
  accumulator_queue_key:str = "accumulator"

env_settings = Settings()
