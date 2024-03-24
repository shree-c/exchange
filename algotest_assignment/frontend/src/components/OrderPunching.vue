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
      <InputNumber
        v-model="price"
        :min="1"
        :max-fraction-digits="2"
        input-class="w-28"
      />
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
import { ref } from 'vue'
import { client } from '@/network/client'
import { useToast } from 'primevue/usetoast'
import {useLocalStorage} from '@vueuse/core'
const toast = useToast()

const side = useLocalStorage<-1 | 1>('side',1)
const quantity = useLocalStorage<number>('quantity', 1)
const price = useLocalStorage<number>('price', 1)
// events
async function punchTrade() {
  try {
    const { data } = await client.post('order', {
      price: price.value,
      quantity: quantity.value,
      side: side.value
    })
    if (data.status === 'success') {
      toast.add({
        severity: 'success',
        summary: 'Order sent.'
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
