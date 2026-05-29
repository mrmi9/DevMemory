export interface Course {
  id: string
  title: string
  description: string
  color: string
}

export interface DocumentItem {
  id: string
  course_id: string
  title: string
  original_filename: string
  kind: string
  status: string
  error_message: string
  chapter?: string
  tags?: string[]
  text_preview: string
  created_at: string
  updated_at: string
  chunk_count: number
  latest_job: {
    id: string
    status: string
    progress: number
    error_message: string
  } | null
}

export interface DocumentChunk {
  id: number
  chunk_index: number
  text: string
  token_count: number
  page_number: number | null
  char_start: number
  char_end: number
}

export interface DocumentJob {
  id: string
  document_id: string
  job_type: string
  status: string
  progress: number
  error_message: string
}

export interface ChatResponse {
  answer: string
  citations: Array<{
    chunk_id: number
    document_id: string
    document_title: string
    course_title: string
    text_preview: string
    page_number: number | null
    similarity: number
  }>
  session_id: string
  assistant_message_id?: string
  retrieval_confidence?: string
  quality_notes?: string[]
}

export interface ChatSession {
  id: string
  course_id: string | null
  title: string
  created_at: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations: ChatResponse['citations']
  created_at: string
}

export interface WrongNote {
  id: string
  course_id: string | null
  title: string
  original_question: string
  user_answer: string
  correct_answer: string
  analysis: string
  tags: string[]
  created_at: string
}

export interface StudyCard {
  id: string
  course_id: string | null
  front: string
  back: string
  source: string
  mastery: number
  review_count?: number
  last_reviewed_at?: string | null
  next_review_at?: string | null
  created_at: string
}

export interface GeneratedQuestion {
  id: string
  course_id: string | null
  question_type: string
  prompt: string
  answer: string
  explanation: string
  created_at: string
}

export interface Mindmap {
  id: string
  course_id: string | null
  title: string
  markdown: string
  created_at: string
}

export interface SystemStatus {
  status: 'ok' | 'degraded'
  environment: string
  ai_mode: 'online' | 'offline_placeholder'
  checks: {
    deepseek?: {
      configured: boolean
      mode?: string
      model?: string
      base_url?: string
    }
    [key: string]: unknown
  }
}

export interface ReviewCard extends StudyCard {
  review_state: 'not_started' | 'needs_reinforcement' | 'mastered'
  next_review_label: string
}

export interface ProgressOverview {
  courses: number
  records: number
  average_mastery: number
  items: unknown[]
  review?: {
    today_due: number
    low_mastery: number
    mastered: number
    cards: ReviewCard[]
    recent_wrong_notes: WrongNote[]
  }
}

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api'

export class ApiClient {
  token = localStorage.getItem('study_token') ?? ''

  async login(username: string, password: string) {
    const data = await this.request<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    }, false)
    this.token = data.access_token
    localStorage.setItem('study_token', this.token)
  }

  logout() {
    this.token = ''
    localStorage.removeItem('study_token')
  }

  hasToken() {
    return Boolean(this.token)
  }

  async systemStatus() {
    return this.request<SystemStatus>('/system/status', {}, false)
  }

  async listCourses() {
    return this.request<Course[]>('/courses')
  }

  async createCourse(payload: { title: string; description: string; color: string }) {
    return this.request<Course>('/courses', { method: 'POST', body: JSON.stringify(payload) })
  }

  async deleteCourse(courseId: string) {
    return this.request<{ ok: boolean }>(`/courses/${courseId}`, { method: 'DELETE' })
  }

  async uploadDocument(courseId: string, file: File) {
    const body = new FormData()
    body.append('file', file)
    return this.request<DocumentItem>(`/courses/${courseId}/documents`, { method: 'POST', body })
  }

  async listDocuments(courseId: string) {
    return this.request<DocumentItem[]>(`/courses/${courseId}/documents`)
  }

  async getDocument(documentId: string) {
    return this.request<DocumentItem>(`/documents/${documentId}`)
  }

  async updateDocumentMetadata(documentId: string, payload: { chapter: string; tags: string[] }) {
    return this.request<DocumentItem>(`/documents/${documentId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    })
  }

  async listDocumentChunks(documentId: string) {
    return this.request<DocumentChunk[]>(`/documents/${documentId}/chunks`)
  }

  async listDocumentJobs(documentId: string) {
    return this.request<DocumentJob[]>(`/documents/${documentId}/jobs`)
  }

  async retryDocument(documentId: string) {
    return this.request<DocumentItem>(`/documents/${documentId}/retry`, { method: 'POST', body: JSON.stringify({}) })
  }

  async deleteDocument(documentId: string) {
    return this.request<{ ok: boolean }>(`/documents/${documentId}`, { method: 'DELETE' })
  }

  async saveChatMessageAsStudyCard(messageId: string) {
    return this.request<StudyCard>(`/chat/messages/${messageId}/study-card`, {
      method: 'POST',
      body: JSON.stringify({})
    })
  }

  async generateQuestionsFromChatMessage(messageId: string, count = 5) {
    return this.request<GeneratedQuestion[]>(`/chat/messages/${messageId}/study-questions`, {
      method: 'POST',
      body: JSON.stringify({ count })
    })
  }

  async addChatMessageToWrongNotes(messageId: string) {
    return this.request<WrongNote>(`/chat/messages/${messageId}/wrong-note`, {
      method: 'POST',
      body: JSON.stringify({})
    })
  }

  async ask(question: string, courseId?: string, sessionId?: string, documentIds: string[] = []) {
    return this.request<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify({ question, course_id: courseId || null, session_id: sessionId || null, document_ids: documentIds })
    })
  }

  async generate(path: '/study/cards' | '/study/questions' | '/mindmaps', topic: string, courseId?: string) {
    return this.request<{ content: string }>(path, {
      method: 'POST',
      body: JSON.stringify({ topic, course_id: courseId || null, document_ids: [], count: 8 })
    })
  }

  async generateMindmap(topic: string, courseId?: string) {
    return this.generate('/mindmaps', topic, courseId)
  }

  async listMindmaps(courseId?: string) {
    const query = courseId ? `?course_id=${encodeURIComponent(courseId)}` : ''
    return this.request<Mindmap[]>(`/mindmaps${query}`)
  }

  async deleteMindmap(mindmapId: string) {
    return this.request<{ ok: boolean }>(`/mindmaps/${mindmapId}`, { method: 'DELETE' })
  }

  async listStudyCards(courseId?: string) {
    const query = courseId ? `?course_id=${encodeURIComponent(courseId)}` : ''
    return this.request<StudyCard[]>(`/study/cards${query}`)
  }

  async updateStudyCardMastery(cardId: string, mastery: number) {
    return this.updateStudyCard(cardId, { mastery })
  }

  async updateStudyCard(cardId: string, payload: { front?: string; back?: string; mastery?: number }) {
    return this.request<StudyCard>(`/study/cards/${cardId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    })
  }

  async deleteStudyCard(cardId: string) {
    return this.request<{ ok: boolean }>(`/study/cards/${cardId}`, { method: 'DELETE' })
  }

  async listGeneratedQuestions(courseId?: string) {
    const query = courseId ? `?course_id=${encodeURIComponent(courseId)}` : ''
    return this.request<GeneratedQuestion[]>(`/study/questions${query}`)
  }

  async updateGeneratedQuestion(questionId: string, payload: { prompt?: string; answer?: string; explanation?: string }) {
    return this.request<GeneratedQuestion>(`/study/questions/${questionId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    })
  }

  async deleteGeneratedQuestion(questionId: string) {
    return this.request<{ ok: boolean }>(`/study/questions/${questionId}`, { method: 'DELETE' })
  }

  async addGeneratedQuestionToWrongNotes(questionId: string) {
    return this.request<WrongNote>(`/study/questions/${questionId}/wrong-note`, {
      method: 'POST',
      body: JSON.stringify({})
    })
  }

  async addWrongNote(payload: {
    course_id?: string
    title: string
    original_question: string
    user_answer: string
    correct_answer: string
  }) {
    return this.request<{ content: string }>('/study/wrong-notes', {
      method: 'POST',
      body: JSON.stringify({ ...payload, course_id: payload.course_id || null })
    })
  }

  async listWrongNotes(courseId?: string) {
    const query = courseId ? `?course_id=${encodeURIComponent(courseId)}` : ''
    return this.request<WrongNote[]>(`/study/wrong-notes${query}`)
  }

  async deleteWrongNote(noteId: string) {
    return this.request<{ ok: boolean }>(`/study/wrong-notes/${noteId}`, { method: 'DELETE' })
  }

  async progressOverview() {
    return this.request<ProgressOverview>('/progress/overview')
  }

  async listChatSessions(courseId?: string) {
    const query = courseId ? `?course_id=${encodeURIComponent(courseId)}` : ''
    return this.request<ChatSession[]>(`/chat/sessions${query}`)
  }

  async updateChatSession(sessionId: string, title: string) {
    return this.request<ChatSession>(`/chat/sessions/${sessionId}`, {
      method: 'PATCH',
      body: JSON.stringify({ title })
    })
  }

  async deleteChatSession(sessionId: string) {
    return this.request<{ ok: boolean }>(`/chat/sessions/${sessionId}`, { method: 'DELETE' })
  }

  async listChatMessages(sessionId: string) {
    return this.request<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`)
  }

  private async request<T>(path: string, init: RequestInit = {}, authenticated = true): Promise<T> {
    const headers = new Headers(init.headers)
    if (!(init.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json')
    }
    if (authenticated && this.token) {
      headers.set('Authorization', `Bearer ${this.token}`)
    }
    const response = await fetch(`${API_BASE}${path}`, { ...init, headers })
    if (!response.ok) {
      const message = await response.text()
      throw new Error(this.formatError(message, response.status))
    }
    return response.json() as Promise<T>
  }

  private formatError(message: string, status: number) {
    if (!message) return `HTTP ${status}`
    const trimmedMessage = message.trim()
    try {
      const payload = JSON.parse(trimmedMessage) as { detail?: unknown }
      if (typeof payload.detail === 'string') return payload.detail
      if (Array.isArray(payload.detail)) {
        return payload.detail
          .map((item) => {
            if (item && typeof item === 'object' && 'msg' in item && typeof item.msg === 'string') {
              return item.msg
            }
            return '请求参数有误'
          })
          .join('；')
      }
    } catch {
      if (this.isHtmlError(trimmedMessage)) {
        if ([502, 503, 504].includes(status)) return '服务暂时不可用，请稍后重试'
        return `请求失败，服务返回了异常页面（HTTP ${status}）`
      }
      return trimmedMessage
    }
    return trimmedMessage
  }

  private isHtmlError(message: string) {
    return /^<!doctype html/i.test(message) || /^<html[\s>]/i.test(message)
  }
}

export const api = new ApiClient()
