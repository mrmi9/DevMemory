import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { describe, expect, it } from 'vitest'

import CoursePanel from './CoursePanel.vue'

describe('CoursePanel', () => {
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
})
