<template>
  <div class="py-28 space-y-2 space-x-2">
    <div>
      <!-- <OrderManagement /> -->
    </div>
    <DataTable
      @row-edit-save="rowEditSave"
      v-model:editing-rows="editingRows"
      edit-mode="row"
      v-model:filters="filters"
      :value="rdata"
      paginator
      :rows="20"
      filterDisplay="row"
      :global-filter-fields="['order_id', 'quantity', 'price', 'side']"
    >
      <template #header>
        <div class="w-max ml-auto space-x-2 flex items-center">
          <div>Offset {{ offset }}</div>
          <IconField iconPosition="left">
            <InputIcon>
              <i class="pi pi-search" />
            </InputIcon>
            <InputText v-model="filters['global'].value" placeholder="Keyword Search" />
          </IconField>
          <FloatLabel>
            <InputNumber v-model:model-value="limit" :min="0" />
            <label>Number of records</label>
          </FloatLabel>
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
                //fetchOrders()
              }
            "
          />
          <Button size="small" label="Reload" @click="fetchOrders" />
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
        <template #editor="{ data }">
          <InputNumber v-model="data.quantity" />
        </template>
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
import { useToast } from 'primevue/usetoast'
import { onMounted, ref } from 'vue'
import type { Order } from '@/types/main'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import InputText from 'primevue/inputtext'
import FloatLabel from 'primevue/floatlabel'
const editingRows = ref()
const toast = useToast()
const limit = useLocalStorage('limit', 10)
const offset = useLocalStorage('offset', 0)
const rdata = ref<Order[]>([])
import { FilterMatchMode } from 'primevue/api'

const filters = ref({
  global: { value: null, matchMode: FilterMatchMode.CONTAINS }
})

onMounted(async () => {
  await fetchOrders()
})

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
    } else {
      throw data
    }
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: JSON.stringify(error)
    })
  }
}

async function rowEditSave({ index, newData }: DataTableRowEditSaveEvent) {
  const res = await updateOrder(newData.quantity, newData.price, newData.order_id)
  if (res) rdata.value[index] = newData
}

async function cancelOrder(order_id: string) {
  try {
    const { data } = await client.delete('order', {
      params: {
        order_id
      }
    })
    if (data.status === 'success') {
      toast.add({
        severity: 'success',
        summary: `order ${order_id} deleted.`,
        life: 3000
      })
      await fetchOrders()
    } else {
      throw data
    }
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: JSON.stringify(error)
    })
  }
}

async function updateOrder(updated_quantity: number, updated_price: number, order_id: number) {
  try {
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
        severity: 'success',
        summary: 'Updated for ' + order_id,
        life: 3000
      })
      return true
    }
    toast.add({
      severity: 'error',
      summary: JSON.stringify(data).slice(0, 150),
      life: 3000
    })
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: JSON.stringify(error),
      life: 3000
    })
  }
}
</script>

<style scoped></style>
