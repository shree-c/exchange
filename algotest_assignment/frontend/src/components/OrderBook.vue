<template>
  <div class="py-28 space-y-2 space-x-2">
    <DataTable :value="rdata" paginator :rows="20">
      <template #header>
        <div class="w-max ml-auto space-x-2">
          <InputNumber v-model:model-value="limit" :min="0" />
          <Button
            size="small"
            label="Prev"
            :disabled="offset == 0"
            @click="
              () => {
                offset -= 1
                fetchOrders()
              }
            "
          />
          <Button
            size="small"
            label="Next"
            :disabled="rdata.length !== limit"
            @click="
              () => {
                offset += 1
                fetchOrders()
              }
            "
          />
          <Button size="small" label="Reload" @click="fetchOrders" />
        </div>
      </template>
      <Column field="side" header="Side">
        <template #body="{data}">
          <div>
            {{ data.side === 1 ? 'BUY': 'SELL' }}
          </div>
        </template>
      </Column>
      <Column field="timestamp" header="Timestamp">
        <template #body="{ data }">
          <div>
            {{ new Date(data.timestamp * 1000).toLocaleString() }}
          </div>
        </template>
      </Column>
      <Column field="price" header="Price"></Column>
      <Column field="quantity" header="Quantity"></Column>
      <Column field="order_id" header="Order id"></Column>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import { useLocalStorage } from '@vueuse/core'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import InputNumber from 'primevue/inputnumber'
import { client } from '@/network/client'
import { useToast } from 'primevue/usetoast'
import { ref } from 'vue'
import type { Order } from '@/types/main'
import { off } from 'process'
const toast = useToast()
const limit = useLocalStorage('limit', 10)
const offset = useLocalStorage('offset', 0)
const rdata = ref<Order[]>([])

// events
async function fetchOrders() {
  try {
    const { data } = await client.get('order/all', {
      params: {
        limit: limit.value,
        offset: offset.value
      }
    })
    if (data.status === 'success') {
      rdata.value = data.data
      toast.add({
        severity: 'success',
        summary: 'Received orders'
      })
    }
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: JSON.stringify(error)
    })
  }
}
</script>

<style scoped></style>
