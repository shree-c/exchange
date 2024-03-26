<script setup lang="ts">
import OrderPunching from '@/components/OrderPunching.vue'
import OrderBook from '@/components/OrderBook.vue'
import TradeUpdate from '@/components/TradeUpdate.vue'
import type { TradeUpdate as TradeUpdateType } from '@/types/main'
import BidAskTable from '@/components/BidAskTable.vue'
import {provide, ref} from 'vue'
const wsData = ref<TradeUpdateType[]>([])
const orderPunchUpdate = ref<number>(0)
provide('orderPunchUpdate', orderPunchUpdate)


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
      <TradeUpdate v-model:trade-update="wsData"/>
    </div>
    <div>
      <OrderBook :trade-update-length="(wsData ? wsData.length : 0) + orderPunchUpdate" />
    </div>
  </div>

 
</template>
