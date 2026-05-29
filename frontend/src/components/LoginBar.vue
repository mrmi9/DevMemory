<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { LogIn } from 'lucide-vue-next'
import { api, type SystemStatus } from '../api'
import { useStudyStore } from '../stores/study'

const store = useStudyStore()
const username = ref('admin')
const password = ref('changeme')
const message = ref('')
const systemStatus = ref<SystemStatus | null>(null)

const aiModeLabel = computed(() => {
  if (!systemStatus.value) return '状态检查中'
  return systemStatus.value.ai_mode === 'online' ? '在线 AI 模式' : '离线占位 AI 模式'
})

const aiModeDetail = computed(() => {
  if (!systemStatus.value) return ''
  if (systemStatus.value.ai_mode === 'online') return systemStatus.value.checks.deepseek?.model || 'DeepSeek 已配置'
  return 'DeepSeek 未配置'
})

onMounted(async () => {
  try {
    systemStatus.value = await api.systemStatus()
  } catch (error) {
    systemStatus.value = null
  }
})

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
    <span class="mode-pill" :class="{ offline: systemStatus?.ai_mode === 'offline_placeholder' }">
      {{ aiModeLabel }}
      <small v-if="aiModeDetail">{{ aiModeDetail }}</small>
    </span>
    <span class="muted">{{ message || store.error }}</span>
  </form>
</template>
