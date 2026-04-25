<script setup>
defineProps({
  title: { type: String, required: true },
  data: { type: [Object, Array, String, null], default: null },
})
</script>

<template>
  <div class="artifact" v-if="data">
    <h3>{{ title }}</h3>
    <pre>{{ typeof data === 'string' ? data : JSON.stringify(data, null, 2) }}</pre>
  </div>
</template>
