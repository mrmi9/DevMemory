import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '../api'
import { useStudyStore } from '../stores/study'
import LearningWorkflowChecklist from './LearningWorkflowChecklist.vue'

vi.mock('../api', () => ({
  api: {
    listChatSessions: vi.fn(),
    listDocuments: vi.fn(),
    listGeneratedQuestions: vi.fn(),
    listStudyCards: vi.fn()
  }
}))

describe('LearningWorkflowChecklist', () => {
  beforeEach(() => {
    vi.mocked(api.listChatSessions).mockReset()
    vi.mocked(api.listDocuments).mockReset()
    vi.mocked(api.listGeneratedQuestions).mockReset()
    vi.mocked(api.listStudyCards).mockReset()
  })

  it('shows the full study loop in clear Chinese when no course is selected', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)

    const wrapper = mount(LearningWorkflowChecklist, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    expect(wrapper.text()).toContain('学习闭环')
    expect(wrapper.text()).toContain('创建课程')
    expect(wrapper.text()).toContain('上传资料')
    expect(wrapper.text()).toContain('等待解析完成')
    expect(wrapper.text()).toContain('提出第一个问题')
    expect(wrapper.text()).toContain('生成卡片或试题')
    expect(wrapper.text()).toContain('完成一次复习')
    expect(wrapper.text()).toContain('查看薄弱点')
    expect(wrapper.text()).not.toMatch(/璇|妫|鍒|鎬|�/)
  })

  it('marks the workflow progress from ready materials through review', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useStudyStore()
    store.courses = [{ id: 'course-1', title: '计算机网络', description: '', color: '#2563eb' }]
    store.selectedCourseId = 'course-1'
    vi.mocked(api.listDocuments).mockResolvedValue([
      {
        id: 'document-1',
        course_id: 'course-1',
        title: 'network.pdf',
        original_filename: 'network.pdf',
        kind: 'pdf',
        status: 'ready',
        error_message: '',
        text_preview: 'SNMP notes',
        created_at: '2026-05-29T14:00:00',
        updated_at: '2026-05-29T14:01:00',
        chunk_count: 8,
        latest_job: null
      }
    ])
    vi.mocked(api.listChatSessions).mockResolvedValue([
      { id: 'session-1', course_id: 'course-1', title: 'SNMP 问答', created_at: '2026-05-29T14:00:00' }
    ])
    vi.mocked(api.listStudyCards).mockResolvedValue([
      {
        id: 'card-1',
        course_id: 'course-1',
        front: '什么是 SNMP trap?',
        back: '设备主动发送的事件通知。',
        source: 'ai',
        mastery: 2,
        created_at: '2026-05-29T14:00:00'
      }
    ])
    vi.mocked(api.listGeneratedQuestions).mockResolvedValue([])

    const wrapper = mount(LearningWorkflowChecklist, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    expect(wrapper.findAll('.workflow-step.done')).toHaveLength(6)
    expect(wrapper.text()).toContain('继续查看低掌握度卡片和最近错题')
    expect(wrapper.text()).not.toMatch(/璇|妫|鍒|鎬|�/)
  })
})
