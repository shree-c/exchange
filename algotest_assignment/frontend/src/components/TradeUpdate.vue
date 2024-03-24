<template>
  <div>
    <DataTable
      :value="wsData"
      size="small"
      state-storage="local"
      state-key="trade-table"
      scrollable
      scroll-height="30rem"
    >
      <template #header>
        <div class="w-max ml-auto space-x-2">
          <InputNumber input-class="w-28" v-model="rowsKept" :min="1" />
          <Button size="small" label="Reconnect" @click="connect" />
          <Button
            label="Clear"
            size="small"
            severity="secondary"
            @click="
              () => {
                wsData = []
              }
            "
          />
        </div>
      </template>
      <Column header="Timestamp" sortable field="timestamp">
        <template #body="{ data }">
          <div>
            {{ new Date(data.timestamp * 1000).toLocaleString() }}
          </div>
        </template>
      </Column>
      <Column header="Quantity" field="quantity" sortable />
      <Column header="Trade id" field="trade_id" />
      <Column header="Buy order id" field="buy_order_id" />
      <Column header="Sell order id" field="sell_order_id" />
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import { onBeforeUnmount, onMounted, ref } from 'vue'
import InputNumber from 'primevue/inputnumber'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import type { TradeUpdate } from '@/types/main'
const wsData = ref<TradeUpdate[]>([])
let ws: WebSocket | null = null
const rowsKept = ref<number>(20)
function connect() {
  if (ws) {
    ws.close()
  }
  ws = new WebSocket(`ws://localhost:8000/trade-update?max=10`)
}

onMounted(() => {
  connect()
  if (ws)
    ws.onmessage = (data) => {
      wsData.value.push(...JSON.parse(data.data || []))
      wsData.value = wsData.value.slice(-1 * rowsKept.value)
    }
})

onBeforeUnmount(() => {
  if (ws) {
    ws.close()
  }
})
</script>

<style scoped></style>
