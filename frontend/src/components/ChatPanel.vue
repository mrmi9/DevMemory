<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { MessageSquare, Pencil, RefreshCw, Send, Trash2 } from 'lucide-vue-next'
import { api, type ChatResponse, type ChatSession, type DocumentItem } from '../api'
import { useStudyStore } from '../stores/study'

const store = useStudyStore()
const question = ref('帮我总结 SNMP 协议考试重点')
const result = ref<ChatResponse | null>(null)
const busy = ref(false)
const sessionBusy = ref('')
const error = ref('')
const sessionId = ref('')
const sessionSearch = ref('')
const messages = ref<Array<{ role: 'user' | 'assistant'; content: string; citations?: ChatResponse['citations'] }>>([])
const sessions = ref<ChatSession[]>([])
const documents = ref<DocumentItem[]>([])
const selectedDocumentIds = ref<Set<string>>(new Set())
const citedDocument = ref<DocumentItem | null>(null)
const citationPreview = ref('')

const filteredSessions = computed(() => {
  const keyword = sessionSearch.value.trim().toLowerCase()
  if (!keyword) return sessions.value
  return sessions.value.filter((session) => session.title.toLowerCase().includes(keyword))
})
const selectedAskDocumentIds = computed(() => documents.value.filter((document) => selectedDocumentIds.value.has(document.id)).map((document) => document.id))

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

async function loadDocuments() {
  if (!store.selectedCourseId) {
    documents.value = []
    selectedDocumentIds.value = new Set()
    return
  }
  try {
    documents.value = await api.listDocuments(store.selectedCourseId)
    selectedDocumentIds.value = new Set([...selectedDocumentIds.value].filter((id) => documents.value.some((document) => document.id === id)))
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught)
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

async function renameSession(session: ChatSession) {
  const nextTitle = window.prompt('输入新的会话标题', session.title)?.trim()
  if (!nextTitle || nextTitle === session.title) return
  sessionBusy.value = `rename:${session.id}`
  error.value = ''
  try {
    const updated = await api.updateChatSession(session.id, nextTitle)
    sessions.value = sessions.value.map((item) => (item.id === updated.id ? updated : item))
    sessionSearch.value = ''
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught)
  } finally {
    sessionBusy.value = ''
  }
}

async function deleteSession(session: ChatSession) {
  if (!window.confirm(`确定删除“${session.title}”吗？该会话历史也会被删除。`)) return
  sessionBusy.value = `delete:${session.id}`
  error.value = ''
  try {
    await api.deleteChatSession(session.id)
    sessions.value = sessions.value.filter((item) => item.id !== session.id)
    if (sessionId.value === session.id) {
      startNewSession()
    }
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught)
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
    messages.value.push({ role: 'assistant', content: result.value.answer, citations: result.value.citations })
    await loadSessions()
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught)
    messages.value = messages.value.filter((message) => message.content !== currentQuestion || message.role !== 'user')
  } finally {
    busy.value = false
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
          @click.stop="renameSession(session)"
        >
          <Pencil :size="14" />
        </button>
        <button
          class="icon-button danger-icon-button session-action-button"
          type="button"
          title="删除会话"
          :disabled="!!sessionBusy"
          @click.stop="deleteSession(session)"
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
    <button data-testid="ask-button" @click="ask" :disabled="busy">
      <Send :size="18" />
      <span>{{ busy ? '检索中' : '提问' }}</span>
    </button>
    <p v-if="error" class="inline-error">{{ error }}</p>
    <div v-if="messages.length" class="chat-history">
      <article v-for="(message, index) in messages" :key="index" class="chat-message" :class="message.role">
        <strong>{{ message.role === 'user' ? '我' : 'AI 助手' }}</strong>
        <pre>{{ message.content }}</pre>
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
          <span v-if="!message.citations?.length" class="neutral">没有检索到引用资料</span>
        </div>
      </article>
      <aside v-if="citedDocument" class="citation-detail">
        <strong>{{ citedDocument.title }}</strong>
        <small>{{ citedDocument.kind }} · {{ citedDocument.chunk_count }} chunks</small>
        <p>{{ citedDocument.text_preview || citationPreview }}</p>
      </aside>
      <div v-if="sessionId" class="muted">会话已保存：{{ sessionId }}</div>
    </div>
    <article v-else class="answer">
      <pre>选择课程并上传资料后，可以直接提问，例如：帮我总结 SNMP 协议考试重点。</pre>
    </article>
  </section>
</template>
