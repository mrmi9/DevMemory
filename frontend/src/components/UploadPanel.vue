<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { FileText, FileUp, RefreshCw, RotateCcw, Trash2 } from 'lucide-vue-next'
import { api, type DocumentChunk, type DocumentItem, type DocumentJob } from '../api'
import { useStudyStore } from '../stores/study'

const store = useStudyStore()
const documents = ref<DocumentItem[]>([])
const selectedDocument = ref<DocumentItem | null>(null)
const selectedDocumentIds = ref<Set<string>>(new Set())
const chunks = ref<DocumentChunk[]>([])
const jobs = ref<DocumentJob[]>([])
const message = ref('')
const loading = ref(false)
const detailLoading = ref(false)
const deleting = ref(false)
let refreshTimer: ReturnType<typeof setInterval> | undefined

const hasProcessingDocuments = computed(() =>
  documents.value.some((document) => ['uploaded', 'processing'].includes(document.status) || document.latest_job?.status === 'queued')
)
const selectedDocuments = computed(() => documents.value.filter((document) => selectedDocumentIds.value.has(document.id)))
const helperMessage = computed(() => {
  if (message.value) return message.value
  if (!store.selectedCourseId) return '请先登录并选择课程，再上传资料。'
  if (loading.value) return '正在读取资料列表...'
  if (documents.value.length) return '选择资料可查看解析预览、chunks，或删除不再需要的文档。'
  return '上传后会自动解析、分块并写入向量库。'
})

watch(
  () => store.selectedCourseId,
  () => {
    void loadDocuments()
  },
  { immediate: true }
)

refreshTimer = setInterval(() => {
  if (store.selectedCourseId && hasProcessingDocuments.value) {
    void loadDocuments(false)
  }
}, 4000)

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})

async function loadDocuments(showLoading = true) {
  if (!store.selectedCourseId) {
    documents.value = []
    selectedDocument.value = null
    selectedDocumentIds.value = new Set()
    chunks.value = []
    jobs.value = []
    return
  }
  if (showLoading) loading.value = true
  try {
    documents.value = await api.listDocuments(store.selectedCourseId)
    selectedDocumentIds.value = new Set([...selectedDocumentIds.value].filter((id) => documents.value.some((document) => document.id === id)))
    if (selectedDocument.value) {
      selectedDocument.value = documents.value.find((document) => document.id === selectedDocument.value?.id) ?? null
      if (!selectedDocument.value) {
        chunks.value = []
        jobs.value = []
      }
    }
  } catch (error) {
    message.value = error instanceof Error ? error.message : String(error)
  } finally {
    loading.value = false
  }
}

function toggleDocumentSelection(documentId: string, checked: boolean) {
  const nextSelectedIds = new Set(selectedDocumentIds.value)
  if (checked) {
    nextSelectedIds.add(documentId)
  } else {
    nextSelectedIds.delete(documentId)
  }
  selectedDocumentIds.value = nextSelectedIds
}

async function deleteSelectedDocuments() {
  const targets = selectedDocuments.value
  if (!targets.length) return
  const confirmed = window.confirm(`确定删除选中的 ${targets.length} 份资料吗？删除后会从知识库检索中移除。`)
  if (!confirmed) return
  deleting.value = true
  message.value = `正在删除 ${targets.length} 份资料...`
  try {
    await Promise.all(targets.map((document) => api.deleteDocument(document.id)))
    const deletedIds = new Set(targets.map((document) => document.id))
    documents.value = documents.value.filter((document) => !deletedIds.has(document.id))
    selectedDocumentIds.value = new Set()
    if (selectedDocument.value && deletedIds.has(selectedDocument.value.id)) {
      selectedDocument.value = null
      chunks.value = []
      jobs.value = []
    }
    message.value = `已删除 ${targets.length} 份资料`
  } catch (error) {
    message.value = error instanceof Error ? error.message : String(error)
  } finally {
    deleting.value = false
  }
}

async function selectDocument(document: DocumentItem) {
  selectedDocument.value = document
  chunks.value = []
  jobs.value = []
  detailLoading.value = true
  try {
    const [nextChunks, nextJobs] = await Promise.all([
      api.listDocumentChunks(document.id),
      api.listDocumentJobs(document.id)
    ])
    chunks.value = nextChunks
    jobs.value = nextJobs
  } catch (error) {
    message.value = error instanceof Error ? error.message : String(error)
  } finally {
    detailLoading.value = false
  }
}

async function retrySelectedDocument() {
  if (!selectedDocument.value) return
  message.value = '已重新加入解析队列...'
  try {
    selectedDocument.value = await api.retryDocument(selectedDocument.value.id)
    await loadDocuments(false)
  } catch (error) {
    message.value = error instanceof Error ? error.message : String(error)
  }
}

async function deleteSelectedDocument() {
  if (!selectedDocument.value) return
  const document = selectedDocument.value
  const confirmed = window.confirm(`确定删除“${document.title}”吗？删除后会从知识库检索中移除。`)
  if (!confirmed) return
  deleting.value = true
  message.value = '正在删除资料...'
  try {
    await api.deleteDocument(document.id)
    documents.value = documents.value.filter((item) => item.id !== document.id)
    selectedDocumentIds.value = new Set([...selectedDocumentIds.value].filter((id) => id !== document.id))
    selectedDocument.value = null
    chunks.value = []
    jobs.value = []
    message.value = '资料已删除'
  } catch (error) {
    message.value = error instanceof Error ? error.message : String(error)
  } finally {
    deleting.value = false
  }
}

async function upload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file || !store.selectedCourseId) return
  message.value = '上传中...'
  try {
    const document = await api.uploadDocument(store.selectedCourseId, file)
    documents.value.unshift(document)
    message.value = '已上传，Worker 会继续解析和向量化'
    await loadDocuments(false)
  } catch (error) {
    message.value = error instanceof Error ? error.message : String(error)
  } finally {
    input.value = ''
  }
}

function statusLabel(document: DocumentItem) {
  const status = document.latest_job?.status || document.status
  const labels: Record<string, string> = {
    uploaded: '已上传',
    queued: '排队中',
    processing: '解析中',
    succeeded: '已入库',
    ready: '已入库',
    failed: '失败'
  }
  return labels[status] ?? status
}

function statusClass(document: DocumentItem) {
  const status = document.latest_job?.status || document.status
  if (status === 'failed') return 'danger'
  if (status === 'succeeded' || document.status === 'ready') return 'success'
  return 'working'
}

function jobStatusClass(job: DocumentJob) {
  if (job.status === 'failed') return 'danger'
  if (job.status === 'succeeded') return 'success'
  return 'working'
}
</script>

<template>
  <section class="panel">
    <header class="panel-header">
      <FileUp :size="20" />
      <h2>课程资料库</h2>
      <button class="icon-button" type="button" title="刷新资料状态" :disabled="!store.selectedCourseId || loading" @click="loadDocuments()">
        <RefreshCw :size="16" />
      </button>
    </header>
    <label class="upload-zone" :class="{ disabled: !store.selectedCourseId }">
      <input
        type="file"
        accept=".pdf,.docx,.md,.markdown,.png,.jpg,.jpeg,.webp"
        :disabled="!store.selectedCourseId"
        @change="upload"
      />
      <span>{{ store.selectedCourseId ? '选择 PDF、Word、Markdown 或图片笔记' : '选择课程后即可上传资料' }}</span>
    </label>
    <p class="muted">{{ helperMessage }}</p>
    <div v-if="documents.length" class="document-bulk-actions">
      <span>{{ selectedDocuments.length }} 份已选</span>
      <button
        class="danger-button"
        type="button"
        title="批量删除资料"
        :disabled="deleting || !selectedDocuments.length"
        @click="deleteSelectedDocuments"
      >
        <Trash2 :size="16" />
        <span>{{ deleting && selectedDocuments.length ? '删除中' : '批量删除' }}</span>
      </button>
    </div>
    <ul class="document-list">
      <li
        v-for="document in documents"
        :key="document.id"
        class="document-row"
        :class="{ active: selectedDocument?.id === document.id }"
        @click="selectDocument(document)"
      >
        <div class="document-title">
          <input
            data-testid="document-select"
            type="checkbox"
            :checked="selectedDocumentIds.has(document.id)"
            :disabled="deleting"
            @click.stop
            @change="toggleDocumentSelection(document.id, ($event.target as HTMLInputElement).checked)"
          />
          <FileText :size="17" />
          <strong>{{ document.title }}</strong>
        </div>
        <div class="document-meta">
          <span class="status-pill" :class="statusClass(document)">{{ statusLabel(document) }}</span>
          <span>{{ document.kind }}</span>
          <span>{{ document.chunk_count }} chunks</span>
          <span v-if="document.latest_job">任务 {{ document.latest_job.progress }}%</span>
        </div>
        <p v-if="document.text_preview" class="document-snippet">{{ document.text_preview }}</p>
        <p v-if="document.error_message || document.latest_job?.error_message" class="inline-error">
          {{ document.error_message || document.latest_job?.error_message }}
        </p>
      </li>
      <li v-if="!documents.length && !loading" class="empty-row">
        {{ store.selectedCourseId ? '当前课程还没有资料，先上传一份笔记试试。' : '登录并选择课程后，这里会显示资料列表。' }}
      </li>
    </ul>
    <aside v-if="selectedDocument" class="document-detail">
      <header class="detail-header">
        <div>
          <strong>{{ selectedDocument.title }}</strong>
          <small>{{ selectedDocument.kind }} · {{ selectedDocument.chunk_count }} chunks · {{ statusLabel(selectedDocument) }}</small>
        </div>
        <div class="detail-actions">
          <button
            v-if="selectedDocument.status === 'failed' || selectedDocument.latest_job?.status === 'failed'"
            type="button"
            :disabled="deleting"
            @click="retrySelectedDocument"
          >
            <RotateCcw :size="16" />
            <span>重试</span>
          </button>
          <button class="danger-button" type="button" :disabled="deleting" @click="deleteSelectedDocument">
            <Trash2 :size="16" />
            <span>{{ deleting ? '删除中' : '删除' }}</span>
          </button>
        </div>
      </header>
      <div class="document-preview">
        <strong>解析预览</strong>
        <pre>{{ selectedDocument.text_preview || '暂无解析文本，等待 Worker 处理。' }}</pre>
      </div>
      <div class="chunk-list">
        <strong>{{ detailLoading ? '读取 chunks...' : `Chunks (${chunks.length})` }}</strong>
        <article v-for="chunk in chunks.slice(0, 5)" :key="chunk.id" class="chunk-row">
          <small>#{{ chunk.chunk_index }} · {{ chunk.token_count }} tokens</small>
          <p>{{ chunk.text }}</p>
        </article>
      </div>
      <div class="job-history">
        <strong>任务历史</strong>
        <article v-for="job in jobs" :key="job.id" class="job-row">
          <div>
            <span class="status-pill" :class="jobStatusClass(job)">{{ job.status }}</span>
            <small>{{ job.id }} 路 {{ job.job_type }} 路 {{ job.progress }}%</small>
          </div>
          <p v-if="job.error_message" class="inline-error">{{ job.error_message }}</p>
        </article>
        <p v-if="!jobs.length && !detailLoading" class="muted">暂无任务历史</p>
      </div>
    </aside>
  </section>
</template>
