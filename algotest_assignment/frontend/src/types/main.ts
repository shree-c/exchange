export type TradeUpdate = {
  trade_id: string,
  timestamp: number,
  sell_order_id: string
  buy_order_id: string
  price: number
  quantity: number
}

export type Order = {
  order_id: string
  timestamp: number
  punched: number
  quantity: number
  side: number
}