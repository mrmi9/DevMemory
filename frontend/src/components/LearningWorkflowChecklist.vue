<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { CheckCircle2, Circle, RefreshCw } from 'lucide-vue-next'
import AppPanel from './AppPanel.vue'
import { api, type ChatSession, type DocumentItem, type GeneratedQuestion, type StudyCard } from '../api'
import { useStudyStore } from '../stores/study'

type WorkflowStatus = 'done' | 'current' | 'locked'

const store = useStudyStore()
const documents = ref<DocumentItem[]>([])
const sessions = ref<ChatSession[]>([])
const cards = ref<StudyCard[]>([])
const questions = ref<GeneratedQuestion[]>([])
const loading = ref(false)
const error = ref('')

const hasCourse = computed(() => Boolean(store.selectedCourseId))
const hasDocuments = computed(() => documents.value.length > 0)
const hasSearchableDocuments = computed(() =>
  documents.value.some((document) => document.chunk_count > 0 && !['failed', 'uploaded', 'processing'].includes(document.status))
)
const hasProcessingDocuments = computed(() =>
  documents.value.some((document) => ['uploaded', 'processing'].includes(document.status) || document.latest_job?.status === 'queued')
)
const hasAsked = computed(() => sessions.value.length > 0)
const hasStudyAssets = computed(() => cards.value.length > 0 || questions.value.length > 0)
const hasReviewed = computed(() => cards.value.some((card) => card.mastery > 0))

const steps = computed<Array<{ title: string; detail: string; status: WorkflowStatus }>>(() => [
  {
    title: '创建课程',
    detail: hasCourse.value ? `正在学习：${store.selectedCourse?.title ?? '当前课程'}` : '先建立一门课程，把资料、问答和复习内容归档在一起。',
    status: hasCourse.value ? 'done' : 'current'
  },
  {
    title: '上传资料',
    detail: hasDocuments.value ? `已收录 ${documents.value.length} 份资料。` : '上传 PDF、Word、Markdown 或图片笔记。',
    status: !hasCourse.value ? 'locked' : hasDocuments.value ? 'done' : 'current'
  },
  {
    title: '等待解析完成',
    detail: hasSearchableDocuments.value
      ? '已有资料可用于知识库检索。'
      : hasProcessingDocuments.value
        ? '资料正在解析，完成后即可提问。'
        : '解析完成后会生成 chunks 并进入向量库。',
    status: !hasDocuments.value ? 'locked' : hasSearchableDocuments.value ? 'done' : 'current'
  },
  {
    title: '提出第一个问题',
    detail: hasAsked.value ? `已有 ${sessions.value.length} 个问答会话。` : '先围绕课程重点提一个具体问题。',
    status: !hasSearchableDocuments.value ? 'locked' : hasAsked.value ? 'done' : 'current'
  },
  {
    title: '生成卡片或试题',
    detail: hasStudyAssets.value ? `已有 ${cards.value.length + questions.value.length} 条学习资产。` : '把资料和问答沉淀成复习材料。',
    status: !hasSearchableDocuments.value ? 'locked' : hasStudyAssets.value ? 'done' : 'current'
  },
  {
    title: '完成一次复习',
    detail: hasReviewed.value ? '已更新卡片掌握度。' : '用 + / - 调整卡片掌握度，记录真实记忆状态。',
    status: !hasStudyAssets.value ? 'locked' : hasReviewed.value ? 'done' : 'current'
  },
  {
    title: '查看薄弱点',
    detail: hasReviewed.value ? '继续查看低掌握度卡片和最近错题。' : '完成复习后，再回到进度面板定位薄弱点。',
    status: hasReviewed.value ? 'current' : 'locked'
  }
])

watch(
  () => [store.selectedCourseId, store.progressRefreshKey],
  () => {
    void loadWorkflowState()
  },
  { immediate: true }
)

async function loadWorkflowState() {
  error.value = ''
  if (!store.selectedCourseId) {
    documents.value = []
    sessions.value = []
    cards.value = []
    questions.value = []
    return
  }
  loading.value = true
  try {
    const [nextDocuments, nextSessions, nextCards, nextQuestions] = await Promise.all([
      api.listDocuments(store.selectedCourseId),
      api.listChatSessions(store.selectedCourseId),
      api.listStudyCards(store.selectedCourseId),
      api.listGeneratedQuestions(store.selectedCourseId)
    ])
    documents.value = nextDocuments
    sessions.value = nextSessions
    cards.value = nextCards
    questions.value = nextQuestions
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AppPanel title="学习闭环" panel-class="workflow-panel">
    <template #icon>
      <CheckCircle2 :size="20" />
    </template>
    <template #actions>
      <button class="icon-button" type="button" title="刷新学习闭环" :disabled="loading" @click="loadWorkflowState">
        <RefreshCw :size="16" />
      </button>
    </template>
    <ol class="workflow-list">
      <li v-for="step in steps" :key="step.title" class="workflow-step" :class="step.status">
        <CheckCircle2 v-if="step.status === 'done'" :size="18" />
        <Circle v-else :size="18" />
        <span>
          <strong>{{ step.title }}</strong>
          <small>{{ step.detail }}</small>
        </span>
      </li>
    </ol>
    <p v-if="error" class="inline-error">{{ error }}</p>
  </AppPanel>
</template>
