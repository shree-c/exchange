# EXCHANGE

## How to build and run app?

* Download the repository and cd into the folder. Make sure docker is installed in your system and docker daemon is running.
```
docker compose build
```

* Change env variables if you need (default values are set)
* Make sure port 3000 is free

```
docker compose up
```

* You will see a web app where you will see *bid-ask table*, *punch orders*, *trade stream*, and *order book*

* You can modify and cancel orders in order book. Order book has pagination


## Architecture

* The app has two microservices **order punching interface** and **order matching engine**
* I am using redis db for fast transactions for matching orders

### Order punching interface
* An http server to accepts order crud requests and for streaming trades
* I have used FastAPI framework for the server

### Order matching engine

* When a trade is punched an unique id is generated to identify it and is stored in order book
* I am using **Redis hash map** for order book for fast O(1) access
* And then the order is inserted into **order match queue**

#### Order match queue

* Order match queue is sorted set with O(log(n)) insertion and deletion
* The idea is to have order_ids ordered by bid/ask price and by time of entry
* A score is calculated to based of bid/ask price and time of entry : **(bid/ask *SCALE) - time of entry
* larger the time lower the score, higher the bid/ask price higher the order.
* multiply bid or ask by -1 to have them in opposite order so that it's easier to pop

#### Race conditions