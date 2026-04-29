<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import PipelineView from './components/PipelineView.vue'
import IdeaPanel from './components/IdeaPanel.vue'
import CustomerPanel from './components/CustomerPanel.vue'
import AgentOutputPanel from './components/AgentOutputPanel.vue'
import ArtifactsPanel from './components/ArtifactsPanel.vue'
import LogPanel from './components/LogPanel.vue'
import { checkHealth, streamRun, testModule, fetchDefaultTestInput } from './api.js'

const idea = ref(
  'I want to build an AI coding companion app for kids aged 6-12 that teaches Python through gamified missions. Please produce a full plan.',
)
const busy = ref(false)
const health = ref(null)
const log = ref([])
const chatInput = ref('')
const chatMessages = ref([])
const customerChatExpanded = ref(true)
const selectedAgent = ref('customer')
const testMode = ref(false)
const customerChatStatus = ref('idle')

const state = reactive({
  trace: [],
  running: '',
  thread_id: '',
  revision_round: 0,
  project_brief: null,
  research_report: null,
  prd: null,
  tech_design: null,
  code_artifact: null,
  qa_report: null,
  final_package: null,
  guardrail_flags: [],
  citations: [],
})

const NODE_ORDER = ['customer', 'research', 'product', 'architect', 'coder', 'qa', 'delivery']

function pushLog(msg) {
  const ts = new Date().toLocaleTimeString()
  log.value.unshift(`[${ts}] ${msg}`)
}

function extractCustomerQuestions(brief) {
  if (!brief || typeof brief !== 'object') return []
  if (!Array.isArray(brief.questions)) return []
  return brief.questions.filter((q) => typeof q === 'string' && q.trim())
}

function briefPreviewText(brief) {
  if (!brief) return ''
  if (typeof brief === 'string') return brief
  if (typeof brief !== 'object') return String(brief)
  if (typeof brief.current_brief === 'string' && brief.current_brief.trim()) return brief.current_brief
  if (typeof brief.summary === 'string' && brief.summary.trim()) return brief.summary
  return JSON.stringify(brief, null, 2)
}

const customerQuestions = computed(() => extractCustomerQuestions(state.project_brief))
const currentBriefText = computed(() => briefPreviewText(state.project_brief))
const customerNeedsClarification = computed(
  () => !!(state.project_brief && typeof state.project_brief === 'object' && state.project_brief.status === 'needs_clarification'),
)
const customerCompleted = computed(
  () => !!(state.project_brief && typeof state.project_brief === 'object' && !customerNeedsClarification.value),
)
const customerStageClosed = computed(
  () => customerCompleted.value && (state.running && state.running !== 'customer' || state.trace.includes('research')),
)
const selectedAgentTitle = computed(() => {
  const map = {
    customer: 'Customer',
    research: 'Research',
    product: 'Product',
    architect: 'Architect',
    coder: 'Coder',
    qa: 'QA',
    delivery: 'Delivery',
  }
  return map[selectedAgent.value] || 'Agent'
})
const selectedAgentData = computed(() => {
  const map = {
    customer: state.project_brief,
    research: state.research_report,
    product: state.prd,
    architect: state.tech_design,
    coder: state.code_artifact,
    qa: state.qa_report,
    delivery: state.final_package,
  }
  return map[selectedAgent.value]
})
const selectedAgentRunning = computed(() => busy.value && state.running === selectedAgent.value)
const customerAgentThinking = computed(() => customerChatStatus.value === 'thinking')
const customerWaitingInput = computed(() => customerChatStatus.value === 'waiting_input')
const customerStageDone = computed(() => customerChatStatus.value === 'done')
let lastLoggedBrief = ''
const seenCustomerQuestions = new Set()
const promptedQuestionSignatures = new Set()
const DEFAULT_CONFIG_HINT = 'If anything is unclear, just tell me to use the default configuration.'

function reset() {
  state.trace = []
  state.running = ''
  state.thread_id = ''
  state.revision_round = 0
  state.project_brief = null
  state.research_report = null
  state.prd = null
  state.tech_design = null
  state.code_artifact = null
  state.qa_report = null
  state.final_package = null
  state.guardrail_flags = []
  state.citations = []
  log.value = []
  chatInput.value = ''
  chatMessages.value = []
  customerChatExpanded.value = true
  selectedAgent.value = 'customer'
  customerChatStatus.value = 'idle'
  seenCustomerQuestions.clear()
  lastLoggedBrief = ''
}

async function setMode(nextTestMode) {
  testMode.value = nextTestMode
  reset()
  if (testMode.value) {
    selectedAgent.value = 'research'
    state.research_report = null
    state.project_brief = null
    state.running = ''
    try {
      const res = await fetchDefaultTestInput('research')
      if (res?.project_brief) state.project_brief = res.project_brief
      if (res?.project_brief) pushLog('Default research input loaded.')
    } catch (e) {
      pushLog(`ERROR: failed to load default test input: ${e?.message || String(e)}`)
    }
  }
}

watch(customerStageClosed, (closed) => {
  if (closed) customerChatExpanded.value = false
})

function appendChatMessage(role, content) {
  if (!content || typeof content !== 'string' || !content.trim()) return
  chatMessages.value.push({ role, content: content.trim() })
}

function syncCustomerQuestionsToChat() {
  let added = 0
  for (const q of customerQuestions.value) {
    if (seenCustomerQuestions.has(q)) continue
    appendChatMessage('agent', q)
    seenCustomerQuestions.add(q)
    added += 1
  }

  const signature = customerQuestions.value.join('\n')
  if (added > 0 && signature && !promptedQuestionSignatures.has(signature)) {
    appendChatMessage('agent', DEFAULT_CONFIG_HINT)
    promptedQuestionSignatures.add(signature)
  }
}

function applyDiff(diff) {
  for (const k of [
    'project_brief', 'research_report', 'prd', 'tech_design',
    'code_artifact', 'qa_report', 'final_package',
  ]) {
    if (k in diff && diff[k] !== null && diff[k] !== undefined) {
      state[k] = diff[k]
    }
  }
  if (Array.isArray(diff.guardrail_flags) && diff.guardrail_flags.length) {
    state.guardrail_flags = diff.guardrail_flags
  }
  if (Array.isArray(diff.citations) && diff.citations.length) {
    state.citations = diff.citations
  }
  if (typeof diff.revision_round === 'number') {
    state.revision_round = diff.revision_round
  }
  if (Array.isArray(diff.trace)) {
    state.trace = diff.trace
  }

  if ('project_brief' in diff && diff.project_brief !== null && diff.project_brief !== undefined) {
    const raw = typeof diff.project_brief === 'string'
      ? diff.project_brief
      : JSON.stringify(diff.project_brief, null, 2)
    if (raw && raw !== lastLoggedBrief) {
      pushLog(`project_brief updated:\n${raw}`)
      lastLoggedBrief = raw
    }
    syncCustomerQuestionsToChat()
  }
}

function executeRun(userMessage, fresh = false) {
  if (!userMessage?.trim() || busy.value) return
  if (fresh) reset()
  busy.value = true
  customerChatStatus.value = 'thinking'
  // Show running highlight immediately instead of waiting for first node update.
  if (fresh) {
    state.running = 'customer'
  } else if (!state.running) {
    state.running = selectedAgent.value || 'customer'
  }
  pushLog(fresh ? 'Starting pipeline...' : 'Continuing conversation...')
  appendChatMessage('user', userMessage)

  streamRun(userMessage, {
    onEvent(msg) {
      if (msg.event === 'started') {
        state.thread_id = msg.thread_id
        if (!state.running) state.running = 'customer'
        pushLog(`thread_id=${msg.thread_id}`)
      } else if (msg.event === 'node_waiting_input') {
        pushLog(`… ${msg.node} waiting for user input`)
        if (msg.node === 'customer') {
          state.running = 'customer'
          selectedAgent.value = 'customer'
          customerChatStatus.value = 'waiting_input'
        }
        if (msg.diff) applyDiff(msg.diff)
      } else if (msg.event === 'node_done') {
        pushLog(`✓ ${msg.node}`)
        if (msg.node === 'customer') customerChatStatus.value = 'done'
        if (NODE_ORDER.includes(msg.node)) {
          if (!state.trace.includes(msg.node)) state.trace.push(msg.node)
          // Auto-focus next panel for completed stages.
          const idx = NODE_ORDER.indexOf(msg.node)
          const nextNode = NODE_ORDER[idx + 1] || ''
          state.running = nextNode
          selectedAgent.value = nextNode || msg.node
        }
        if (msg.diff) applyDiff(msg.diff)
      } else if (msg.event === 'final') {
        pushLog('Pipeline finished.')
        if (msg.state) applyDiff(msg.state)
        const stillWaitingCustomerInput =
          customerChatStatus.value === 'waiting_input' ||
          (state.project_brief &&
            typeof state.project_brief === 'object' &&
            state.project_brief.status === 'needs_clarification')
        state.running = stillWaitingCustomerInput ? 'customer' : ''
        busy.value = false
        if (customerChatStatus.value === 'thinking') customerChatStatus.value = 'idle'
      } else if (msg.event === 'blocked') {
        pushLog(`BLOCKED by ${msg.guardrail}`)
        busy.value = false
        customerChatStatus.value = 'idle'
      } else if (msg.event === 'error') {
        pushLog(`ERROR: ${msg.message}`)
        busy.value = false
        customerChatStatus.value = 'idle'
      }
    },
    onError() {
      pushLog('WebSocket error')
      busy.value = false
      customerChatStatus.value = 'idle'
    },
    onClose() {
      busy.value = false
      if (customerChatStatus.value === 'thinking') customerChatStatus.value = 'idle'
    },
  }, state.thread_id)
}

async function testSelectedModule() {
  if (busy.value) return
  // Only support module testing in current MVP for 'research'
  if (selectedAgent.value !== 'research') {
    pushLog('Module test MVP currently supports only: research')
    return
  }
  busy.value = true
  selectedAgent.value = 'research'
  state.running = 'research'

  // Keep state.project_brief (default input) loaded by setMode().
  // Only clear outputs related to this module test.
  state.trace = []
  state.research_report = null
  state.prd = null
  state.tech_design = null
  state.code_artifact = null
  state.qa_report = null
  state.final_package = null
  state.guardrail_flags = []
  state.citations = []
  state.revision_round = 0
  log.value = []

  try {
    const res = await testModule('research')
    if (Array.isArray(res.debug_logs)) {
      // Replace log panel content with structured step logs.
      log.value = res.debug_logs
    }
    if (res.trace) state.trace = res.trace
    if (res.project_brief) state.project_brief = res.project_brief
    if (res.research_report) state.research_report = res.research_report
    if (Array.isArray(res.citations) && res.citations.length) state.citations = res.citations
    if (Array.isArray(res.guardrail_flags) && res.guardrail_flags.length) state.guardrail_flags = res.guardrail_flags
    state.revision_round = res.revision_round || 0
    state.running = ''
    busy.value = false
    selectedAgent.value = 'research'
    // Finished log is optional; intermediate steps are shown above.
  } catch (e) {
    pushLog(`ERROR: ${e?.message || String(e)}`)
    busy.value = false
    state.running = ''
  }
}

function run() {
  executeRun(idea.value, true)
}

function sendCustomerMessage() {
  const message = chatInput.value.trim()
  if (!message || busy.value) return
  chatInput.value = ''
  executeRun(message, false)
}

function selectAgent(agentId) {
  selectedAgent.value = agentId
}

async function onTestStart(agentId) {
  if (!testMode.value) return
  // MVP supports research-only tests.
  if (agentId !== 'research') {
    pushLog('Module test MVP currently supports only: research')
    return
  }
  await testSelectedModule()
}

function downloadFinal() {
  const data = {
    thread_id: state.thread_id,
    trace: state.trace,
    project_brief: state.project_brief,
    research_report: state.research_report,
    prd: state.prd,
    tech_design: state.tech_design,
    code_artifact: state.code_artifact,
    qa_report: state.qa_report,
    final_package: state.final_package,
    citations: state.citations,
    guardrail_flags: state.guardrail_flags,
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `final_package_${state.thread_id || 'demo'}.json`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  try {
    health.value = await checkHealth()
  } catch {
    health.value = { status: 'unreachable', model: '?' }
  }
})
</script>

<template>
  <div class="app">
    <h1>
      🤖 CA6123 Agentic Workflow
      <span class="tag" v-if="health">model: {{ health.model }} · {{ health.status }}</span>
    </h1>

    <div class="panel" style="margin-top: 12px">
      <h2 style="margin: 0 0 10px 0">Mode</h2>
      <label style="display:flex;gap:10px;align-items:center;">
        <input type="checkbox" v-model="testMode" @change="setMode($event.target.checked)" />
        <span>Test mode (run selected agent in isolation)</span>
      </label>
    </div>

    <IdeaPanel
      :idea="idea"
      :busy="busy"
      :thread-id="state.thread_id"
      @update:idea="idea = $event"
      @reset="reset"
      @run="run"
      :run-disabled="testMode"
    />

    <div class="panel">
      <h2>Pipeline</h2>
      <div class="pipeline-hint">
        Click any agent card to view its dedicated panel.
      </div>
      <PipelineView
        :trace="state.trace"
        :running="state.running"
        :active-agent="selectedAgent"
        :test-mode="testMode"
        @select="selectAgent"
        @test-start="onTestStart"
      />
    </div>

    <CustomerPanel
      v-if="selectedAgent === 'customer'"
      :chat-messages="chatMessages"
      :busy="busy"
      :customer-stage-closed="customerStageClosed"
      :customer-chat-expanded="customerChatExpanded"
      :chat-input="chatInput"
      :customer-agent-thinking="customerAgentThinking"
      :customer-waiting-input="customerWaitingInput"
      :customer-stage-done="customerStageDone"
      :current-brief-text="currentBriefText"
      @toggle-expand="customerChatExpanded = !customerChatExpanded"
      @update:chat-input="chatInput = $event"
      @send-customer-message="sendCustomerMessage"
    />

    <AgentOutputPanel
      v-if="selectedAgent !== 'customer'"
      :selected-agent-title="selectedAgentTitle"
      :selected-agent="selectedAgent"
      :selected-agent-running="selectedAgentRunning"
      :selected-agent-data="selectedAgentData"
      :test-mode="testMode"
      :state="state"
    />

    <div class="panel" v-if="state.guardrail_flags.length">
      <h2>Guardrail flags</h2>
      <div v-for="(f, i) in state.guardrail_flags" :key="i" class="flag">
        {{ JSON.stringify(f) }}
      </div>
    </div>

    <ArtifactsPanel :state="state" @download-final="downloadFinal" />

    <LogPanel :lines="log" />
  </div>
</template>
