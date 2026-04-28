<script setup>
import ArtifactCard from './ArtifactCard.vue'

const emit = defineEmits(['download-final'])

defineProps({
  state: { type: Object, required: true },
})

const artifactDefs = [
  { title: 'Project Brief', key: 'project_brief' },
  { title: 'Research Report', key: 'research_report' },
  { title: 'PRD', key: 'prd' },
  { title: 'Technical Design', key: 'tech_design' },
  { title: 'Code Artifact', key: 'code_artifact' },
  { title: 'QA Report', key: 'qa_report' },
]
</script>

<template>
  <div class="panel">
    <h2>Artifacts</h2>
    <div class="artifact-grid">
      <ArtifactCard
        v-for="item in artifactDefs"
        :key="item.key"
        :title="item.title"
        :data="state[item.key]"
      />
    </div>
  </div>

  <div class="panel" v-if="state.final_package">
    <div class="row between">
      <h2 style="margin: 0">Final Package</h2>
      <button class="secondary" @click="emit('download-final')">Download JSON</button>
    </div>
    <ArtifactCard title="" :data="state.final_package" />
  </div>
</template>
