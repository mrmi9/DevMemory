<script setup lang="ts">
import { ref, watch } from 'vue'
import { MessageSquare, RefreshCw, Send } from 'lucide-vue-next'
import { api, type ChatResponse, type ChatSession } from '../api'
import { useStudyStore } from '../stores/study'

const store = useStudyStore()
const question = ref('帮我总结 SNMP 协议考试重点')
const result = ref<ChatResponse | null>(null)
const busy = ref(false)
const error = ref('')
const sessionId = ref('')
const messages = ref<Array<{ role: 'user' | 'assistant'; content: string; citations?: ChatResponse['citations'] }>>([])
const sessions = ref<ChatSession[]>([])

watch(
  () => store.selectedCourseId,
  () => {
    sessionId.value = ''
    messages.value = []
    void loadSessions()
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

async function openSession(session: ChatSession) {
  sessionId.value = session.id
  error.value = ''
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
}

async function ask() {
  const currentQuestion = question.value.trim()
  if (!currentQuestion) return
  busy.value = true
  error.value = ''
  try {
    messages.value.push({ role: 'user', content: currentQuestion })
    result.value = await api.ask(currentQuestion, store.selectedCourseId, sessionId.value)
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
    <div class="session-list">
      <button type="button" :class="{ active: !sessionId }" @click="startNewSession">新会话</button>
      <button
        v-for="session in sessions"
        :key="session.id"
        type="button"
        :class="{ active: session.id === sessionId }"
        @click="openSession(session)"
      >
        {{ session.title }}
      </button>
    </div>
    <textarea v-model="question" rows="4" placeholder="输入你的问题"></textarea>
    <button @click="ask" :disabled="busy">
      <Send :size="18" />
      <span>{{ busy ? '检索中' : '提问' }}</span>
    </button>
    <p v-if="error" class="inline-error">{{ error }}</p>
    <div v-if="messages.length" class="chat-history">
      <article v-for="(message, index) in messages" :key="index" class="chat-message" :class="message.role">
        <strong>{{ message.role === 'user' ? '我' : 'AI 助手' }}</strong>
        <pre>{{ message.content }}</pre>
        <div v-if="message.role === 'assistant'" class="citation-strip">
          <span v-for="citation in message.citations" :key="citation.chunk_id">
            {{ citation.document_title }} · 相似度 {{ citation.similarity.toFixed(2) }}
          </span>
          <span v-if="!message.citations?.length" class="neutral">没有检索到引用资料</span>
        </div>
      </article>
      <div v-if="sessionId" class="muted">会话已保存：{{ sessionId }}</div>
    </div>
    <article v-else class="answer">
      <pre>选择课程并上传资料后，可以直接提问，例如：帮我总结 SNMP 协议考试重点。</pre>
    </article>
  </section>
</template>
