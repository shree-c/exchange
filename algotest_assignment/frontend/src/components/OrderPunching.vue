<template>
  <div class="flex gap-2">
    <FloatLabel>
      <Dropdown
        class="w-32"
        :options="[
          { label: 'Buy', value: 1 },
          { label: 'Sell', value: -1 }
        ]"
        v-model="side"
        option-label="label"
        option-value="value"
      >
      </Dropdown>
      <label>Side</label>
    </FloatLabel>
    <FloatLabel>
      <InputNumber :min="1" :max-fraction-digits="0" v-model="quantity" input-class="w-28" />
      <label>Quantity</label>
    </FloatLabel>
    <FloatLabel>
      <InputNumber v-model="price" :min="1" :max-fraction-digits="2" input-class="w-28" />
      <label>Price</label>
    </FloatLabel>
    <Button label="Punch" @click="punchTrade" />
  </div>
</template>

<script setup lang="ts">
import Dropdown from 'primevue/dropdown'
import Button from 'primevue/button'
import FloatLabel from 'primevue/floatlabel'
import InputNumber from 'primevue/inputnumber'
import { client } from '@/network/client'
import { useLocalStorage } from '@vueuse/core'
import { useNetworkWrapper } from '@/composables/networkWrapper'
import { inject } from 'vue'
import type { Ref } from 'vue'
const { networkWrapper, toast } = useNetworkWrapper()

const side = useLocalStorage<-1 | 1>('side', 1)
const quantity = useLocalStorage<number>('quantity', 1)
const price = useLocalStorage<number>('price', 1)
const orderPunchUpdate = inject<Ref<number>>('orderPunchUpdate')
// events
async function punchTrade() {
  await networkWrapper(async () => {
    const { data } = await client.post('order', {
      price: price.value,
      quantity: quantity.value,
      side: side.value
    })
    if (data.status === 'success') {
      toast.add({
        severity: 'success',
        summary: `Order created. ${data.data.order_id}`,
        life: 5000
      })
      if (orderPunchUpdate)
        orderPunchUpdate.value = Math.random() * 10
    }
  })
}
</script>

<style scoped></style>
