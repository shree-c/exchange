<script setup lang="ts">
import Toast from 'primevue/toast';
</script>

<template>
  <header>
    <Toast position="bottom-left"/>
    <div class="wrapper"></div>
  </header>
  <RouterView />
</template>
