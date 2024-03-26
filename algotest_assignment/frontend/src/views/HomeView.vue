<script setup lang="ts">
import OrderPunching from '@/components/OrderPunching.vue'
import OrderBook from '@/components/OrderBook.vue'
import TradeUpdate from '@/components/TradeUpdate.vue'
import BidAskTable from '@/components/BidAskTable.vue'

</script>

<template>
  <div class="p-28 space-y-10">
    <div>
      <BidAskTable/>
    </div>
    <div>
      <OrderPunching />
    </div>
    <div>
      <TradeUpdate />
    </div>
    <div>
      <OrderBook />
    </div>
  </div>

 
</template>
