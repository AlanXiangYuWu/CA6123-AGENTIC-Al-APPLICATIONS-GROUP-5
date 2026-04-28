<script setup>
import { ref, reactive, onMounted } from 'vue'
import PipelineView from './components/PipelineView.vue'
import ArtifactCard from './components/ArtifactCard.vue'
import { checkHealth, streamRun } from './api.js'

const idea = ref(
  'I want to build an AI coding companion app for kids aged 6-12 that teaches Python through gamified missions. Please produce a full plan.',
)
const busy = ref(false)
const health = ref(null)
const log = ref([])

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
}

function run() {
  if (!idea.value.trim() || busy.value) return
  reset()
  busy.value = true
  pushLog('Starting pipeline...')

  streamRun(idea.value, {
    onEvent(msg) {
      if (msg.event === 'started') {
        state.thread_id = msg.thread_id
        pushLog(`thread_id=${msg.thread_id}`)
      } else if (msg.event === 'node_done') {
        pushLog(`✓ ${msg.node}`)
        if (NODE_ORDER.includes(msg.node)) {
          if (!state.trace.includes(msg.node)) state.trace.push(msg.node)
          // Set running to the next node (best-effort)
          const idx = NODE_ORDER.indexOf(msg.node)
          state.running = NODE_ORDER[idx + 1] || ''
        }
        if (msg.diff) applyDiff(msg.diff)
      } else if (msg.event === 'final') {
        pushLog('Pipeline finished.')
        if (msg.state) applyDiff(msg.state)
        state.running = ''
        busy.value = false
      } else if (msg.event === 'blocked') {
        pushLog(`BLOCKED by ${msg.guardrail}`)
        busy.value = false
      } else if (msg.event === 'error') {
        pushLog(`ERROR: ${msg.message}`)
        busy.value = false
      }
    },
    onError() {
      pushLog('WebSocket error')
      busy.value = false
    },
    onClose() {
      busy.value = false
    },
  })
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

    <div class="panel">
      <h2>Your Idea</h2>
      <textarea v-model="idea" :disabled="busy" />
      <div class="row between" style="margin-top: 12px">
        <span class="tag">thread: {{ state.thread_id || '-' }}</span>
        <div class="row">
          <button class="secondary" @click="reset" :disabled="busy">Reset</button>
          <button @click="run" :disabled="busy">
            {{ busy ? 'Running…' : 'Run pipeline' }}
          </button>
        </div>
      </div>
    </div>

    <div class="panel">
      <h2>Pipeline</h2>
      <PipelineView :trace="state.trace" :running="state.running" />
    </div>

    <div class="panel" v-if="state.guardrail_flags.length">
      <h2>Guardrail flags</h2>
      <div v-for="(f, i) in state.guardrail_flags" :key="i" class="flag">
        {{ JSON.stringify(f) }}
      </div>
    </div>

    <div class="panel">
      <h2>Artifacts</h2>
      <div class="artifact-grid">
        <ArtifactCard title="Project Brief" :data="state.project_brief" />
        <ArtifactCard title="Research Report" :data="state.research_report" />
        <ArtifactCard title="PRD" :data="state.prd" />
        <ArtifactCard title="Technical Design" :data="state.tech_design" />
        <ArtifactCard title="Code Artifact" :data="state.code_artifact" />
        <ArtifactCard title="QA Report" :data="state.qa_report" />
      </div>
    </div>

    <div class="panel" v-if="state.final_package">
      <div class="row between">
        <h2 style="margin: 0">Final Package</h2>
        <button class="secondary" @click="downloadFinal">Download JSON</button>
      </div>
      <ArtifactCard title="" :data="state.final_package" />
    </div>

    <div class="panel">
      <h2>Log</h2>
      <div class="log">
        <div v-for="(line, i) in log" :key="i">{{ line }}</div>
      </div>
    </div>
  </div>
</template>
