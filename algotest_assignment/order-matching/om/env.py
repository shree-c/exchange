from pydantic_settings import BaseSettings
from pydantic import PositiveFloat


class Settings(BaseSettings):
    accumulator_queue_key: str = "accumulator"
    bid_ask_exchange: str = "bid_ask"
    trade_updates_exchange_name: str = "trade_update_exchange"
    state_change_queue_key: str = "order_book_state_changes"
    mutations_exchange_name: str = "mutations"
    mutation_persistent_queue_key: str = "mutations_persistent"
    bid_ask_depth: int = 5
    rabbit_mq_hostname: str = "localhost"


env_settings = Settings()
