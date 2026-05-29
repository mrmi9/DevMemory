<script setup lang="ts">
import { ref } from 'vue'
import { LogIn } from 'lucide-vue-next'
import { useStudyStore } from '../stores/study'

const store = useStudyStore()
const username = ref('admin')
const password = ref('changeme')
const message = ref('')

async function login() {
  message.value = ''
  try {
    await store.login(username.value, password.value)
    await store.loadCourses()
    message.value = '已登录'
  } catch (error) {
    message.value = error instanceof Error ? error.message : String(error)
  }
}
</script>

<template>
  <form class="login-bar" @submit.prevent="login">
    <input v-model="username" aria-label="用户名" placeholder="用户名" />
    <input v-model="password" aria-label="密码" placeholder="密码" type="password" />
    <button type="submit" title="登录">
      <LogIn :size="18" />
      <span>登录</span>
    </button>
    <span class="muted">{{ message || store.error }}</span>
  </form>
</template>
