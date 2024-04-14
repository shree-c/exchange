# EXCHANGE

## How to build and run app?

* Download the repository and cd into the folder. Make sure docker is installed in your system and docker daemon is running.

* Start rabbitmq docker container
```
docker run -d --hostname rabbitmq --name my-rabbit -p 5672:5672 -p 15672:15672 --network algotest rabbitmq:management
```

* Make sure rabbitmq is up. Check at http://localhost:15672
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


* Rabbit mq is used for messaging

### Exchanges
* TRADE UPDATE
  * Executed trades are published here
* MUTATION
  * Successful order book changes here
* BID ASK

### Queues
* ACCUMULATOR (persistent)
  * CRUD order requests are added to this queue
* STATE LOGS (persistent )
  * CRUD orders are added to this by accumulator

### Order punching interface
* A http server to accept request for order crud and trade streams.
* I have used FastAPI framework for http server.
* Functionality
  * CRUD order
  * BID ASK stream
  * Trade execution update stream

### Order matching engine
* Has two Four processes between which common memory is shared

#### Accumulator
* Reads from accumulator queue and tries to change order book and maintains price-table-buy, price-table-sell, priority-queue-buy and priority-queue-sell accordingly
* __Price tables__ are dictionaries of doubly linked lists
* __Order book__ is a dictionary
* __Priority_queues__ contains active prices

#### Match engine
* Reads from price tables, order book, **buy and sell priority queues**
* Publish trades if there is a match -> published to a **trade update queue**

#### Trade consumer
* Consume executed trades
  * Mutate persistent order book when a certain quantity is punched for an order
  * Publish it to general trade update exchange to be consumed by frontend

#### Bid ask publisher
* Read price tables and publish bid-ask spread table

__COMPLEXITY__
* O(1) for reading latest buy or sell item from __price_table__
* O(1) for reading order details from order book
* Amortized O(1) for consuming from and adding to priority queue (Provided if there is upper and lower limit to prices)
* O(1) for adding, updating and, cancelling order by accumulator
* O(1) for calculating bid-ask spread

### State manager
* Has two processes

#### Mutation manager
* Read from mutation exchange and save it to persistent storage

#### State logger
* Read from state log queue and save it to persistent storage


### Frontend
* Provides ability to punch, update and cancel orders; listen to bid ask spread, and trade and order-change updates; view order book.


# BUGS

* There is bug with fastapi websocket connection which freezes frontend streams on reloads
* It is related to aio_pika (rabbitmq client) and handling connections, I am working on it



