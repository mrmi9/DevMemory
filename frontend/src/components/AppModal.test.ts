import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import AppModal from './AppModal.vue'

describe('AppModal', () => {
  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('renders body content and emits confirm or close from app controls', async () => {
    const wrapper = mount(AppModal, {
      props: {
        open: true,
        title: '删除资料',
        confirmLabel: '确认删除',
        cancelLabel: '取消',
        danger: true
      },
      slots: {
        default: '删除后会从知识库检索中移除。'
      }
    })

    expect(document.body.textContent).toContain('删除资料')
    expect(document.body.textContent).toContain('删除后会从知识库检索中移除。')

    ;(document.body.querySelector('[data-testid="modal-confirm"]') as HTMLButtonElement).click()
    await wrapper.vm.$nextTick()
    expect(wrapper.emitted('confirm')).toHaveLength(1)

    ;(document.body.querySelector('[data-testid="modal-cancel"]') as HTMLButtonElement).click()
    await wrapper.vm.$nextTick()
    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('disables closing actions while busy and shows inline errors', () => {
    const wrapper = mount(AppModal, {
      props: {
        open: true,
        title: '保存修改',
        busy: true,
        error: '保存失败'
      }
    })

    const confirmButton = document.body.querySelector('[data-testid="modal-confirm"]') as HTMLButtonElement
    const cancelButton = document.body.querySelector('[data-testid="modal-cancel"]') as HTMLButtonElement

    expect(confirmButton.disabled).toBe(true)
    expect(cancelButton.disabled).toBe(true)
    expect(document.body.textContent).toContain('保存失败')
    expect(wrapper.emitted('close')).toBeUndefined()
  })
})
