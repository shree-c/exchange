from pydantic_settings import BaseSettings
from pydantic import PositiveFloat

class Settings(BaseSettings):
  redis_host: str = "localhost"
  redis_password: str = ""
  opi_bid_ask_spread_stream_interval: PositiveFloat = 1
  opi_trade_update_stream_interval: PositiveFloat = 1

  accumulator_queue_key:str = "accumulator"
  bid_ask_exchange: str = "bid_ask"
  trade_updates_exchange_name: str = "trade_update_exchange"
  state_change_queue_key:str = "order_book_state_changes"
  mutations_exchange_name:str = "mutations"
  mutation_persistent_queue_key:str = "mutations_persistent"
  rabbit_mq_hostname: str = "localhost"



env_settings = Settings()