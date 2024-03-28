# EXCHANGE

## How to build and run app?

* Download the repository and cd into the folder. Make sure docker is installed in your system and docker daemon is running.
```
docker compose build
```

* Change env variables if you need (default values are set). I have added a __sample__ .env file
* Make sure port 3000 is free

```
docker compose up
```

* The web app can be accessed at http://localhost:3000. It has *bid-ask table*, *punch orders*, *trade stream*, and *order book*

* You can modify and cancel orders in order book.


## Architecture

![](/diagram.png)

* The app has two microservices **order punching interface** and **order matching engine**
* I am using redis db for fast transactions for matching orders

### Order punching interface
* A http server to accept request for order crud and trade streams.
* I have used FastAPI framework for http server

### Order matching engine

### Order matching algorithm
* Buy order with highest bid is given priority and sell order with lowest ask is given priority.

* If the orders have same bid or ask price the earliest order is given priority.

* If there is price difference between highest bid and lowest ask. For example, for a bid price of 45 and ask price of 42, the trade takes place at the price of the earliest of two orders.

### Order matching process

* An order is punched through order punching interface by http requests.
* Immediately, the order is assigned an order_id and stored in order book, a redis hashmap. At the same time, a score is calculated based on the bid or ask price and order entry time, and the order_id is added to order match queue.

##### Order match queue

* Two sorted sets are maintained for buy and sell orders respectively which holds order_ids based on the priority described above.

* A score is calculated based on the bid/ask price and timestamp.

* Timestamp is unix epoch in further mentions.

* We want lowest bid price to rank higher in sell queue and highest bid price to rank higher.

* At the same time we want to give higher priority to earliest order if two orders have same bid or ask price.

* Which means larger the timestamp lower should be the score within it's bid or ask price.

#### Calculating score

* SCALE here is just a large positivr number which keeps score from going negative because timestamp is a large number, but the ordering works regardless.

* For sell orders : (Ask_price * SCALE) - timestamp.

* For buy orders : -1 * (bid_price * SCALE) - timestamp.

* Multiplied by -1 to keep both buy and sell scores in ascending order.


#### Order matching engine internals
* An infinite loop with sleep every iteration by the amount supplied by the env variable.
* However, a better scheme would be processing every order until an order match is not possible and try to match again when there is new entry in either buy or sell list.
* Inside the loop if the buy price >= sell price trade is taken.
* If the amount traded is equal to the quantity of the order, or if an order is executed partially, if quantity - previously punched == traded quantity, the order_id is popped from the queue, else the loop goes to next iteration.

#### Race conditions

* To prevent race conditions I am popping order ids before i inspect them so that they are not cancelled/update/punched during that
