<template>
  <div class="py-28 space-y-2 space-x-2">
    <div class="text-3xl pl-2 py-3 font-light flex justify-between items-baseline">
      <div>Order book</div>
      <div>
        <Button severity="danger" label="Flush Database" @click="flushDb"/>
      </div>
    </div>
    <DataTable
      v-if="ordersData"
      @row-edit-save="rowEditSave"
      v-model:editing-rows="editingRows"
      edit-mode="row"
      v-model:filters="filters"
      :value="ordersData"
      paginator
      :rows="20"
      filterDisplay="row"
      :global-filter-fields="['order_id', 'quantity', 'price', 'side']"
    >
      <template #header>
        <div class="flex-wrap w-max ml-auto space-x-2 flex items-center">
          <div>Last</div>
          <FloatLabel>
            <InputNumber v-model:model-value="limit" :min="0" :max="500" />
            <label>Number of records</label>
          </FloatLabel>
          <Button size="small" label="Fetch" @click="fetchOrders" />
          <IconField iconPosition="left">
            <InputIcon>
              <i class="pi pi-search" />
            </InputIcon>
            <InputText v-model="filters['global'].value" placeholder="Keyword Search" />
          </IconField>
        </div>
      </template>
      <Column field="side" header="Side">
        <template #body="{ data }">
          <div
            :class="{
              'border-green-400': data.side === 1,
              'border-red-400': data.side === -1
            }"
            class="border-0 border-l-4 px-2"
          >
            {{ data.side === 1 ? 'BUY' : 'SELL' }}
          </div>
        </template>
      </Column>
      <Column field="timestamp" header="Timestamp" sortable>
        <template #body="{ data }">
          <div>
            {{ new Date(data.timestamp * 1000).toLocaleString() }}
          </div>
        </template>
      </Column>
      <Column field="price" header="Price" sortable>
        <template #editor="{ data }">
          <InputNumber v-model="data.price" />
        </template>
      </Column>
      <Column field="quantity" header="Quantity" sortable>
        <!-- <template #editor="{ data }">
          <InputNumber v-model="data.quantity" />
        </template> -->
      </Column>
      <Column field="punched" header="Punched"></Column>
      <Column field="order_id" header="Order id"></Column>
      <Column field="status">
        <template #body="{ data }">
          <template v-if="data.punched === data.quantity">
            <div class="text-green-400 font-mono font-semibold">Filled</div>
          </template>
          <template v-else-if="data.cancelled === 1">
            <div class="text-rose-500 font-mono font-semibold">Cancelled</div>
          </template>
          <template v-else>
            <div class="text-lime-400 font-mono font-semibold">Pending</div>
          </template>
        </template>
      </Column>
      <Column header="Delete">
        <template #body="{ data }">
          <Button
            size="small"
            severity="danger"
            outlined
            label="Cancel"
            :disabled="data.punched > 0 || data.cancelled === 1"
            @click="
              async () => {
                await cancelOrder(data.order_id)
              }
            "
          />
        </template>
      </Column>
      <Column
        :rowEditor="true"
        style="width: 10%; min-width: 8rem"
        bodyStyle="text-align:center"
      ></Column>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import { useLocalStorage } from '@vueuse/core'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import type { DataTableRowEditSaveEvent } from 'primevue/datatable'
import Column from 'primevue/column'
import InputNumber from 'primevue/inputnumber'
import { client } from '@/network/client'
import { useNetworkWrapper } from '@/composables/networkWrapper'
import { watch, ref } from 'vue'
import type { Order } from '@/types/main'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import InputText from 'primevue/inputtext'
import FloatLabel from 'primevue/floatlabel'
import { FilterMatchMode } from 'primevue/api'
const props = defineProps<{
  tradeUpdateLength: number
}>()
// state
const { networkWrapper, toast } = useNetworkWrapper()
const editingRows = ref()
const limit = useLocalStorage('limit-x', 100)
const ordersData = ref<Order[]>([])
const filters = ref({
  global: { value: null, matchMode: FilterMatchMode.CONTAINS }
})
watch(()=> props.tradeUpdateLength, async ()=> {
  await fetchOrders()
}, {
  immediate: true,
})
// events
async function fetchOrders() {
  await networkWrapper(async () => {
    const { data } = await client.get('order/all', {
      params: {
        limit: limit.value,
        offset: 0
      }
    })
    if (data.status === 'success') {
      const orders = data.data as Order[]
      ordersData.value = orders.sort((a, b) => b.timestamp - a.timestamp)
    }
  })
}

async function rowEditSave({ index, newData }: DataTableRowEditSaveEvent) {
  const res = await updateOrder(newData.quantity, newData.price, newData.order_id)
  if (res) ordersData.value[index] = newData
}

async function cancelOrder(order_id: string) {
  await networkWrapper(async () => {
    const { data } = await client.delete('order', {
      params: {
        order_id
      }
    })
    if (data.status === 'success') {
      toast.add({
        severity: 'secondary',
        summary: `Cancel requested for ${order_id}.`,
        life: 3000
      })
      await fetchOrders()
    }
  })
}

async function flushDb() {
  networkWrapper(async () => {
    const { data } = await client.get('flush-database')
    if (data.status === 'success') {
      await fetchOrders()
      toast.add({
        severity: 'secondary',
        summary: 'Database flush successful.',
        life: 3000
      })
    }
  })
}

async function updateOrder(updated_quantity: number, updated_price: number, order_id: number) {
  return networkWrapper(async () => {
    const { data } = await client.put(
      'order',
      {
        updated_quantity,
        updated_price
      },
      {
        params: {
          order_id
        }
      }
    )
    if (data.status === 'success') {
      toast.add({
        severity: 'secondary',
        summary: 'Updated requested ' + order_id,
        life: 3000
      })
      return true
    } else {
      return false
    }
  })
}
</script>

<style scoped></style>
