import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '../api'
import LoginBar from './LoginBar.vue'

vi.mock('../api', () => ({
  api: {
    hasToken: vi.fn(),
    listCourses: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    getAiConfig: vi.fn(),
    updateAiConfig: vi.fn(),
    systemStatus: vi.fn()
  }
}))

describe('LoginBar', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
    vi.useRealTimers()
    vi.mocked(api.hasToken).mockReturnValue(false)
    vi.mocked(api.listCourses).mockResolvedValue([])
    vi.mocked(api.login).mockResolvedValue(undefined)
    vi.mocked(api.logout).mockReset()
    vi.mocked(api.getAiConfig).mockReset()
    vi.mocked(api.updateAiConfig).mockReset()
    vi.mocked(api.systemStatus).mockReset()
  })

  afterEach(() => {
    vi.useRealTimers()
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
    expect(wrapper.text()).not.toMatch(/璇|妫|鍒|鎬|�/)
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
    expect(wrapper.text()).toContain('在线 AI 模式')
    expect(wrapper.text()).toContain('deepseek-v4-flash')
  })

  it('shows a failure state when the AI status check fails', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    vi.mocked(api.systemStatus).mockRejectedValue(new Error('服务暂时不可用，请稍后重试'))

    const wrapper = mount(LoginBar, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    expect(wrapper.text()).toContain('状态检查失败')
    expect(wrapper.text()).toContain('服务暂时不可用，请稍后重试')
    expect(wrapper.text()).not.toContain('状态检查中')
  })

  it('automatically retries failed AI status checks and recovers', async () => {
    vi.useFakeTimers()
    const pinia = createPinia()
    setActivePinia(pinia)
    vi.mocked(api.systemStatus)
      .mockRejectedValueOnce(new Error('temporary 502'))
      .mockResolvedValueOnce({
        status: 'ok',
        environment: 'production',
        ai_mode: 'online',
        checks: {
          deepseek: { configured: true, model: 'deepseek-v4-pro' }
        }
      })

    const wrapper = mount(LoginBar, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    expect(wrapper.text()).toContain('状态检查失败')

    await vi.advanceTimersByTimeAsync(1200)
    await flushPromises()

    expect(api.systemStatus).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('在线 AI 模式')
    expect(wrapper.text()).toContain('deepseek-v4-pro')
  })

  it('lets users manually retry the AI status check', async () => {
    vi.useFakeTimers()
    const pinia = createPinia()
    setActivePinia(pinia)
    vi.mocked(api.systemStatus)
      .mockRejectedValueOnce(new Error('temporary 502'))
      .mockResolvedValueOnce({
        status: 'ok',
        environment: 'production',
        ai_mode: 'online',
        checks: {
          deepseek: { configured: true, model: 'deepseek-v4-pro' }
        }
      })

    const wrapper = mount(LoginBar, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    await wrapper.find('[data-testid="status-retry-button"]').trigger('click')
    await flushPromises()

    expect(api.systemStatus).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('在线 AI 模式')
    expect(wrapper.text()).toContain('deepseek-v4-pro')
  })

  it('lets signed-in users configure DeepSeek from the page', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    vi.mocked(api.hasToken).mockReturnValue(true)
    vi.mocked(api.systemStatus)
      .mockResolvedValueOnce({
        status: 'ok',
        environment: 'production',
        ai_mode: 'offline_placeholder',
        checks: {
          deepseek: { configured: false }
        }
      })
      .mockResolvedValueOnce({
        status: 'ok',
        environment: 'production',
        ai_mode: 'online',
        checks: {
          deepseek: { configured: true, model: 'deepseek-chat' }
        }
      })
    vi.mocked(api.getAiConfig).mockResolvedValue({
      configured: false,
      api_key_hint: null,
      base_url: 'https://api.deepseek.com',
      model: 'deepseek-chat'
    })
    vi.mocked(api.updateAiConfig).mockResolvedValue({
      configured: true,
      api_key_hint: '••••3456',
      base_url: 'https://api.deepseek.com',
      model: 'deepseek-chat'
    })

    const wrapper = mount(LoginBar, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    await wrapper.find('[data-testid="ai-config-button"]').trigger('click')
    await flushPromises()
    ;(document.body.querySelector('[data-testid="deepseek-api-key-input"]') as HTMLInputElement).value = 'sk-page-123456'
    ;(document.body.querySelector('[data-testid="deepseek-api-key-input"]') as HTMLInputElement).dispatchEvent(new Event('input'))
    ;(document.body.querySelector('[data-testid="deepseek-model-input"]') as HTMLInputElement).value = 'deepseek-chat'
    ;(document.body.querySelector('[data-testid="deepseek-model-input"]') as HTMLInputElement).dispatchEvent(new Event('input'))
    await wrapper.findComponent({ name: 'AppModal' }).vm.$emit('confirm')
    await flushPromises()

    expect(api.updateAiConfig).toHaveBeenCalledWith({
      api_key: 'sk-page-123456',
      base_url: 'https://api.deepseek.com',
      model: 'deepseek-chat'
    })
    expect(api.systemStatus).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('在线 AI 模式')
    expect(wrapper.text()).toContain('AI 配置已保存')
  })
})
