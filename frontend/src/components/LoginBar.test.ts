import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '../api'
import LoginBar from './LoginBar.vue'

vi.mock('../api', () => ({
  api: {
    hasToken: vi.fn(),
    listCourses: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    systemStatus: vi.fn()
  }
}))

describe('LoginBar', () => {
  beforeEach(() => {
    vi.mocked(api.hasToken).mockReturnValue(false)
    vi.mocked(api.listCourses).mockResolvedValue([])
    vi.mocked(api.login).mockResolvedValue(undefined)
    vi.mocked(api.logout).mockReset()
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

  it('lets signed-in users log out and clears local study state', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    vi.mocked(api.hasToken).mockReturnValue(true)
    vi.mocked(api.systemStatus).mockResolvedValue({
      status: 'ok',
      environment: 'production',
      ai_mode: 'online',
      checks: {
        deepseek: { configured: true, model: 'deepseek-v4-flash' }
      }
    })

    const wrapper = mount(LoginBar, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    await wrapper.find('[data-testid="logout-button"]').trigger('click')

    expect(api.logout).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('已退出登录')
  })
})
