<script setup lang="ts">
import OrderPunching from '@/components/OrderPunching.vue'
import OrderBook from '@/components/OrderBook.vue'
import TradeUpdate from '@/components/TradeUpdate.vue'
import type { TradeUpdate as TradeUpdateType } from '@/types/main'
import BidAskTable from '@/components/BidAskTable.vue'
import { provide, ref, onMounted, onBeforeUnmount } from 'vue'
const wsData = ref<TradeUpdateType[]>([])
const orderPunchUpdate = ref<number>(0)
import { useToast } from 'primevue/usetoast'
const toast = useToast()
provide('orderPunchUpdate', orderPunchUpdate)

let ws: WebSocket | null = null
const rowsKept = ref<number>(20)
function connect() {
  if (ws) {
    ws.close()
  }
  ws = new WebSocket(`${import.meta.env.VITE_WS_URL}/mutation-updates`)
}

onMounted(() => {
  connect()
  if (ws)
    ws.onmessage = (message: any) => {
      console.log(message)
      const message_body = JSON.parse(message['data'])
      if (message_body['success']) {
        toast.add({
          severity: 'success',
          life: 3000,
          summary: JSON.stringify(message_body.body)
        })
      } else {
        toast.add({
          severity: 'error',
          summary: message_body.message,
          life: 3000
        })
      }
    }
})

onBeforeUnmount(() => {
  if (ws) {
    ws.close()
  }
})
</script>

<template>
  <div class="p-28 space-y-10">
    <div>
      <BidAskTable />
    </div>
    <div>
      <OrderPunching />
    </div>
    <div>
      <TradeUpdate v-model:trade-update="wsData" />
    </div>
    <div>
      <OrderBook :trade-update-length="(wsData ? wsData.length : 0) + orderPunchUpdate" />
    </div>
  </div>
</template>
