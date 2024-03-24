<template>
  {{ rData }}
  <div class="flex gap-2">
    <FloatLabel>
      <InputText v-model="orderId" />
      <label>Order id</label>
    </FloatLabel>
    <Button label="Get" @click="fetchOrder" />
  </div>
  <div v-if="rData" class="space-x-2">
    <Card>
      <template #content>
        <div>
          <div class="flex justify-between">
            <div class="text-[var(--primary-color)]">
              {{ rData.order_id }}
            </div>
            <div>
              {{ new Date(rData.timestamp * 1000).toLocaleString() }}
            </div>
            <div class="space-x-2">
              <Button
                v-if="!editMode"
                size="small"
                label="Edit"
                @click="
                  () => {
                    editMode = !editMode
                    ;(editData.price = rData?.price || 0),
                      (editData.quantity = rData?.quantity || 0)
                  }
                "
              >
              </Button>
              <Button
                v-if="editMode"
                size="small"
                label="Cancel"
                @click="
                  () => {
                    editMode = !editMode
                  }
                "
              >
              </Button>
              <Button
                v-if="editMode"
                size="small"
                label="Save"
                @click="
                  async () => {
                    editMode = !editMode
                    await updateOrder()
                    await fetchOrder()
                  }
                "
              >
              </Button>
            </div>
          </div>
          <template v-if="editMode">
            <div class="flex gap-5 py-5">
              <FloatLabel>
                <InputNumber v-model:model-value="editData.price" />
                <label for="">Price</label>
              </FloatLabel>
              <FloatLabel>
                <InputNumber v-model:model-value="editData.quantity" />
                <label for="">Quantity</label>
              </FloatLabel>
            </div>
          </template>
          <template v-else>
            <div class="flex gap-5 py-5">
              <div class="flex gap-2">
                <div>Side</div>
                <div>{{ rData.side }}</div>
              </div>
              <div class="flex gap-2">
                <div>Quantity</div>
                <div>{{ rData.quantity }}</div>
              </div>
              <div class="flex gap-2">
                <div>Price</div>
                <div>{{ rData.price }}</div>
              </div>
              <div class="flex gap-2">
                <div>Punched</div>
                <div>{{ rData.punched }}</div>
              </div>
              <div class="flex gap-2">
                <div>Alive</div>
                <div>{{ rData.cancelled }}</div>
              </div>
            </div>
          </template>
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { client } from '@/network/client'
import Card from 'primevue/card'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import FloatLabel from 'primevue/floatlabel'
import InputNumber from 'primevue/inputnumber'
import Toast from 'primevue/toast'
import { useToast } from 'primevue/usetoast'
import { ref } from 'vue'
import type { Order } from '@/types/main'
const toast = useToast()
const rData = ref<Order | null>(null)
const editMode = ref(false)
const editData = ref<{
  price: number
  quantity: number
}>({
  quantity: 10,
  price: 300
})

async function fetchOrder() {
  try {
    const { data } = await client.get('order', {
      params: {
        order_id: orderId.value
      }
    })
    if (data.status === 'success') {
      rData.value = data.data
    }
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: JSON.stringify(error),
      life: 3000
    })
  }
}

async function updateOrder() {
  try {
    const { data } = await client.put(
      'order',
      {
        updated_quantity: editData.value.quantity,
        updated_price: editData.value.price
      },
      {
        params: {
          order_id: orderId.value
        }
      }
    )
    if (data.status === 'success') {
      rData.value = data.data
      toast.add({
        severity: 'success',
        summary: 'Received orders',
        life: 3000
      })
    } else {
      toast.add({
        severity: 'error',
        summary: JSON.stringify(data).slice(0, 150),
        life: 3000
      })
    }
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: JSON.stringify(error),
      life: 3000
    })
  }
}

const orderId = ref('')
</script>

<style scoped></style>
