<script setup lang="ts">
import { ref } from 'vue'
import { BookOpen, Plus, Trash2 } from 'lucide-vue-next'
import AppModal from './AppModal.vue'
import AppPanel from './AppPanel.vue'
import { useStudyStore } from '../stores/study'

const store = useStudyStore()
const title = ref('')
const description = ref('')
const message = ref('')
const deletingCourseId = ref('')
const coursePendingDelete = ref<{ id: string; title: string } | null>(null)
const courseDeleteError = ref('')

async function createCourse() {
  if (!title.value.trim()) return
  await store.createCourse(title.value.trim(), description.value.trim())
  title.value = ''
  description.value = ''
}

function requestDeleteCourse(courseId: string, courseTitle: string) {
  coursePendingDelete.value = { id: courseId, title: courseTitle }
  message.value = ''
  courseDeleteError.value = ''
}

async function confirmDeleteCourse() {
  if (!coursePendingDelete.value) return
  deletingCourseId.value = coursePendingDelete.value.id
  message.value = ''
  courseDeleteError.value = ''
  try {
    await store.deleteCourse(coursePendingDelete.value.id)
    message.value = '课程已删除'
    coursePendingDelete.value = null
  } catch (error) {
    courseDeleteError.value = error instanceof Error ? error.message : String(error)
    message.value = courseDeleteError.value
  } finally {
    deletingCourseId.value = ''
  }
}
</script>

<template>
  <AppPanel title="课程" panel-class="course-panel">
    <template #icon>
      <BookOpen :size="20" />
    </template>
    <div class="course-list">
      <div
        v-for="course in store.courses"
        :key="course.id"
        class="course-row"
        :class="{ active: course.id === store.selectedCourseId }"
      >
        <button
          class="course-select"
          type="button"
          :disabled="!!deletingCourseId"
          @click="store.selectedCourseId = course.id"
        >
          <span class="swatch" :style="{ background: course.color }"></span>
          <span>
            <strong>{{ course.title }}</strong>
            <small>{{ course.description || '暂无描述' }}</small>
          </span>
        </button>
        <button
          class="course-delete-button"
          type="button"
          title="删除课程"
          :disabled="!!deletingCourseId"
          @click.stop="requestDeleteCourse(course.id, course.title)"
        >
          <Trash2 :size="16" />
          <span class="sr-only">删除课程</span>
        </button>
      </div>
    </div>
    <article v-if="!store.courses.length" class="empty-state">
      <strong>从第一门课程开始</strong>
      <p>创建课程后即可上传资料、提问并生成复习内容。</p>
    </article>
    <p v-if="message || store.error" class="muted">{{ message || store.error }}</p>
    <form class="stack" @submit.prevent="createCourse">
      <input v-model="title" placeholder="例如：计算机网络" />
      <textarea v-model="description" rows="3" placeholder="例如：课程资料、协议重点与错题整理"></textarea>
      <button type="submit" :disabled="store.busy || !!deletingCourseId || !title.trim()">
        <Plus :size="18" />
        <span>新建课程</span>
      </button>
    </form>
    <AppModal
      :open="!!coursePendingDelete"
      title="删除课程"
      confirm-label="删除课程"
      danger
      :busy="!!deletingCourseId"
      :error="courseDeleteError"
      @close="coursePendingDelete = null"
      @confirm="confirmDeleteCourse"
    >
      <p>确定删除“{{ coursePendingDelete?.title }}”吗？该课程下的资料和学习记录也会被删除。</p>
    </AppModal>
  </AppPanel>
</template>
