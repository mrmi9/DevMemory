import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '../api'
import LoginBar from './LoginBar.vue'

vi.mock('../api', () => ({
  api: {
    systemStatus: vi.fn()
  }
}))

describe('LoginBar', () => {
  beforeEach(() => {
    vi.mocked(api.systemStatus).mockReset()
  })

  it('shows offline AI mode when DeepSeek is not configured', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    vi.mocked(api.systemStatus).mockResolvedValue({
      status: 'ok',
      environment: 'production',
      ai_mode: 'offline_placeholder',
      checks: {
        deepseek: { configured: false }
      }
    })

    const wrapper = mount(LoginBar, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    expect(wrapper.text()).toContain('离线占位 AI 模式')
    expect(wrapper.text()).toContain('DeepSeek 未配置')
  })
})
