<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import OrderPunching from '@/components/OrderPunching.vue'
import OrderBook from '@/components/OrderBook.vue'
import TradeUpdate from '@/components/TradeUpdate.vue'
import BidAskTable from '@/components/BidAskTable.vue'

</script>

<template>
  <div class="p-28 space-y-5">
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
