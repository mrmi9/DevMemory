import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, describe, expect, it, vi } from 'vitest'

import CoursePanel from './CoursePanel.vue'
import { useStudyStore } from '../stores/study'

describe('CoursePanel', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    document.body.innerHTML = ''
  })

  it('shows first-course guidance in readable Chinese when the course list is empty', () => {
    const pinia = createPinia()
    setActivePinia(pinia)

    const wrapper = mount(CoursePanel, {
      global: {
        plugins: [pinia]
      }
    })

    expect(wrapper.text()).toContain('从第一门课程开始')
    expect(wrapper.text()).toContain('创建课程后即可上传资料、提问并生成复习内容')
    expect(wrapper.text()).not.toMatch(/璇|妫|鍒|鎬|�/)
  })

  it('uses placeholders instead of prefilled course examples', () => {
    const pinia = createPinia()
    setActivePinia(pinia)

    const wrapper = mount(CoursePanel, {
      global: {
        plugins: [pinia]
      }
    })

    const titleInput = wrapper.find('input')
    const descriptionInput = wrapper.find('textarea')
    const submitButton = wrapper.find('button[type="submit"]')

    expect((titleInput.element as HTMLInputElement).value).toBe('')
    expect(titleInput.attributes('placeholder')).toBe('例如：计算机网络')
    expect((descriptionInput.element as HTMLTextAreaElement).value).toBe('')
    expect(descriptionInput.attributes('placeholder')).toBe('例如：课程资料、协议重点与错题整理')
    expect((submitButton.element as HTMLButtonElement).disabled).toBe(true)
  })

  it('confirms course deletion in an app modal without window.confirm', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useStudyStore()
    store.courses = [
      {
        id: 'course-1',
        title: '计算机网络',
        description: '协议重点',
        color: '#2563eb'
      }
    ]
    const deleteCourse = vi.spyOn(store, 'deleteCourse').mockResolvedValue()
    const confirmSpy = vi.spyOn(window, 'confirm').mockImplementation(() => {
      throw new Error('window.confirm should not be used')
    })

    const wrapper = mount(CoursePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await wrapper.find('[title="删除课程"]').trigger('click')
    await flushPromises()

    expect(document.body.textContent).toContain('删除课程')
    expect(document.body.textContent).toContain('该课程下的资料和学习记录也会被删除')
    ;(document.body.querySelector('[data-testid="modal-confirm"]') as HTMLButtonElement).click()
    await flushPromises()

    expect(deleteCourse).toHaveBeenCalledWith('course-1')
    expect(confirmSpy).not.toHaveBeenCalled()
  })

  it('keeps delete errors visible inside the course modal', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useStudyStore()
    store.courses = [
      {
        id: 'course-1',
        title: '计算机网络',
        description: '协议重点',
        color: '#2563eb'
      }
    ]
    vi.spyOn(store, 'deleteCourse').mockRejectedValue(new Error('删除失败'))

    const wrapper = mount(CoursePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await wrapper.find('[title="删除课程"]').trigger('click')
    await flushPromises()
    ;(document.body.querySelector('[data-testid="modal-confirm"]') as HTMLButtonElement).click()
    await flushPromises()

    expect(document.body.textContent).toContain('删除失败')
    expect(document.body.textContent).toContain('计算机网络')
  })
})
