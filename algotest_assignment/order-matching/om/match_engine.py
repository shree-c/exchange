from time import sleep, perf_counter_ns
from multiprocessing import Lock
from datetime import datetime
from om.utils.priority_queue import PQManager


def match_engine(shared_memory, mutation_lock, trade_publish_queue):
    # sanity
    # print(shared_memory["price_active_set_buy"], "THis should be set")
    # print("should not throw error")
    # shared_memory['price_active_set_buy'].add(10)
    # print("Added 10")
    # normal_set = set()
    # print(10 in normal_set, "For normal set")
    # print(10 in shared_memory['price_active_set_buy'])

    # sanity
    buy_pq = PQManager(
        shared_memory["price_active_set_buy"],
        shared_memory["price_priority_queue_buy"],
        -1,
    )
    sell_pq = PQManager(
        shared_memory["price_active_set_sell"],
        shared_memory["price_priority_queue_sell"],
        1,
    )

    while True:
        # print(shared_memory["price_table_buy"], "PTB")
        # print(shared_memory["price_table_sell"], "PTS")
        # print(shared_memory["order_book"], "OB")
        print("JAI MAHADEV")
        print("WAITING FOR BUY ")
        top_buy_price = buy_pq.get()
        print("GOT BUY")
        # No waiting for sell
        print("WAITING FOR SELL")
        top_sell_price = sell_pq.get()
        print("TOP BUY", top_buy_price, "TOP SELL ", top_sell_price)
        print("GOT SELL")
        # if not top_sell_price:
        #     print("NO Sell order")
        #     buy_pq.put(top_buy_price)
        #     continue
        if top_buy_price >= top_sell_price:
            print("Match seem to exist")
            sell_queue_len = len(
                shared_memory["price_table_sell"][top_sell_price]._getvalue()
            )
            buy_queue_len = len(
                shared_memory["price_table_buy"][top_buy_price]._getvalue()
            )
            print("BUY QUEUE LEN", buy_queue_len, "SELL QUEUE LEN", sell_queue_len)
            if sell_queue_len == 0 or buy_queue_len == 0:
                print("THIS SHOULD NOT HAVE HAPPENED")
                continue
            sell_index = 0
            buy_index = 0
            print("Before lock")
            lst = perf_counter_ns()
            with mutation_lock:
                lsp = perf_counter_ns()
                
                print(round((lsp - lst) / 1000000, 2), 'milli secs', 'lock acq')
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
                        buy_item -= 1
                        shared_memory["price_table_sell"][top_sell_price].popleft()
                        sell_index += 1
                        continue
                    execution_quantity = min(
                        buy_item["quantity"] - buy_item['punched'], sell_item["quantity"] - sell_item['punched']
                    )
                    print("BEFORE")
                    print(buy_item, sell_item, execution_quantity)
                    buy_item["punched"] += execution_quantity
                    sell_item["punched"] += execution_quantity
                    print(buy_item, sell_item, execution_quantity)
                    print("AFTER")
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
                    print(round((sp - st) / 1000000, 2), 'milli secs')
                    if buy_item["punched"] == buy_item["quantity"]:
                        print("Completely filled,  BUY", buy_item["order_id"])
                        buy_index += 1
                        shared_memory["price_table_buy"][top_buy_price].popleft()
                    if sell_item["punched"] == sell_item["quantity"]:
                        print("Completely filled, SELL ", sell_item["order_id"])
                        sell_index += 1
                        shared_memory["price_table_sell"][top_sell_price].popleft()
                print(round((perf_counter_ns() - stx)/1000000, 2), "milli secs", 'a price loop') 
                print("FINISHED LOOP FOR", "BUY QUEUE LEN", buy_queue_len, "SELL QUEUE LEN", sell_queue_len)
            if sell_index != sell_queue_len:
                print("Trying to put  to sell queue")
                sell_pq.put(top_sell_price)
                print("sell queue done")
            if buy_index != buy_queue_len:
                print("Trying to put to buy queue")
                buy_pq.put(top_buy_price)
                print("Buy queue done")
            # print(
            #     "BUY QUEUE: ",
            #     len(shared_memory["price_table_buy"][top_buy_price]._getvalue()),
            # )
            # print(
            #     "SELL QUEUE: ",
            #     len(shared_memory["price_table_sell"][top_sell_price]._getvalue()),
            # )
        else:
            buy_pq.put(top_buy_price)
            sell_pq.put(top_sell_price)
