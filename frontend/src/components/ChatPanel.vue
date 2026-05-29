<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { ClipboardList, FileText, Layers, MessageSquare, NotebookPen, Pencil, RefreshCw, Send, Trash2 } from 'lucide-vue-next'
import AppModal from './AppModal.vue'
import { api, type ChatResponse, type ChatSession, type DocumentItem } from '../api'
import { useStudyStore } from '../stores/study'

const store = useStudyStore()
const question = ref('帮我总结 SNMP 协议考试重点')
const result = ref<ChatResponse | null>(null)
const busy = ref(false)
const sessionBusy = ref('')
const assetBusy = ref('')
const assetMessages = ref<string[]>([])
const error = ref('')
const sessionId = ref('')
const sessionSearch = ref('')
const messages = ref<Array<{
  id?: string
  role: 'user' | 'assistant'
  content: string
  citations?: ChatResponse['citations']
  retrieval_confidence?: string
  quality_notes?: string[]
}>>([])
const sessions = ref<ChatSession[]>([])
const documents = ref<DocumentItem[]>([])
const selectedDocumentIds = ref<Set<string>>(new Set())
const citedDocument = ref<DocumentItem | null>(null)
const citationPreview = ref('')
const sessionPendingRename = ref<ChatSession | null>(null)
const sessionRenameTitle = ref('')
const sessionPendingDelete = ref<ChatSession | null>(null)
const modalError = ref('')
let refreshTimer: ReturnType<typeof setInterval> | undefined

const filteredSessions = computed(() => {
  const keyword = sessionSearch.value.trim().toLowerCase()
  if (!keyword) return sessions.value
  return sessions.value.filter((session) => session.title.toLowerCase().includes(keyword))
})
const selectedAskDocumentIds = computed(() => documents.value.filter((document) => selectedDocumentIds.value.has(document.id)).map((document) => document.id))
const hasProcessingDocuments = computed(() => documents.value.some(isProcessingDocument))
const searchableDocuments = computed(() => documents.value.filter(isSearchableDocument))
const askDisabled = computed(() => busy.value || !store.selectedCourseId || !searchableDocuments.value.length)
const emptyAnswerTitle = computed(() => {
  if (!store.selectedCourseId) return '先创建或选择课程'
  if (!searchableDocuments.value.length) return '还没有可检索资料'
  return '开始一次课程问答'
})
const emptyAnswerDetail = computed(() => {
  if (!store.selectedCourseId) return '登录后创建课程，DevMemory 会把后续资料、问答和复习内容归档到课程下。'
  if (!searchableDocuments.value.length) return '先在课程资料库上传并等待解析完成，再向知识库提问。'
  return '选择课程并上传资料后，可以直接提问，例如：帮我总结 SNMP 协议考试重点。'
})

watch(
  () => store.selectedCourseId,
  () => {
    sessionId.value = ''
    messages.value = []
    citedDocument.value = null
    citationPreview.value = ''
    void loadSessions()
    void loadDocuments()
  },
  { immediate: true }
)

watch(
  () => store.progressRefreshKey,
  () => {
    void loadDocuments(false)
  }
)

refreshTimer = setInterval(() => {
  if (store.selectedCourseId && hasProcessingDocuments.value) {
    void loadDocuments(false)
  }
}, 4000)

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})

function documentRuntimeStatus(document: DocumentItem) {
  return document.latest_job?.status || document.status
}

function isFailedDocument(document: DocumentItem) {
  return document.status === 'failed' || document.latest_job?.status === 'failed'
}

function isProcessingDocument(document: DocumentItem) {
  return ['uploaded', 'processing', 'queued'].includes(documentRuntimeStatus(document))
}

function isSearchableDocument(document: DocumentItem) {
  return document.chunk_count > 0 && !isFailedDocument(document) && !isProcessingDocument(document)
}

async function loadSessions() {
  if (!store.selectedCourseId) {
    sessions.value = []
    return
  }
  try {
    sessions.value = await api.listChatSessions(store.selectedCourseId)
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught)
  }
}

async function loadDocuments(reportErrors = true) {
  if (!store.selectedCourseId) {
    documents.value = []
    selectedDocumentIds.value = new Set()
    return
  }
  try {
    documents.value = await api.listDocuments(store.selectedCourseId)
    selectedDocumentIds.value = new Set([...selectedDocumentIds.value].filter((id) => documents.value.some((document) => document.id === id)))
  } catch (caught) {
    if (reportErrors) {
      error.value = caught instanceof Error ? caught.message : String(caught)
    }
  }
}

function toggleDocumentFilter(documentId: string, checked: boolean) {
  const nextSelected = new Set(selectedDocumentIds.value)
  if (checked) {
    nextSelected.add(documentId)
  } else {
    nextSelected.delete(documentId)
  }
  selectedDocumentIds.value = nextSelected
}

async function openSession(session: ChatSession) {
  sessionId.value = session.id
  error.value = ''
  citedDocument.value = null
  citationPreview.value = ''
  try {
    const loaded = await api.listChatMessages(session.id)
    messages.value = loaded.map((message) => ({
      id: message.id,
      role: message.role,
      content: message.content,
      citations: message.citations
    }))
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught)
  }
}

function startNewSession() {
  sessionId.value = ''
  messages.value = []
  citedDocument.value = null
  citationPreview.value = ''
}

function requestRenameSession(session: ChatSession) {
  sessionPendingRename.value = session
  sessionRenameTitle.value = session.title
  modalError.value = ''
}

async function confirmRenameSession() {
  if (!sessionPendingRename.value) return
  const nextTitle = sessionRenameTitle.value.trim()
  if (!nextTitle) {
    modalError.value = '会话标题不能为空'
    return
  }
  if (nextTitle === sessionPendingRename.value.title) {
    sessionPendingRename.value = null
    return
  }
  const session = sessionPendingRename.value
  sessionBusy.value = `rename:${session.id}`
  error.value = ''
  modalError.value = ''
  try {
    const updated = await api.updateChatSession(session.id, nextTitle)
    sessions.value = sessions.value.map((item) => (item.id === updated.id ? updated : item))
    sessionSearch.value = ''
    sessionPendingRename.value = null
  } catch (caught) {
    modalError.value = caught instanceof Error ? caught.message : String(caught)
    error.value = modalError.value
  } finally {
    sessionBusy.value = ''
  }
}

function requestDeleteSession(session: ChatSession) {
  sessionPendingDelete.value = session
  modalError.value = ''
}

async function confirmDeleteSession() {
  if (!sessionPendingDelete.value) return
  const session = sessionPendingDelete.value
  sessionBusy.value = `delete:${session.id}`
  error.value = ''
  modalError.value = ''
  try {
    await api.deleteChatSession(session.id)
    sessions.value = sessions.value.filter((item) => item.id !== session.id)
    if (sessionId.value === session.id) {
      startNewSession()
    }
    sessionPendingDelete.value = null
  } catch (caught) {
    modalError.value = caught instanceof Error ? caught.message : String(caught)
    error.value = modalError.value
  } finally {
    sessionBusy.value = ''
  }
}

async function ask() {
  const currentQuestion = question.value.trim()
  if (!currentQuestion) return
  busy.value = true
  error.value = ''
  citedDocument.value = null
  citationPreview.value = ''
  try {
    messages.value.push({ role: 'user', content: currentQuestion })
    result.value = await api.ask(currentQuestion, store.selectedCourseId, sessionId.value, selectedAskDocumentIds.value)
    sessionId.value = result.value.session_id
    messages.value.push({
      id: result.value.assistant_message_id,
      role: 'assistant',
      content: result.value.answer,
      citations: result.value.citations,
      retrieval_confidence: result.value.retrieval_confidence,
      quality_notes: result.value.quality_notes
    })
    await loadSessions()
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught)
    messages.value = messages.value.filter((message) => message.content !== currentQuestion || message.role !== 'user')
  } finally {
    busy.value = false
  }
}

function canCreateStudyAsset(message: { id?: string; role: string; citations?: ChatResponse['citations']; retrieval_confidence?: string }) {
  if (message.role !== 'assistant' || !message.id || !message.citations?.length) return false
  return !['weak', 'none'].includes(message.retrieval_confidence ?? '')
}

function canUseAnswerContext(message: { role: string; citations?: ChatResponse['citations'] }) {
  return message.role === 'assistant' && Boolean(message.citations?.length)
}

function startFollowUp(message: { content: string }) {
  question.value = `基于上面的回答，继续解释：${message.content.slice(0, 80)}`
}

function useCitedDocuments(message: { citations?: ChatResponse['citations'] }) {
  const ids = new Set((message.citations ?? []).map((citation) => citation.document_id))
  selectedDocumentIds.value = ids
  noteAssetMessage('已切换为只基于引用资料提问')
}

function noteAssetMessage(message: string) {
  assetMessages.value = [...assetMessages.value.filter((item) => item !== message), message].slice(-4)
}

async function saveAnswerAsCard(message: { id?: string }) {
  if (!message.id) return
  assetBusy.value = `card:${message.id}`
  try {
    await api.saveChatMessageAsStudyCard(message.id)
    noteAssetMessage('已保存为复习卡片')
    store.markProgressChanged()
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught)
  } finally {
    assetBusy.value = ''
  }
}

async function generateAnswerQuestions(message: { id?: string }) {
  if (!message.id) return
  assetBusy.value = `questions:${message.id}`
  try {
    const questions = await api.generateQuestionsFromChatMessage(message.id, 5)
    noteAssetMessage(`已生成 ${questions.length} 道练习题`)
    store.markProgressChanged()
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught)
  } finally {
    assetBusy.value = ''
  }
}

async function addAnswerToWrongNotes(message: { id?: string }) {
  if (!message.id) return
  assetBusy.value = `wrong:${message.id}`
  try {
    await api.addChatMessageToWrongNotes(message.id)
    noteAssetMessage('已加入重点')
    store.markProgressChanged()
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught)
  } finally {
    assetBusy.value = ''
  }
}

async function openCitation(citation: ChatResponse['citations'][number]) {
  error.value = ''
  citationPreview.value = citation.text_preview
  try {
    citedDocument.value = await api.getDocument(citation.document_id)
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught)
  }
}
</script>

<template>
  <section class="panel chat-panel">
    <header class="panel-header">
      <MessageSquare :size="20" />
      <h2>知识库问答</h2>
      <button class="icon-button" type="button" title="刷新会话" @click="loadSessions">
        <RefreshCw :size="16" />
      </button>
    </header>
    <input v-model="sessionSearch" placeholder="搜索历史会话" />
    <div class="session-list">
      <button type="button" :class="{ active: !sessionId }" @click="startNewSession">新会话</button>
      <div
        v-for="session in filteredSessions"
        :key="session.id"
        class="session-item"
        :class="{ active: session.id === sessionId }"
      >
        <button type="button" class="session-open-button" @click="openSession(session)">
          {{ session.title }}
        </button>
        <button
          class="icon-button session-action-button"
          type="button"
          title="重命名会话"
          :disabled="!!sessionBusy"
          @click.stop="requestRenameSession(session)"
        >
          <Pencil :size="14" />
        </button>
        <button
          class="icon-button danger-icon-button session-action-button"
          type="button"
          title="删除会话"
          :disabled="!!sessionBusy"
          @click.stop="requestDeleteSession(session)"
        >
          <Trash2 :size="14" />
        </button>
      </div>
    </div>
    <div v-if="documents.length" class="chat-document-filter">
      <span>资料范围</span>
      <label v-for="document in documents" :key="document.id" class="chat-document-filter-item">
        <input
          data-testid="chat-document-filter"
          type="checkbox"
          :checked="selectedDocumentIds.has(document.id)"
          @change="toggleDocumentFilter(document.id, ($event.target as HTMLInputElement).checked)"
        />
        <span>{{ document.title }}</span>
      </label>
    </div>
    <textarea v-model="question" rows="4" placeholder="输入你的问题"></textarea>
    <button data-testid="ask-button" @click="ask" :disabled="askDisabled">
      <Send :size="18" />
      <span>{{ busy ? '检索中' : '提问' }}</span>
    </button>
    <p v-if="error" class="inline-error">{{ error }}</p>
    <div v-if="messages.length" class="chat-history">
      <article v-for="(message, index) in messages" :key="index" class="chat-message" :class="message.role">
        <strong>{{ message.role === 'user' ? '我' : 'AI 助手' }}</strong>
        <pre>{{ message.content }}</pre>
        <div v-if="message.role === 'assistant' && message.retrieval_confidence" class="quality-strip">
          <span>检索置信度：{{ message.retrieval_confidence }}</span>
          <small v-for="note in message.quality_notes" :key="note">{{ note }}</small>
        </div>
        <div v-if="message.role === 'assistant'" class="citation-strip">
          <button
            v-for="citation in message.citations"
            :key="citation.chunk_id"
            class="citation-button"
            type="button"
            data-testid="citation-link"
            @click="openCitation(citation)"
          >
            <span>{{ citation.document_title }} · 相似度 {{ citation.similarity.toFixed(2) }}</span>
            <small>{{ citation.text_preview }}</small>
          </button>
          <span v-if="!message.citations?.length" class="neutral">资料不足，建议上传或选择更相关的资料</span>
        </div>
        <div v-if="canCreateStudyAsset(message)" class="answer-asset-actions">
          <button
            class="secondary-button"
            type="button"
            data-testid="save-answer-card"
            :disabled="!!assetBusy"
            @click="saveAnswerAsCard(message)"
          >
            <Layers :size="16" />
            <span>{{ assetBusy === `card:${message.id}` ? '保存中' : '保存为复习卡片' }}</span>
          </button>
          <button
            class="secondary-button"
            type="button"
            data-testid="generate-answer-questions"
            :disabled="!!assetBusy"
            @click="generateAnswerQuestions(message)"
          >
            <ClipboardList :size="16" />
            <span>{{ assetBusy === `questions:${message.id}` ? '生成中' : '生成 5 道练习题' }}</span>
          </button>
          <button
            class="secondary-button"
            type="button"
            data-testid="add-answer-wrong-note"
            :disabled="!!assetBusy"
            @click="addAnswerToWrongNotes(message)"
          >
            <NotebookPen :size="16" />
            <span>{{ assetBusy === `wrong:${message.id}` ? '加入中' : '加入错题/重点' }}</span>
          </button>
        </div>
        <div v-if="canUseAnswerContext(message)" class="answer-asset-actions">
          <button
            class="secondary-button"
            type="button"
            data-testid="follow-up-answer"
            @click="startFollowUp(message)"
          >
            <MessageSquare :size="16" />
            <span>基于这次回答继续追问</span>
          </button>
          <button
            class="secondary-button"
            type="button"
            data-testid="use-cited-documents"
            @click="useCitedDocuments(message)"
          >
            <FileText :size="16" />
            <span>只基于这些资料重新回答</span>
          </button>
        </div>
      </article>
      <div v-if="assetMessages.length" class="asset-message-list">
        <p v-for="message in assetMessages" :key="message" class="success-text">{{ message }}</p>
      </div>
      <aside v-if="citedDocument" class="citation-detail">
        <strong>{{ citedDocument.title }}</strong>
        <small>{{ citedDocument.kind }} · {{ citedDocument.chunk_count }} chunks</small>
        <p>{{ citedDocument.text_preview || citationPreview }}</p>
      </aside>
      <div v-if="sessionId" class="muted">会话已保存：{{ sessionId }}</div>
    </div>
    <article v-else class="answer empty-state">
      <strong>{{ emptyAnswerTitle }}</strong>
      <p>{{ emptyAnswerDetail }}</p>
    </article>
    <AppModal
      :open="!!sessionPendingRename"
      title="重命名会话"
      confirm-label="保存"
      :busy="sessionBusy.startsWith('rename:')"
      :error="modalError"
      @close="sessionPendingRename = null"
      @confirm="confirmRenameSession"
    >
      <label>
        <span>会话标题</span>
        <input v-model="sessionRenameTitle" data-testid="session-title-input" />
      </label>
    </AppModal>
    <AppModal
      :open="!!sessionPendingDelete"
      title="删除会话"
      confirm-label="删除会话"
      danger
      :busy="sessionBusy.startsWith('delete:')"
      :error="modalError"
      @close="sessionPendingDelete = null"
      @confirm="confirmDeleteSession"
    >
      <p>确定删除“{{ sessionPendingDelete?.title }}”吗？该会话历史也会被删除。</p>
    </AppModal>
  </section>
</template>
