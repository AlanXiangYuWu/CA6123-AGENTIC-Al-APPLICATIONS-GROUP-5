<script setup>
defineProps({
  trace: { type: Array, default: () => [] },
  running: { type: String, default: '' },
})

const NODES = [
  { id: 'customer', label: 'Customer' },
  { id: 'research', label: 'Research' },
  { id: 'product', label: 'Product' },
  { id: 'architect', label: 'Architect' },
  { id: 'coder', label: 'Coder' },
  { id: 'qa', label: 'QA' },
  { id: 'delivery', label: 'Delivery' },
]

function statusOf(id, trace, running) {
  if (running === id) return 'running'
  if (trace.includes(id)) return 'done'
  return ''
}
</script>

<template>
  <div class="pipeline">
    <div
      v-for="n in NODES"
      :key="n.id"
      class="node"
      :class="statusOf(n.id, trace, running)"
    >
      <div class="node-dot" />
      {{ n.label }}
    </div>
  </div>
</template>
