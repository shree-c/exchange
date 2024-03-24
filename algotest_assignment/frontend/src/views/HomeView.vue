<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import OrderPunching from '@/components/OrderPunching.vue'
import OrderBook from '@/components/OrderBook.vue'
import TradeUpdate from '@/components/TradeUpdate.vue'
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

onMounted(() => {
  const ws = new WebSocket('ws://localhost:8000/depth')
  ws.onmessage = (data) => {
    wsData.value = JSON.parse(data.data)
  }
})
</script>

<template>
  <div class="p-28">
    <div>
      <OrderPunching />
    </div>
    <div>
      <OrderBook />
    </div>
    <div>
      <TradeUpdate />
    </div>
  </div>

  <main class="flex gap-2 p-28">
    <div class="flex-grow">
      <div class="text-slate-900 text-xl">SELL</div>
      <div class="relative overflow-x-auto" v-if="wsData['sell']">
        <table class="w-full text-sm text-left rtl:text-right text-gray-500 dark:text-gray-400">
          <thead
            class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400"
          >
            <tr>
              <th scope="col" class="px-6 py-3">Price</th>
              <th scope="col" class="px-6 py-3">Quantity</th>
            </tr>
          </thead>
          <tbody>
            <template :key="item[0]" v-for="item in Object.entries(wsData['sell'])">
              <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700">
                <td class="px-6 py-4">{{ item[0] }}</td>
                <td class="px-6 py-4">
                  <div class="flex gap-5 justify-between">
                    <div>
                      {{ item[1] }}
                    </div>
                    <div class="w-40 border bg-emerald-400">
                      <div
                        class="h-5 w-[100%] transition-all bg-pink-500"
                        :style="{
                          width: `${(item[1] / max) * 100}%`
                        }"
                      ></div>
                    </div>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>
    <div class="flex-grow">
      <div class="text-slate-900 text-xl">BUY</div>
      <div class="relative overflow-x-auto" v-if="wsData['buy']">
        <table class="w-full text-sm text-left rtl:text-right text-gray-500 dark:text-gray-400">
          <thead
            class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400"
          >
            <tr>
              <th scope="col" class="px-6 py-3">Quantity</th>
              <th scope="col" class="px-6 py-3">Price</th>
            </tr>
          </thead>
          <tbody>
            <template :key="item[0]" v-for="item in Object.entries(wsData['buy'])">
              <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700">
                <td class="px-6 py-4">
                  <div class="flex gap-5 justify-between">
                    <div class="w-40 rotate-180 border bg-emerald-400">
                      <div
                        class="h-5 w-[100%] transition-all bg-pink-500"
                        :style="{
                          width: `${(item[1] / max) * 100}%`
                        }"
                      ></div>
                    </div>
                    <div>
                      {{ item[1] }}
                    </div>
                  </div>
                </td>
                <td class="px-6 py-4">{{ item[0] }}</td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>
    <!-- </p> -->
  </main>
</template>
