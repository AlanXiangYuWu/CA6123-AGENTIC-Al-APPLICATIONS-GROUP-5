<script setup>
defineProps({
  lines: { type: Array, default: () => [] },
})
</script>

<template>
  <div class="panel">
    <h2>Log</h2>
    <div class="log">
      <div v-for="(line, i) in lines" :key="i">{{ line }}</div>
    </div>
  </div>
</template>
