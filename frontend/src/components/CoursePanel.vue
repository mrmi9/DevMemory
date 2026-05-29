<script setup lang="ts">
import { ref } from 'vue'
import { BookOpen, Plus } from 'lucide-vue-next'
import { useStudyStore } from '../stores/study'

const store = useStudyStore()
const title = ref('计算机网络')
const description = ref('课程资料、协议重点与错题整理')

async function createCourse() {
  if (!title.value.trim()) return
  await store.createCourse(title.value.trim(), description.value.trim())
  title.value = ''
  description.value = ''
}
</script>

<template>
  <section class="panel course-panel">
    <header class="panel-header">
      <BookOpen :size="20" />
      <h2>课程</h2>
    </header>
    <div class="course-list">
      <button
        v-for="course in store.courses"
        :key="course.id"
        class="course-row"
        :class="{ active: course.id === store.selectedCourseId }"
        @click="store.selectedCourseId = course.id"
      >
        <span class="swatch" :style="{ background: course.color }"></span>
        <span>
          <strong>{{ course.title }}</strong>
          <small>{{ course.description || '暂无描述' }}</small>
        </span>
      </button>
    </div>
    <form class="stack" @submit.prevent="createCourse">
      <input v-model="title" placeholder="课程名称" />
      <textarea v-model="description" rows="3" placeholder="课程描述"></textarea>
      <button type="submit">
        <Plus :size="18" />
        <span>新建课程</span>
      </button>
    </form>
  </section>
</template>
