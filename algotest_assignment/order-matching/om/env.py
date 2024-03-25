from pydantic_settings import BaseSettings
from pydantic import PositiveFloat

class Settings(BaseSettings):
  order_matching_interval: PositiveFloat = 0.3
  redis_host: str = "localhost"
  redis_password: str = ""

env_settings = Settings()