from pydantic_settings import BaseSettings
from pydantic import PositiveFloat

class Settings(BaseSettings):
  redis_host: str = "localhost"
  redis_password: str = ""
  opi_bid_ask_spread_stream_interval: PositiveFloat = 1
  opi_trade_update_stream_interval: PositiveFloat = 1

env_settings = Settings()