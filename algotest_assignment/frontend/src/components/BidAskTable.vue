<template>
  <div>
    <div class="flex gap-2">
      <DataTable class="flex-grow h-80" :value="transformForTable(wsData['buy'] || {})">
        <Column field="quantity" header="Quantity" />
        <Column field="price" header="Price" />
      </DataTable>
      <DataTable class="flex-grow h-80" :value="transformForTable(wsData['sell'] || {})">
        <Column field="quantity" header="Quantity" />
        <Column field="price" header="Price" />
      </DataTable>
    </div>
  </div>
</template>

<script setup lang="ts">
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import { ref, computed, onMounted } from 'vue'

const wsData = ref<any>({})
const max = computed(() => {
  const allValues: any = []
  if (wsData.value['buy']) {
    allValues.push(...Object.values(wsData.value['buy']))
  }
  if (wsData.value['sell']) {
    allValues.push(...Object.values(wsData.value['sell']))
  }
  return Math.max(0, ...allValues)
})

function transformForTable(priceQuantityMap: Record<string, number>) {
  return Object.entries(priceQuantityMap).reduce(
    (prev: { price: number; quantity: number }[], cur) => {
      prev.push({
        price: +cur[0],
        quantity: cur[1]
      })
      return prev
    },
    []
  )
}

onMounted(() => {
  const ws = new WebSocket(`${import.meta.env.VITE_WS_URL}/depth`)
  ws.onmessage = (data) => {
    wsData.value = JSON.parse(data.data)
  }
})
</script>

<style scoped></style>
