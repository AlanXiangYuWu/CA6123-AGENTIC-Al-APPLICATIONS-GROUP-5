<script setup>
defineProps({
  chatMessages: { type: Array, default: () => [] },
  busy: { type: Boolean, default: false },
  customerStageClosed: { type: Boolean, default: false },
  customerChatExpanded: { type: Boolean, default: true },
  chatInput: { type: String, default: '' },
  customerAgentThinking: { type: Boolean, default: false },
  customerWaitingInput: { type: Boolean, default: false },
  customerStageDone: { type: Boolean, default: false },
  currentBriefText: { type: String, default: '' },
})

const emit = defineEmits([
  'toggle-expand',
  'update:chatInput',
  'send-customer-message',
])

function onChatInput(event) {
  emit('update:chatInput', event.target.value)
}

function onEnterToSend(event) {
  if (event.shiftKey) return
  event.preventDefault()
  emit('send-customer-message')
}
</script>

<template>
  <div class="panel agent-panel active-agent-panel">
    <div class="row between">
      <h2 style="margin: 0">Customer Chat</h2>
      <div class="row">
        <span class="tag success" v-if="customerStageClosed">Completed</span>
        <button class="secondary" @click="emit('toggle-expand')">
          {{ customerChatExpanded ? 'Collapse' : 'Expand history' }}
        </button>
      </div>
    </div>
    <div v-if="!customerChatExpanded" class="chat-collapsed-hint">
      Customer stage is complete. Expand history to review this conversation.
    </div>
    <template v-else>
      <div class="chat-box">
        <template v-if="chatMessages.length">
          <div class="chat-msg" :class="m.role === 'user' ? 'user' : 'agent'" v-for="(m, i) in chatMessages" :key="`m-${i}`">
            <div class="chat-role">{{ m.role === 'user' ? 'You' : 'Customer Agent' }}</div>
            <div class="chat-content">{{ m.content }}</div>
          </div>
        </template>
        <div class="chat-msg agent typing" v-if="customerAgentThinking">
          <div class="chat-role">Customer Agent</div>
          <div class="typing-dots" aria-label="Customer Agent is thinking">
            <span></span><span></span><span></span>
          </div>
        </div>
        <div class="chat-msg agent waiting" v-else-if="customerWaitingInput">
          <div class="chat-role">Customer Agent</div>
          <div class="chat-content">Waiting for your reply</div>
        </div>
        <div class="chat-msg agent done" v-else-if="customerStageDone">
          <div class="chat-role">Customer Agent</div>
          <div class="chat-content">Done</div>
        </div>
        <div class="chat-empty" v-if="!chatMessages.length && !busy">
          Start with "Run pipeline", then continue chatting here.
        </div>
      </div>
      <div class="chat-compose">
        <textarea
          :value="chatInput"
          class="chat-input"
          placeholder="Reply to Customer Agent..."
          :disabled="busy || customerStageClosed"
          @input="onChatInput"
          @keydown.enter.exact="onEnterToSend"
        />
        <button @click="emit('send-customer-message')" :disabled="busy || customerStageClosed || !chatInput.trim()">
          {{ busy ? 'Sending…' : 'Send' }}
        </button>
      </div>
    </template>
  </div>

  <div class="panel">
    <h2>Current Brief</h2>
    <div class="brief-box" v-if="currentBriefText">
      <pre>{{ currentBriefText }}</pre>
    </div>
    <div class="chat-empty" v-else>
      Current brief not available yet.
    </div>
  </div>
</template>
