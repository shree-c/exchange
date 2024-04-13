from time import perf_counter_ns
from datetime import datetime
from om.utils.priority_queue import PQManager


def match_engine(shared_memory, mutation_lock, trade_publish_queue):
    buy_pq = PQManager(
        shared_memory["price_active_set_buy"],
        shared_memory["price_priority_queue_buy"],
        shared_memory["last_added_buy"],
        -1,
    )
    sell_pq = PQManager(
        shared_memory["price_active_set_sell"],
        shared_memory["price_priority_queue_sell"],
        shared_memory["last_added_sell"],
        1,
    )

    while True:
        top_buy_price = buy_pq.get()
        print("GOT BUY")
        print("WAITING FOR SELL")
        top_sell_price = sell_pq.get()
        print("TOP BUY", top_buy_price, "TOP SELL ", top_sell_price, flush=True)
        print("GOT SELL", flush=True)
        if top_buy_price >= top_sell_price:
            # taking snapshot of length it can be updated while orders are processed but we want to give priority to better bid or asks
            # or a switch should be kept to know if the buy or sell table has been updated
            sell_queue_len = len(
                shared_memory["price_table_sell"][top_sell_price]._getvalue()
            )
            buy_queue_len = len(
                shared_memory["price_table_buy"][top_buy_price]._getvalue()
            )
            print("BUY QUEUE LEN", buy_queue_len, "SELL QUEUE LEN", sell_queue_len)
            sell_index = 0
            buy_index = 0
            print("Before lock")
            lst = perf_counter_ns()
            with mutation_lock:
                lsp = perf_counter_ns()
                print(round((lsp - lst) / 1000000, 2), "milli secs", "lock acq")
                stx = perf_counter_ns()
                while True:
                    if sell_index >= sell_queue_len or buy_index >= buy_queue_len:
                        break
                    buy_item = shared_memory["price_table_buy"][
                        top_buy_price
                    ]._getvalue()[0]
                    if buy_item["price"] != top_buy_price or buy_item["cancelled"]:
                        shared_memory["price_table_buy"][top_buy_price].popleft()
                        buy_index += 1
                        continue
                    sell_item = shared_memory["price_table_sell"][
                        top_sell_price
                    ]._getvalue()[0]
                    if sell_item["price"] != top_sell_price or sell_item["cancelled"]:
                        shared_memory["price_table_buy"][top_buy_price].appendleft(
                            buy_item
                        )
                        shared_memory["price_table_sell"][top_sell_price].popleft()
                        sell_index += 1
                        continue
                    execution_quantity = min(
                        buy_item["quantity"] - buy_item["punched"],
                        sell_item["quantity"] - sell_item["punched"],
                    )
                    print(buy_item, sell_item, execution_quantity)
                    buy_item["punched"] += execution_quantity
                    sell_item["punched"] += execution_quantity
                    print(buy_item, sell_item, execution_quantity)
                    st = perf_counter_ns()
                    trade_publish_queue.put(
                        {
                            "buy_order_id": buy_item["order_id"],
                            "sell_order_id": sell_item["order_id"],
                            "timestamp": datetime.now().timestamp(),
                            "price": (
                                buy_item["price"]
                                if buy_item["timestamp"] >= sell_item["timestamp"]
                                else sell_item["price"]
                            ),
                            "quantity": execution_quantity,
                        }
                    )
                    sp = perf_counter_ns()
                    print(round((sp - st) / 1000000, 2), "milli secs")
                    if buy_item["punched"] == buy_item["quantity"]:
                        print("Completely filled,  BUY", buy_item["order_id"])
                        buy_index += 1
                        shared_memory["price_table_buy"][top_buy_price].popleft()
                    if sell_item["punched"] == sell_item["quantity"]:
                        print("Completely filled, SELL ", sell_item["order_id"])
                        sell_index += 1
                        shared_memory["price_table_sell"][top_sell_price].popleft()
            if sell_index != sell_queue_len:
                sell_pq.put(top_sell_price)
            if buy_index != buy_queue_len:
                buy_pq.put(top_buy_price)
        else:
            buy_pq.put(top_buy_price)
            sell_pq.put(top_sell_price)
