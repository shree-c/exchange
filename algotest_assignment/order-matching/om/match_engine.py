from datetime import datetime
from om.utils.priority_queue import PQManager


def match_engine(shared_memory, mutation_lock, trade_publish_queue):
    # manage unique priority queue (combination of python set and priority queue)
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
        # blocking get
        top_buy_price = buy_pq.get()
        print("GOT BUY")
        print(top_buy_price)
        print("WAITING FOR SELL")
        # blocking get
        top_sell_price = sell_pq.get()
        print("TOP BUY", top_buy_price, "TOP SELL ", top_sell_price, flush=True)
        print("GOT SELL", flush=True)
        if top_buy_price >= top_sell_price:
            sell_queue_len = len(
                shared_memory["price_table_sell"][top_sell_price]._getvalue()
            )
            buy_queue_len = len(
                shared_memory["price_table_buy"][top_buy_price]._getvalue()
            )
            print(buy_queue_len, sell_queue_len)
            # while there are items in price table row
            with mutation_lock:
                while (
                    len(shared_memory["price_table_buy"][top_buy_price]._getvalue())
                    != 0
                    and len(
                        shared_memory["price_table_sell"][top_sell_price]._getvalue()
                    )
                    != 0
                ):
                    print("loop...")
                    # INSPECT items for cancellation and changes (if price doesn't match current row then the item has been changed)
                    buy_item = shared_memory["price_table_buy"][
                        top_buy_price
                    ]._getvalue()[0]
                    if buy_item["price"] != top_buy_price or buy_item["cancelled"]:
                        shared_memory["price_table_buy"][top_buy_price].popleft()
                    sell_item = shared_memory["price_table_sell"][
                        top_sell_price
                    ]._getvalue()[0]
                    if sell_item["price"] != top_sell_price or sell_item["cancelled"]:
                        shared_memory["price_table_buy"][top_buy_price].appendleft(
                            buy_item
                        )
                        shared_memory["price_table_sell"][top_sell_price].popleft()
                        continue
                    execution_quantity = min(
                        buy_item["quantity"] - buy_item["punched"],
                        sell_item["quantity"] - sell_item["punched"],
                    )
                    buy_item["punched"] += execution_quantity
                    sell_item["punched"] += execution_quantity
                    # publish
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
                    if buy_item["punched"] == buy_item["quantity"]:
                        print("Completely filled,  BUY", buy_item["order_id"])
                        shared_memory["price_table_buy"][top_buy_price].popleft()
                    if sell_item["punched"] == sell_item["quantity"]:
                        print("Completely filled, SELL ", sell_item["order_id"])
                        shared_memory["price_table_sell"][top_sell_price].popleft()
                    # check if chosen top_buy_price is current top buy price
                    if buy_pq.last_added_price.value > top_buy_price:
                        break
                    # check if chosen top_sell_price is current top sell price
                    if sell_pq.last_added_price.value < top_sell_price:
                        break
                    print("END...", flush=True)
                
                # if buy or sell row is not completely empty add prices back to priority queue
                if (
                    len(shared_memory["price_table_sell"][top_sell_price]._getvalue())
                    != 0
                ):
                    sell_pq.put(top_sell_price)
                if (
                    len(shared_memory["price_table_buy"][top_buy_price]._getvalue())
                    != 0
                ):
                    buy_pq.put(top_buy_price)
        else:
            # they don't match put them back
            buy_pq.put(top_buy_price)
            sell_pq.put(top_sell_price)
