<script setup>
defineProps({
  trace: { type: Array, default: () => [] },
  running: { type: String, default: '' },
  activeAgent: { type: String, default: 'customer' },
  testMode: { type: Boolean, default: false },
})
const emit = defineEmits(['select', 'test-start'])

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
      :class="[statusOf(n.id, trace, running), { active: activeAgent === n.id, clickable: true }]"
      role="button"
      tabindex="0"
      @click="emit('select', n.id)"
      @keydown.enter.prevent="emit('select', n.id)"
    >
      <div v-if="activeAgent === n.id" class="node-viewing-badge">VIEWING</div>
      <div v-if="running === n.id" class="node-running-badge">RUNNING</div>
      <div class="node-dot" />
      {{ n.label }}

      <button
        v-if="testMode && activeAgent === n.id && n.id === 'research'"
        class="node-test-start"
        @click.stop="emit('test-start', n.id)"
        aria-label="Start module test"
        type="button"
      >
        ▶ Start
      </button>
    </div>
  </div>
</template>
