<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { KeyRound, LogIn, LogOut, RefreshCw } from 'lucide-vue-next'
import { api, type AIConfig, type SystemStatus } from '../api'
import { useStudyStore } from '../stores/study'
import AppModal from './AppModal.vue'

const store = useStudyStore()
const username = ref('')
const password = ref('')
const message = ref('')
const isLoggedIn = ref(api.hasToken())
const systemStatus = ref<SystemStatus | null>(null)
const statusLoading = ref(false)
const statusError = ref('')
const aiConfigOpen = ref(false)
const aiConfig = ref<AIConfig | null>(null)
const aiConfigBusy = ref(false)
const aiConfigError = ref('')
const deepseekApiKey = ref('')
const deepseekBaseUrl = ref('https://api.deepseek.com')
const deepseekModel = ref('deepseek-chat')
let statusRetryTimer: ReturnType<typeof setTimeout> | null = null

const aiModeLabel = computed(() => {
  if (statusLoading.value && !systemStatus.value) return '状态检查中'
  if (statusError.value && !systemStatus.value) return '状态检查失败'
  if (!systemStatus.value) return '状态检查中'
  return systemStatus.value.ai_mode === 'online' ? '在线 AI 模式' : '离线占位 AI 模式'
})

const aiModeDetail = computed(() => {
  if (statusError.value) return statusError.value
  if (!systemStatus.value) return ''
  if (systemStatus.value.ai_mode === 'online') return systemStatus.value.checks.deepseek?.model || 'DeepSeek 已配置'
  return 'DeepSeek 未配置'
})

onMounted(() => refreshSystemStatus({ retries: 2 }))

onBeforeUnmount(() => {
  clearStatusRetryTimer()
})

function clearStatusRetryTimer() {
  if (statusRetryTimer) {
    clearTimeout(statusRetryTimer)
    statusRetryTimer = null
  }
}

async function refreshSystemStatus(options: { retries?: number; clearRetry?: boolean } = {}) {
  const retries = options.retries ?? 0
  if (options.clearRetry ?? true) clearStatusRetryTimer()
  statusLoading.value = true
  try {
    systemStatus.value = await api.systemStatus()
    statusError.value = ''
  } catch {
    statusError.value = '服务暂时不可用，请稍后重试'
    if (retries > 0) {
      statusRetryTimer = setTimeout(() => {
        refreshSystemStatus({ retries: retries - 1, clearRetry: false })
      }, 1000)
    }
  } finally {
    statusLoading.value = false
  }
}

function retrySystemStatus() {
  refreshSystemStatus()
}

async function login() {
  if (!username.value.trim() || !password.value) return
  message.value = ''
  try {
    await store.login(username.value, password.value)
    await store.loadCourses()
    isLoggedIn.value = true
    message.value = '已登录'
  } catch (error) {
    message.value = error instanceof Error ? error.message : String(error)
  }
}

function logout() {
  store.logout()
  isLoggedIn.value = false
  message.value = '已退出登录'
}

async function openAiConfig() {
  if (!isLoggedIn.value) {
    message.value = '请先登录后再配置 AI'
    return
  }
  aiConfigOpen.value = true
  aiConfigError.value = ''
  deepseekApiKey.value = ''
  try {
    aiConfig.value = await api.getAiConfig()
    deepseekBaseUrl.value = aiConfig.value.base_url
    deepseekModel.value = aiConfig.value.model
  } catch (error) {
    aiConfigError.value = error instanceof Error ? error.message : String(error)
  }
}

async function saveAiConfig() {
  aiConfigBusy.value = true
  aiConfigError.value = ''
  try {
    aiConfig.value = await api.updateAiConfig({
      api_key: deepseekApiKey.value.trim() || undefined,
      base_url: deepseekBaseUrl.value.trim(),
      model: deepseekModel.value.trim()
    })
    deepseekApiKey.value = ''
    await refreshSystemStatus()
    message.value = 'AI 配置已保存'
    aiConfigOpen.value = false
  } catch (error) {
    aiConfigError.value = error instanceof Error ? error.message : String(error)
  } finally {
    aiConfigBusy.value = false
  }
}
</script>

<template>
  <form class="login-bar" @submit.prevent="login">
    <input v-model="username" aria-label="用户名" placeholder="用户名（例如：admin）" :disabled="isLoggedIn" />
    <input v-model="password" aria-label="密码" placeholder="密码" type="password" :disabled="isLoggedIn" />
    <button v-if="!isLoggedIn" type="submit" title="登录" :disabled="!username.trim() || !password">
      <LogIn :size="18" />
      <span>登录</span>
    </button>
    <button v-else type="button" title="退出登录" data-testid="logout-button" class="secondary-button" @click="logout">
      <LogOut :size="18" />
      <span>退出</span>
    </button>
    <span
      class="mode-pill"
      :class="{
        offline: systemStatus?.ai_mode === 'offline_placeholder',
        error: Boolean(statusError)
      }"
    >
      {{ aiModeLabel }}
      <small v-if="aiModeDetail">{{ aiModeDetail }}</small>
    </span>
    <button
      v-if="statusError"
      type="button"
      title="重新检查 AI 状态"
      data-testid="status-retry-button"
      class="icon-button"
      :disabled="statusLoading"
      @click="retrySystemStatus"
    >
      <RefreshCw :size="16" />
    </button>
    <button
      type="button"
      title="配置 DeepSeek API"
      data-testid="ai-config-button"
      class="secondary-button"
      @click="openAiConfig"
    >
      <KeyRound :size="18" />
      <span>AI 配置</span>
    </button>
    <span class="muted">{{ message || store.error }}</span>
    <AppModal
      :open="aiConfigOpen"
      title="DeepSeek API 配置"
      confirm-label="保存配置"
      :busy="aiConfigBusy"
      :error="aiConfigError"
      @close="aiConfigOpen = false"
      @confirm="saveAiConfig"
    >
      <div class="stack ai-config-form">
        <p class="muted">
          当前状态：{{ aiConfig?.configured ? `已配置 ${aiConfig.api_key_hint || ''}` : '未配置' }}
        </p>
        <label>
          <span>API Key</span>
          <input
            v-model="deepseekApiKey"
            data-testid="deepseek-api-key-input"
            type="password"
            autocomplete="off"
            placeholder="sk-..."
          />
        </label>
        <label>
          <span>Base URL</span>
          <input v-model="deepseekBaseUrl" data-testid="deepseek-base-url-input" />
        </label>
        <label>
          <span>模型</span>
          <input v-model="deepseekModel" data-testid="deepseek-model-input" />
        </label>
      </div>
    </AppModal>
  </form>
</template>
