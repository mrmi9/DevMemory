<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { Brain, ClipboardList, Layers, NotebookPen, Pencil, RefreshCw, Trash2 } from 'lucide-vue-next'
import AppModal from './AppModal.vue'
import AppPanel from './AppPanel.vue'
import { api, type GeneratedQuestion, type StudyCard, type WrongNote } from '../api'
import { useStudyStore } from '../stores/study'

const store = useStudyStore()
const topic = ref('')
const output = ref('')
const wrongQuestion = ref('')
const wrongAnswer = ref('')
const correctAnswer = ref('')
const busy = ref('')
const error = ref('')
const studyCards = ref<StudyCard[]>([])
const generatedQuestions = ref<GeneratedQuestion[]>([])
const wrongNotes = ref<WrongNote[]>([])
const cardPendingEdit = ref<StudyCard | null>(null)
const cardEditFront = ref('')
const cardEditBack = ref('')
const questionPendingEdit = ref<GeneratedQuestion | null>(null)
const questionEditPrompt = ref('')
const questionEditAnswer = ref('')
const questionEditExplanation = ref('')
const deleteTarget = ref<
  | { kind: 'card'; id: string; title: string }
  | { kind: 'question'; id: string; title: string }
  | { kind: 'wrong'; id: string; title: string }
  | null
>(null)
const modalError = ref('')

onMounted(loadStudyAssets)
watch(() => store.selectedCourseId, loadStudyAssets)

async function generate(kind: 'cards' | 'questions') {
  const currentTopic = topic.value.trim()
  if (!currentTopic) return
  busy.value = kind
  output.value = ''
  error.value = ''
  try {
    const path = kind === 'cards' ? '/study/cards' : '/study/questions'
    output.value = (await api.generate(path, currentTopic, store.selectedCourseId)).content
    if (kind === 'cards') {
      await loadStudyCards()
    } else {
      await loadGeneratedQuestions()
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    busy.value = ''
  }
}

async function saveWrongNote() {
  busy.value = 'wrong'
  output.value = ''
  error.value = ''
  try {
    output.value = (
      await api.addWrongNote({
        course_id: store.selectedCourseId,
        title: topic.value,
        original_question: wrongQuestion.value,
        user_answer: wrongAnswer.value,
        correct_answer: correctAnswer.value
      })
    ).content
    wrongQuestion.value = ''
    wrongAnswer.value = ''
    correctAnswer.value = ''
    await loadWrongNotes()
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    busy.value = ''
  }
}

async function loadStudyAssets() {
  await Promise.all([loadStudyCards(), loadGeneratedQuestions(), loadWrongNotes()])
}

async function loadStudyCards() {
  if (!store.selectedCourseId) {
    studyCards.value = []
    return
  }
  try {
    studyCards.value = await api.listStudyCards(store.selectedCourseId)
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  }
}

async function loadGeneratedQuestions() {
  if (!store.selectedCourseId) {
    generatedQuestions.value = []
    return
  }
  try {
    generatedQuestions.value = await api.listGeneratedQuestions(store.selectedCourseId)
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  }
}

async function updateCardMastery(card: StudyCard, mastery: number) {
  const nextMastery = Math.min(5, Math.max(0, mastery))
  error.value = ''
  try {
    const updated = await api.updateStudyCardMastery(card.id, nextMastery)
    studyCards.value = studyCards.value.map((item) => (item.id === updated.id ? updated : item))
    store.markProgressChanged()
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  }
}

function editStudyCard(card: StudyCard) {
  cardPendingEdit.value = card
  cardEditFront.value = card.front
  cardEditBack.value = card.back
  modalError.value = ''
}

async function confirmEditStudyCard() {
  if (!cardPendingEdit.value) return
  const nextFront = cardEditFront.value.trim()
  const nextBack = cardEditBack.value.trim()
  if (!nextFront || !nextBack) {
    modalError.value = '卡片正面和背面不能为空'
    return
  }
  const card = cardPendingEdit.value
  busy.value = `card-edit:${card.id}`
  error.value = ''
  modalError.value = ''
  try {
    const updated = await api.updateStudyCard(card.id, { front: nextFront, back: nextBack })
    studyCards.value = studyCards.value.map((item) => (item.id === updated.id ? updated : item))
    cardPendingEdit.value = null
  } catch (err) {
    modalError.value = err instanceof Error ? err.message : String(err)
    error.value = modalError.value
  } finally {
    busy.value = ''
  }
}

function deleteStudyCard(card: StudyCard) {
  deleteTarget.value = { kind: 'card', id: card.id, title: card.front }
  modalError.value = ''
}

async function confirmDeleteTarget() {
  if (!deleteTarget.value) return
  const target = deleteTarget.value
  if (target.kind === 'card') {
    await confirmDeleteStudyCard(target.id)
  } else if (target.kind === 'question') {
    await confirmDeleteGeneratedQuestion(target.id)
  } else {
    await confirmDeleteWrongNote(target.id)
  }
}

async function confirmDeleteStudyCard(cardId: string) {
  busy.value = `card-delete:${cardId}`
  error.value = ''
  modalError.value = ''
  try {
    await api.deleteStudyCard(cardId)
    studyCards.value = studyCards.value.filter((item) => item.id !== cardId)
    deleteTarget.value = null
    store.markProgressChanged()
  } catch (err) {
    modalError.value = err instanceof Error ? err.message : String(err)
    error.value = modalError.value
  } finally {
    busy.value = ''
  }
}

async function addQuestionToWrongNotes(question: GeneratedQuestion) {
  busy.value = `question:${question.id}`
  output.value = ''
  error.value = ''
  try {
    const note = await api.addGeneratedQuestionToWrongNotes(question.id)
    wrongNotes.value = [note, ...wrongNotes.value.filter((item) => item.id !== note.id)]
    output.value = '已加入错题本'
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    busy.value = ''
  }
}

function editGeneratedQuestion(question: GeneratedQuestion) {
  questionPendingEdit.value = question
  questionEditPrompt.value = question.prompt
  questionEditAnswer.value = question.answer
  questionEditExplanation.value = question.explanation
  modalError.value = ''
}

async function confirmEditGeneratedQuestion() {
  if (!questionPendingEdit.value) return
  const nextPrompt = questionEditPrompt.value.trim()
  const nextAnswer = questionEditAnswer.value.trim()
  const nextExplanation = questionEditExplanation.value.trim()
  if (!nextPrompt || !nextAnswer) {
    modalError.value = '试题题干和参考答案不能为空'
    return
  }
  const question = questionPendingEdit.value
  busy.value = `question-edit:${question.id}`
  error.value = ''
  modalError.value = ''
  try {
    const updated = await api.updateGeneratedQuestion(question.id, {
      prompt: nextPrompt,
      answer: nextAnswer,
      explanation: nextExplanation
    })
    generatedQuestions.value = generatedQuestions.value.map((item) => (item.id === updated.id ? updated : item))
    questionPendingEdit.value = null
  } catch (err) {
    modalError.value = err instanceof Error ? err.message : String(err)
    error.value = modalError.value
  } finally {
    busy.value = ''
  }
}

function deleteGeneratedQuestion(question: GeneratedQuestion) {
  deleteTarget.value = { kind: 'question', id: question.id, title: question.prompt }
  modalError.value = ''
}

async function confirmDeleteGeneratedQuestion(questionId: string) {
  busy.value = `question-delete:${questionId}`
  error.value = ''
  modalError.value = ''
  try {
    await api.deleteGeneratedQuestion(questionId)
    generatedQuestions.value = generatedQuestions.value.filter((item) => item.id !== questionId)
    deleteTarget.value = null
  } catch (err) {
    modalError.value = err instanceof Error ? err.message : String(err)
    error.value = modalError.value
  } finally {
    busy.value = ''
  }
}

async function loadWrongNotes() {
  if (!store.selectedCourseId) {
    wrongNotes.value = []
    return
  }
  try {
    wrongNotes.value = await api.listWrongNotes(store.selectedCourseId)
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  }
}

function deleteWrongNote(note: WrongNote) {
  deleteTarget.value = { kind: 'wrong', id: note.id, title: note.title }
  modalError.value = ''
}

async function confirmDeleteWrongNote(noteId: string) {
  busy.value = `wrong-delete:${noteId}`
  error.value = ''
  modalError.value = ''
  try {
    await api.deleteWrongNote(noteId)
    wrongNotes.value = wrongNotes.value.filter((item) => item.id !== noteId)
    deleteTarget.value = null
  } catch (err) {
    modalError.value = err instanceof Error ? err.message : String(err)
    error.value = modalError.value
  } finally {
    busy.value = ''
  }
}
</script>

<template>
  <AppPanel title="学习材料">
    <template #icon>
      <Brain :size="20" />
    </template>
    <template #actions>
      <button class="icon-button" type="button" title="刷新学习材料" @click="loadStudyAssets">
        <RefreshCw :size="16" />
      </button>
    </template>

    <input v-model="topic" placeholder="例如：SNMP 协议" />
    <div class="button-row">
      <button data-testid="generate-cards-button" @click="generate('cards')" :disabled="!!busy || !topic.trim()">
        <Layers :size="18" />
        <span>复习卡片</span>
      </button>
      <button data-testid="generate-questions-button" @click="generate('questions')" :disabled="!!busy || !topic.trim()">
        <ClipboardList :size="18" />
        <span>考试题</span>
      </button>
    </div>

    <section class="study-card-list">
      <header class="section-heading">
        <strong>最近卡片</strong>
        <span>{{ studyCards.length }} 张</span>
      </header>
      <article v-for="card in studyCards" :key="card.id" class="study-card">
        <header class="asset-card-header">
          <strong>{{ card.front }}</strong>
          <div class="asset-card-actions">
            <button class="icon-button" type="button" title="编辑卡片" :disabled="!!busy" @click="editStudyCard(card)">
              <Pencil :size="15" />
            </button>
            <button class="icon-button danger-icon-button" type="button" title="删除卡片" :disabled="!!busy" @click="deleteStudyCard(card)">
              <Trash2 :size="15" />
            </button>
          </div>
        </header>
        <p>{{ card.back }}</p>
        <div class="mastery-control">
          <button type="button" title="降低掌握度" :disabled="card.mastery <= 0" @click="updateCardMastery(card, card.mastery - 1)">
            -
          </button>
          <small>掌握度 {{ card.mastery }}/5</small>
          <button type="button" title="提高掌握度" :disabled="card.mastery >= 5" @click="updateCardMastery(card, card.mastery + 1)">
            +
          </button>
        </div>
      </article>
      <p v-if="!studyCards.length" class="muted">当前课程还没有复习卡片。</p>
    </section>

    <section class="generated-question-list">
      <header class="section-heading">
        <strong>最近试题</strong>
        <span>{{ generatedQuestions.length }} 套</span>
      </header>
      <article v-for="question in generatedQuestions" :key="question.id" class="generated-question-card">
        <header class="asset-card-header">
          <strong>{{ question.prompt }}</strong>
          <div class="asset-card-actions">
            <button class="icon-button" type="button" title="编辑试题" :disabled="!!busy" @click="editGeneratedQuestion(question)">
              <Pencil :size="15" />
            </button>
            <button class="icon-button danger-icon-button" type="button" title="删除试题" :disabled="!!busy" @click="deleteGeneratedQuestion(question)">
              <Trash2 :size="15" />
            </button>
          </div>
        </header>
        <pre>{{ question.answer }}</pre>
        <p v-if="question.explanation" class="muted">{{ question.explanation }}</p>
        <button
          class="secondary-button"
          type="button"
          :disabled="!!busy"
          @click="addQuestionToWrongNotes(question)"
        >
          <NotebookPen :size="16" />
          <span>{{ busy === `question:${question.id}` ? '加入中' : '加入错题本' }}</span>
        </button>
      </article>
      <p v-if="!generatedQuestions.length" class="muted">当前课程还没有生成试题。</p>
    </section>

    <div class="wrong-note">
      <textarea v-model="wrongQuestion" rows="3" placeholder="错题题目"></textarea>
      <textarea v-model="wrongAnswer" rows="2" placeholder="我的答案"></textarea>
      <textarea v-model="correctAnswer" rows="2" placeholder="参考答案，可以留空"></textarea>
      <button @click="saveWrongNote" :disabled="!!busy || !wrongQuestion.trim()">
        <NotebookPen :size="18" />
        <span>整理错题</span>
      </button>
    </div>

    <p v-if="error" class="inline-error">{{ error }}</p>
    <pre v-if="output" class="generated-output">{{ output }}</pre>

    <section class="wrong-note-list">
      <header class="section-heading">
        <strong>最近错题</strong>
        <span>{{ wrongNotes.length }} 条</span>
      </header>
      <article v-for="note in wrongNotes" :key="note.id" class="wrong-note-card">
        <header class="asset-card-header">
          <strong>{{ note.title }}</strong>
          <button class="icon-button danger-icon-button" type="button" title="删除错题" :disabled="!!busy" @click="deleteWrongNote(note)">
            <Trash2 :size="15" />
          </button>
        </header>
        <p>{{ note.original_question }}</p>
        <dl>
          <template v-if="note.user_answer">
            <dt>我的答案</dt>
            <dd>{{ note.user_answer }}</dd>
          </template>
          <template v-if="note.correct_answer">
            <dt>参考答案</dt>
            <dd>{{ note.correct_answer }}</dd>
          </template>
          <template v-if="note.analysis">
            <dt>AI 解析</dt>
            <dd>{{ note.analysis }}</dd>
          </template>
        </dl>
      </article>
      <p v-if="!wrongNotes.length" class="muted">当前课程还没有错题记录。</p>
    </section>
    <AppModal
      :open="!!cardPendingEdit"
      title="编辑复习卡片"
      confirm-label="保存卡片"
      :busy="busy.startsWith('card-edit:')"
      :error="modalError"
      @close="cardPendingEdit = null"
      @confirm="confirmEditStudyCard"
    >
      <label>
        <span>卡片正面</span>
        <textarea v-model="cardEditFront" data-testid="card-front-input" rows="3"></textarea>
      </label>
      <label>
        <span>卡片背面</span>
        <textarea v-model="cardEditBack" data-testid="card-back-input" rows="4"></textarea>
      </label>
    </AppModal>
    <AppModal
      :open="!!questionPendingEdit"
      title="编辑练习题"
      confirm-label="保存试题"
      :busy="busy.startsWith('question-edit:')"
      :error="modalError"
      @close="questionPendingEdit = null"
      @confirm="confirmEditGeneratedQuestion"
    >
      <label>
        <span>题干</span>
        <textarea v-model="questionEditPrompt" data-testid="question-prompt-input" rows="3"></textarea>
      </label>
      <label>
        <span>参考答案</span>
        <textarea v-model="questionEditAnswer" data-testid="question-answer-input" rows="4"></textarea>
      </label>
      <label>
        <span>解析</span>
        <textarea v-model="questionEditExplanation" data-testid="question-explanation-input" rows="3"></textarea>
      </label>
    </AppModal>
    <AppModal
      :open="!!deleteTarget"
      :title="deleteTarget?.kind === 'card' ? '删除复习卡片' : deleteTarget?.kind === 'question' ? '删除练习题' : '删除错题记录'"
      :confirm-label="deleteTarget?.kind === 'card' ? '删除卡片' : deleteTarget?.kind === 'question' ? '删除试题' : '删除错题'"
      danger
      :busy="busy.includes('-delete:')"
      :error="modalError"
      @close="deleteTarget = null"
      @confirm="confirmDeleteTarget"
    >
      <p>确定删除“{{ deleteTarget?.title }}”吗？该操作无法撤销。</p>
    </AppModal>
  </AppPanel>
</template>
