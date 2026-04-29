<script setup>
defineProps({
  idea: { type: String, required: true },
  busy: { type: Boolean, default: false },
  threadId: { type: String, default: '' },
  runDisabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:idea', 'reset', 'run'])

function onIdeaInput(event) {
  emit('update:idea', event.target.value)
}
</script>

<template>
  <div class="panel">
    <h2>Your Idea</h2>
    <textarea :value="idea" :disabled="busy" @input="onIdeaInput" />
    <div class="row between" style="margin-top: 12px">
      <span class="tag">thread: {{ threadId || '-' }}</span>
      <div class="row">
        <button class="secondary" @click="emit('reset')" :disabled="busy">Reset</button>
        <button @click="emit('run')" :disabled="busy || runDisabled">
          {{ busy ? 'Running…' : runDisabled ? 'Test mode' : 'Run pipeline' }}
        </button>
      </div>
    </div>
  </div>
</template>
