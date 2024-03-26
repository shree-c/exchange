<template>
  <div>
    <div class="text-3xl pl-2 py-3 font-light flex justify-between items-baseline">BID - ASK</div>
    <div class="flex gap-2">
      <DataTable class="flex-grow h-80" :value="transformForTable(wsData['buy'] || {})">
        <Column field="price" header="Price">
          <template #body="{ data }">
            <div class="font-bold text-lg">
              {{ data.price }}
            </div>
          </template>
        </Column>
        <Column field="quantity">
          <template #header>
            <div class="text-right w-full">Quantity</div>
          </template>
          <template #body="{ data }">
            <div class="flex gap-20">
              <div class="min-w-52 font-bold text-lg">{{ data.quantity }}</div>
              <div class="flex-grow" v-if="data.quantity">
                <DepthIndicator :percent="(data.quantity / max) * 100" />
              </div>
            </div>
          </template>
        </Column>
      </DataTable>
      <DataTable class="flex-grow h-80" :value="transformForTable(wsData['sell'] || {})">
        <Column field="quantity" header="Quantity">
          <template #body="{ data }">
            <div class="flex gap-20">
              <div class="flex-grow rotate-180" v-if="data.quantity">
                <DepthIndicator :percent="(data.quantity / max) * 100" />
              </div>
              <div class="min-w-52 font-bold text-lg">{{ data.quantity }}</div>
            </div>
          </template>
        </Column>
        <Column field="price" header="Price">
          <template #body="{ data }">
            <div class="font-bold text-lg">
              {{ data.price }}
            </div>
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>

<script setup lang="ts">
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import { ref, computed, onMounted } from 'vue'
import DepthIndicator from '@/components/DepthIndicator.vue'

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
