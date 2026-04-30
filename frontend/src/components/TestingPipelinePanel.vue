<script setup>
import PipelineView from './PipelineView.vue'
import { testModule, fetchDefaultTestInput } from '../api.js'

const props = defineProps({
  trace: { type: Array, default: () => [] },
  running: { type: String, default: '' },
  selectedAgent: { type: String, required: true },
  testMode: { type: Boolean, default: false },
  busy: { type: Boolean, default: false },
  state: { type: Object, required: true },
  pushLog: { type: Function, required: true },
  resetApp: { type: Function, required: true },
})

const emit = defineEmits([
  'update:test-mode',
  'update:selected-agent',
  'update:busy',
  'replace-log',
])

async function setMode(nextTestMode) {
  emit('update:test-mode', nextTestMode)
  props.resetApp()
  if (nextTestMode) {
    emit('update:selected-agent', 'research')
    props.state.research_report = null
    props.state.project_brief = null
    props.state.running = ''
    try {
      const res = await fetchDefaultTestInput('research')
      if (res?.project_brief) props.state.project_brief = res.project_brief
      if (res?.research_report) props.state.research_report = res.research_report
      if (res?.project_brief) props.pushLog('Default research input loaded.')
      if (res?.research_report) props.pushLog('Default research_report loaded.')
    } catch (e) {
      props.pushLog(`ERROR: failed to load default test input: ${e?.message || String(e)}`)
    }
  }
}

async function testSelectedModule() {
  if (props.busy) return
  if (!['research', 'product'].includes(props.selectedAgent)) {
    props.pushLog('Module test currently supports: research, product')
    return
  }
  const moduleId = props.selectedAgent
  emit('update:busy', true)
  emit('update:selected-agent', moduleId)
  props.state.running = moduleId

  props.state.trace = []
  if (moduleId === 'research') {
    props.state.research_report = null
  }
  props.state.prd = null
  props.state.tech_design = null
  props.state.code_artifact = null
  props.state.qa_report = null
  props.state.final_package = null
  props.state.guardrail_flags = []
  props.state.citations = []
  props.state.revision_round = 0
  emit('replace-log', [])

  try {
    const res = await testModule(moduleId)
    if (Array.isArray(res.debug_logs)) emit('replace-log', res.debug_logs)
    if (res.trace) props.state.trace = res.trace
    if (res.project_brief) props.state.project_brief = res.project_brief
    if (res.research_report) props.state.research_report = res.research_report
    if (res.prd) props.state.prd = res.prd
    if (Array.isArray(res.citations) && res.citations.length) props.state.citations = res.citations
    if (Array.isArray(res.guardrail_flags) && res.guardrail_flags.length) props.state.guardrail_flags = res.guardrail_flags
    props.state.revision_round = res.revision_round || 0
    props.state.running = ''
    emit('update:busy', false)
    emit('update:selected-agent', moduleId)
  } catch (e) {
    props.pushLog(`ERROR: ${e?.message || String(e)}`)
    emit('update:busy', false)
    props.state.running = ''
  }
}

async function onTestStart(agentId) {
  if (!props.testMode) return
  if (!['research', 'product'].includes(agentId)) {
    props.pushLog('Module test currently supports: research, product')
    return
  }
  emit('update:selected-agent', agentId)
  try {
    const res = await fetchDefaultTestInput(agentId)
    if (res?.project_brief) props.state.project_brief = res.project_brief
    if (res?.research_report) props.state.research_report = res.research_report
    if (res?.research_report) props.pushLog(`Default ${agentId} research_report loaded.`)
  } catch (e) {
    props.pushLog(`ERROR: failed to load default test input: ${e?.message || String(e)}`)
  }
  await testSelectedModule()
}

async function onSelectAgent(agentId) {
  emit('update:selected-agent', agentId)
  if (!props.testMode) return
  if (!['research', 'product'].includes(agentId)) return
  try {
    const res = await fetchDefaultTestInput(agentId)
    if (res?.project_brief) props.state.project_brief = res.project_brief
    if ('research_report' in (res || {})) props.state.research_report = res.research_report
    props.pushLog(`Default ${agentId} input loaded.`)
  } catch (e) {
    props.pushLog(`ERROR: failed to load default test input: ${e?.message || String(e)}`)
  }
}
</script>

<template>
  <div class="panel" style="margin-top: 12px">
    <h2 style="margin: 0 0 10px 0">Mode</h2>
    <label style="display:flex;gap:10px;align-items:center;">
      <input type="checkbox" :checked="testMode" @change="setMode($event.target.checked)" />
      <span>Test mode (run selected agent in isolation)</span>
    </label>
  </div>

  <div class="panel">
    <h2>Pipeline</h2>
    <div class="pipeline-hint">
      Click any agent card to view its dedicated panel.
    </div>
    <PipelineView
      :trace="trace"
      :running="running"
      :active-agent="selectedAgent"
      :test-mode="testMode"
      @select="onSelectAgent"
      @test-start="onTestStart"
    />
  </div>
</template>
