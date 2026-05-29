<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Activity } from 'lucide-vue-next'
import { api } from '../api'

const overview = ref({ courses: 0, records: 0, average_mastery: 0 })

onMounted(async () => {
  try {
    overview.value = await api.progressOverview()
  } catch {
    overview.value = { courses: 0, records: 0, average_mastery: 0 }
  }
})
</script>

<template>
  <section class="panel progress-panel">
    <header class="panel-header">
      <Activity :size="20" />
      <h2>学习进度</h2>
    </header>
    <div class="metrics">
      <span><strong>{{ overview.courses }}</strong><small>课程</small></span>
      <span><strong>{{ overview.records }}</strong><small>记录</small></span>
      <span><strong>{{ overview.average_mastery }}</strong><small>平均掌握</small></span>
    </div>
  </section>
</template>
