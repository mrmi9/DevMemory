<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { Activity } from 'lucide-vue-next'
import AppPanel from './AppPanel.vue'
import { api, type ProgressOverview, type ReviewCard } from '../api'
import { useStudyStore } from '../stores/study'

const store = useStudyStore()
const emptyOverview: ProgressOverview = {
  courses: 0,
  records: 0,
  average_mastery: 0,
  items: [],
  review: {
    today_due: 0,
    low_mastery: 0,
    mastered: 0,
    cards: [],
    recent_wrong_notes: []
  }
}
const overview = ref<ProgressOverview>(emptyOverview)
const reviewBusy = ref('')

async function loadOverview() {
  try {
    overview.value = await api.progressOverview()
  } catch {
    overview.value = emptyOverview
  }
}

async function reviewCard(card: ReviewCard, mastery: number) {
  reviewBusy.value = card.id
  try {
    await api.updateStudyCardMastery(card.id, mastery)
    store.markProgressChanged()
  } finally {
    reviewBusy.value = ''
  }
}

function reviewStateLabel(card: ReviewCard) {
  if (card.review_state === 'mastered') return '已掌握'
  if (card.review_state === 'not_started') return '未开始'
  return '需巩固'
}

onMounted(loadOverview)
watch(() => store.selectedCourseId, loadOverview)
watch(() => store.progressRefreshKey, loadOverview)
</script>

<template>
  <AppPanel title="学习进度" panel-class="progress-panel">
    <template #icon>
      <Activity :size="20" />
    </template>
    <div class="metrics">
      <span><strong>{{ overview.courses }}</strong><small>课程</small></span>
      <span><strong>{{ overview.records }}</strong><small>记录</small></span>
      <span><strong>{{ overview.average_mastery }}</strong><small>平均掌握</small></span>
    </div>
    <section class="daily-review">
      <header class="section-heading">
        <strong>今日复习任务</strong>
        <span>{{ overview.review?.today_due ?? 0 }} 张待复习</span>
      </header>
      <div class="review-metrics">
        <span><strong>{{ overview.review?.today_due ?? 0 }}</strong><small>今日待复习</small></span>
        <span><strong>{{ overview.review?.low_mastery ?? 0 }}</strong><small>低掌握</small></span>
        <span><strong>{{ overview.review?.mastered ?? 0 }}</strong><small>已掌握</small></span>
      </div>
      <article v-for="card in overview.review?.cards ?? []" :key="card.id" class="review-card">
        <div>
          <strong>{{ card.front }}</strong>
          <small>{{ reviewStateLabel(card) }} · 掌握度 {{ card.mastery }}/5</small>
          <small>下次复习：{{ card.next_review_label }} · 已复习 {{ card.review_count ?? 0 }} 次</small>
        </div>
        <div class="review-actions">
          <button type="button" :disabled="reviewBusy === card.id" @click="reviewCard(card, 1)">忘记</button>
          <button type="button" :disabled="reviewBusy === card.id" @click="reviewCard(card, 2)">模糊</button>
          <button type="button" data-testid="review-good" :disabled="reviewBusy === card.id" @click="reviewCard(card, 4)">掌握</button>
          <button type="button" :disabled="reviewBusy === card.id" @click="reviewCard(card, 5)">简单</button>
        </div>
      </article>
      <p v-if="!(overview.review?.cards?.length)" class="muted">今天没有待复习卡片。</p>
      <section class="recent-wrong-notes">
        <header class="section-heading">
          <strong>最近错题</strong>
          <span>{{ overview.review?.recent_wrong_notes?.length ?? 0 }} 条</span>
        </header>
        <article v-for="note in overview.review?.recent_wrong_notes ?? []" :key="note.id" class="review-card">
          <strong>{{ note.title }}</strong>
          <small>{{ note.analysis || note.correct_answer }}</small>
        </article>
      </section>
    </section>
  </AppPanel>
</template>
