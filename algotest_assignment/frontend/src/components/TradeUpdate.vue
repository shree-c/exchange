<template>
  <div v-if="wsData">
    <div class="text-3xl ml-auto w-max font-mono">
      {{ wsData.length > 0 ? wsData[wsData.length - 1].price : 0 }} : LTP
    </div>
    <DataTable
      v-if="wsData"
      :value="wsData"
      size="small"
      state-storage="local"
      state-key="trade-table"
      scrollable
      scroll-height="30rem"
    >
      <template #header>
        <div class="w-max ml-auto space-x-2">
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
      <Column header="Timestamp" field="timestamp">
        <template #body="{ data }">
          <div>
            {{ new Date(data.timestamp * 1000).toLocaleString() }}
          </div>
        </template>
      </Column>
      <Column header="Quantity" field="quantity" />
      <Column header="Trade id" field="trade_id" />
      <Column header="Buy order id" field="buy_order_id" />
      <Column header="Sell order id" field="sell_order_id" />
      <Column header="Price" field="price" />
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import { computed, onBeforeUnmount, onErrorCaptured, onMounted, ref } from 'vue'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import type { TradeUpdate } from '@/types/main'
const props =  defineProps<{
  tradeUpdate: TradeUpdate[]
}>()
const emits = defineEmits<{
  (e: 'update:tradeUpdate', v: TradeUpdate[]): void
}>()

let ws: WebSocket | null = null
const rowsKept = ref<number>(20)
function connect() {
  if (ws) {
    ws.close()
  }
  ws = new WebSocket(`${import.meta.env.VITE_WS_URL}/trade-update`)
}

const wsData = computed({
  get: ()=> {
    return props.tradeUpdate
  },

  set: (value: TradeUpdate[])=> {
    emits('update:tradeUpdate', value)
  }
})

onMounted(() => {
  connect()
  if (ws)
    ws.onmessage = (data) => {
      wsData.value.unshift(JSON.parse(data.data) || [])
      wsData.value = wsData.value.slice(0, rowsKept.value)
    }
})

onBeforeUnmount(() => {
  if (ws) {
    ws.close()
  }
})


onErrorCaptured((er) => {
  console.log(er)
})
</script>

<style scoped></style>
