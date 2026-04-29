<script setup>
import ArtifactCard from './ArtifactCard.vue'

defineProps({
  selectedAgentTitle: { type: String, required: true },
  selectedAgent: { type: String, required: true },
  selectedAgentRunning: { type: Boolean, default: false },
  selectedAgentData: { type: [Object, Array, String, null], default: null },
  testMode: { type: Boolean, default: false },
  state: { type: Object, required: true },
})
</script>

<template>
  <div class="panel agent-panel active-agent-panel">
    <div class="row between" style="margin-bottom: 10px">
      <h2 style="margin: 0">{{ selectedAgentTitle }} Panel</h2>
    </div>
    <div class="pipeline-hint" style="margin-bottom: 10px">
      This panel shows the selected agent's output snapshot.
    </div>
    <ArtifactCard
      v-if="selectedAgent === 'research' && testMode && state.project_brief"
      title="Test Input (Project Brief)"
      :data="state.project_brief"
    />
    <div class="agent-running-state" v-if="selectedAgentRunning && !selectedAgentData">
      <div class="agent-running-title">{{ selectedAgentTitle }} is running...</div>
      <div class="typing-dots" aria-label="Agent is processing">
        <span></span><span></span><span></span>
      </div>
      <div class="agent-running-note">
        This stage is active. Output will appear here once this agent finishes.
      </div>
    </div>
    <ArtifactCard
      v-else-if="selectedAgent === 'research'"
      title="Research Report"
      :data="state.research_report"
    />
    <ArtifactCard v-else-if="selectedAgent === 'product'" title="PRD" :data="state.prd" />
    <ArtifactCard v-else-if="selectedAgent === 'architect'" title="Technical Design" :data="state.tech_design" />
    <ArtifactCard v-else-if="selectedAgent === 'coder'" title="Code Artifact" :data="state.code_artifact" />
    <ArtifactCard v-else-if="selectedAgent === 'qa'" title="QA Report" :data="state.qa_report" />
    <ArtifactCard v-else-if="selectedAgent === 'delivery'" title="Final Package" :data="state.final_package" />
    <div class="chat-empty" v-else>
      No data for this agent yet. Run pipeline to generate outputs.
    </div>
  </div>
</template>
