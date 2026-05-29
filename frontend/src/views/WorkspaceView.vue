<script setup lang="ts">
import { onMounted } from 'vue'
import LoginBar from '../components/LoginBar.vue'
import CoursePanel from '../components/CoursePanel.vue'
import LearningWorkflowChecklist from '../components/LearningWorkflowChecklist.vue'
import UploadPanel from '../components/UploadPanel.vue'
import ChatPanel from '../components/ChatPanel.vue'
import StudyToolsPanel from '../components/StudyToolsPanel.vue'
import MindmapPanel from '../components/MindmapPanel.vue'
import ProgressPanel from '../components/ProgressPanel.vue'
import { useStudyStore } from '../stores/study'

const store = useStudyStore()

onMounted(async () => {
  if (localStorage.getItem('study_token')) {
    await store.loadCourses()
  }
})
</script>

<template>
  <main class="workspace">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark">AI</span>
        <div>
          <h1>学习知识库</h1>
          <p>课程资料、问答和复习生成</p>
        </div>
      </div>
      <LoginBar />
      <CoursePanel />
    </aside>
    <section class="main-grid">
      <LearningWorkflowChecklist />
      <UploadPanel />
      <ChatPanel />
      <StudyToolsPanel />
      <MindmapPanel />
      <ProgressPanel />
    </section>
  </main>
</template>
