<template>
  <div class="w-full bg-slate-700 h-6 rounded-sm">
    <div class="bg-emerald-300 h-full transition-all" :style="{
      width: `${percent}%`
    }"></div> 
  </div>
</template>

<script setup lang="ts">
defineProps<{
  percent: number,
}>()

</script>

<style scoped>

</style>