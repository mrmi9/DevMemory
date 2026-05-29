<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { Brain, ClipboardList, Layers, NotebookPen, Pencil, RefreshCw, Trash2 } from 'lucide-vue-next'
import { api, type GeneratedQuestion, type StudyCard, type WrongNote } from '../api'
import { useStudyStore } from '../stores/study'

const store = useStudyStore()
const topic = ref('SNMP 协议')
const output = ref('')
const wrongQuestion = ref('')
const wrongAnswer = ref('')
const correctAnswer = ref('')
const busy = ref('')
const error = ref('')
const studyCards = ref<StudyCard[]>([])
const generatedQuestions = ref<GeneratedQuestion[]>([])
const wrongNotes = ref<WrongNote[]>([])

onMounted(loadStudyAssets)
watch(() => store.selectedCourseId, loadStudyAssets)

async function generate(kind: 'cards' | 'questions') {
  busy.value = kind
  output.value = ''
  error.value = ''
  try {
    const path = kind === 'cards' ? '/study/cards' : '/study/questions'
    output.value = (await api.generate(path, topic.value, store.selectedCourseId)).content
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

async function editStudyCard(card: StudyCard) {
  const nextFront = window.prompt('编辑卡片正面', card.front)?.trim()
  if (!nextFront) return
  const nextBack = window.prompt('编辑卡片背面', card.back)?.trim()
  if (!nextBack) return
  busy.value = `card-edit:${card.id}`
  error.value = ''
  try {
    const updated = await api.updateStudyCard(card.id, { front: nextFront, back: nextBack })
    studyCards.value = studyCards.value.map((item) => (item.id === updated.id ? updated : item))
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    busy.value = ''
  }
}

async function deleteStudyCard(card: StudyCard) {
  if (!window.confirm(`确定删除“${card.front}”吗？`)) return
  busy.value = `card-delete:${card.id}`
  error.value = ''
  try {
    await api.deleteStudyCard(card.id)
    studyCards.value = studyCards.value.filter((item) => item.id !== card.id)
    store.markProgressChanged()
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
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

async function editGeneratedQuestion(question: GeneratedQuestion) {
  const nextPrompt = window.prompt('编辑试题题干', question.prompt)?.trim()
  if (!nextPrompt) return
  const nextAnswer = window.prompt('编辑参考答案', question.answer)?.trim()
  if (!nextAnswer) return
  const nextExplanation = window.prompt('编辑解析', question.explanation)?.trim() ?? ''
  busy.value = `question-edit:${question.id}`
  error.value = ''
  try {
    const updated = await api.updateGeneratedQuestion(question.id, {
      prompt: nextPrompt,
      answer: nextAnswer,
      explanation: nextExplanation
    })
    generatedQuestions.value = generatedQuestions.value.map((item) => (item.id === updated.id ? updated : item))
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    busy.value = ''
  }
}

async function deleteGeneratedQuestion(question: GeneratedQuestion) {
  if (!window.confirm(`确定删除“${question.prompt}”吗？`)) return
  busy.value = `question-delete:${question.id}`
  error.value = ''
  try {
    await api.deleteGeneratedQuestion(question.id)
    generatedQuestions.value = generatedQuestions.value.filter((item) => item.id !== question.id)
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
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

async function deleteWrongNote(note: WrongNote) {
  if (!window.confirm(`确定删除“${note.title}”吗？`)) return
  busy.value = `wrong-delete:${note.id}`
  error.value = ''
  try {
    await api.deleteWrongNote(note.id)
    wrongNotes.value = wrongNotes.value.filter((item) => item.id !== note.id)
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    busy.value = ''
  }
}
</script>

<template>
  <section class="panel">
    <header class="panel-header">
      <Brain :size="20" />
      <h2>学习材料</h2>
      <button class="icon-button" type="button" title="刷新学习材料" @click="loadStudyAssets">
        <RefreshCw :size="16" />
      </button>
    </header>

    <input v-model="topic" placeholder="主题，例如 SNMP 协议" />
    <div class="button-row">
      <button @click="generate('cards')" :disabled="!!busy">
        <Layers :size="18" />
        <span>复习卡片</span>
      </button>
      <button @click="generate('questions')" :disabled="!!busy">
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
      <textarea v-model="correctAnswer" rows="2" placeholder="参考答案，可留空"></textarea>
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
  </section>
</template>
