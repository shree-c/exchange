from pydantic_settings import BaseSettings
from pydantic import PositiveFloat

class Settings(BaseSettings):
  order_matching_interval: PositiveFloat = 0.3
  redis_host: str = "localhost"
  redis_password: str = ""
  om_new_state_notify_key:str = "om_new_state"
  
  accumulator_queue_key:str = "accumulator"
  bid_ask_exchange: str = "bid_ask"
  trade_updates_exchange_name: str = "trade_update_exchange"
  state_change_queue_key:str = "order_book_state_changes"
  mutations_exchange_name:str = "mutations"
  mutation_persistent_queue_key:str = "mutations_persistent"
  rabbit_mq_hostname: str = "localhost"

env_settings = Settings()