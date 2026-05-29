import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '../api'
import { useStudyStore } from '../stores/study'
import ChatPanel from './ChatPanel.vue'

vi.mock('../api', () => ({
  api: {
    ask: vi.fn(),
    deleteChatSession: vi.fn(),
    getDocument: vi.fn(),
    listChatMessages: vi.fn(),
    listChatSessions: vi.fn(),
    listDocuments: vi.fn(),
    updateChatSession: vi.fn()
  }
}))

describe('ChatPanel', () => {
  beforeEach(() => {
    vi.mocked(api.ask).mockReset()
    vi.mocked(api.deleteChatSession).mockReset()
    vi.mocked(api.getDocument).mockReset()
    vi.mocked(api.listChatMessages).mockReset()
    vi.mocked(api.listChatSessions).mockReset()
    vi.mocked(api.listDocuments).mockReset()
    vi.mocked(api.updateChatSession).mockReset()
    vi.mocked(api.listDocuments).mockResolvedValue([])
  })

  it('opens a cited document preview and shows readable quality notes', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    useStudyStore().selectedCourseId = 'course-1'
    vi.mocked(api.listChatSessions).mockResolvedValue([])
    vi.mocked(api.ask).mockResolvedValue({
      answer: 'SNMP trap is event driven.',
      session_id: 'session-1',
      retrieval_confidence: 'high',
      quality_notes: ['引用资料较充分'],
      citations: [
        {
          chunk_id: 7,
          document_id: 'document-1',
          document_title: 'network.pdf',
          course_title: 'Computer Networks',
          text_preview: 'SNMP trap is an event notification.',
          page_number: 3,
          similarity: 0.92
        }
      ]
    })
    vi.mocked(api.getDocument).mockResolvedValue({
      id: 'document-1',
      course_id: 'course-1',
      title: 'network.pdf',
      original_filename: 'network.pdf',
      kind: 'pdf',
      status: 'ready',
      error_message: '',
      text_preview: 'Full parsed preview for SNMP trap.',
      created_at: '2026-05-29T14:00:00',
      updated_at: '2026-05-29T14:01:00',
      chunk_count: 12,
      latest_job: null
    })
    vi.mocked(api.listDocuments).mockResolvedValue([
      {
        id: 'document-1',
        course_id: 'course-1',
        title: 'network.pdf',
        original_filename: 'network.pdf',
        kind: 'pdf',
        status: 'ready',
        error_message: '',
        text_preview: 'Full parsed preview for SNMP trap.',
        created_at: '2026-05-29T14:00:00',
        updated_at: '2026-05-29T14:01:00',
        chunk_count: 12,
        latest_job: null
      }
    ])

    const wrapper = mount(ChatPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    await wrapper.find('[data-testid="ask-button"]').trigger('click')
    await flushPromises()
    await wrapper.find('[data-testid="citation-link"]').trigger('click')
    await flushPromises()

    expect(api.getDocument).toHaveBeenCalledWith('document-1')
    expect(wrapper.text()).toContain('Full parsed preview for SNMP trap.')
    expect(wrapper.text()).toContain('检索置信度：high')
    expect(wrapper.text()).toContain('引用资料较充分')
    expect(wrapper.text()).not.toMatch(/璇|妫|鍒|鎬|�/)
  })

  it('searches, renames, and deletes chat sessions with readable Chinese controls', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    useStudyStore().selectedCourseId = 'course-1'
    vi.spyOn(window, 'prompt').mockReturnValue('期末复习')
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.mocked(api.listChatSessions).mockResolvedValue([
      {
        id: 'session-1',
        course_id: 'course-1',
        title: 'SNMP 问答',
        created_at: '2026-05-29T14:00:00'
      },
      {
        id: 'session-2',
        course_id: 'course-1',
        title: 'HTTP 总结',
        created_at: '2026-05-29T15:00:00'
      }
    ])
    vi.mocked(api.updateChatSession).mockResolvedValue({
      id: 'session-1',
      course_id: 'course-1',
      title: '期末复习',
      created_at: '2026-05-29T14:00:00'
    })
    vi.mocked(api.deleteChatSession).mockResolvedValue({ ok: true })

    const wrapper = mount(ChatPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    await wrapper.find('[placeholder="搜索历史会话"]').setValue('SNMP')

    expect(wrapper.text()).toContain('SNMP 问答')
    expect(wrapper.text()).not.toContain('HTTP 总结')

    await wrapper.find('[title="重命名会话"]').trigger('click')
    await flushPromises()

    expect(api.updateChatSession).toHaveBeenCalledWith('session-1', '期末复习')
    expect(wrapper.text()).toContain('期末复习')

    await wrapper.find('[title="删除会话"]').trigger('click')
    await flushPromises()

    expect(api.deleteChatSession).toHaveBeenCalledWith('session-1')
    expect(wrapper.text()).not.toContain('期末复习')
  })

  it('passes selected document filters when asking a question', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    useStudyStore().selectedCourseId = 'course-1'
    vi.mocked(api.listChatSessions).mockResolvedValue([])
    vi.mocked(api.listDocuments).mockResolvedValue([
      {
        id: 'document-1',
        course_id: 'course-1',
        title: 'network.pdf',
        original_filename: 'network.pdf',
        kind: 'pdf',
        status: 'ready',
        error_message: '',
        text_preview: '',
        created_at: '2026-05-29T14:00:00',
        updated_at: '2026-05-29T14:01:00',
        chunk_count: 4,
        latest_job: null
      }
    ])
    vi.mocked(api.ask).mockResolvedValue({
      answer: 'Filtered answer.',
      session_id: 'session-1',
      citations: []
    })

    const wrapper = mount(ChatPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    await wrapper.find('[data-testid="chat-document-filter"]').setValue(true)
    await wrapper.find('[data-testid="ask-button"]').trigger('click')
    await flushPromises()

    expect(api.ask).toHaveBeenCalledWith('帮我总结 SNMP 协议考试重点', 'course-1', '', ['document-1'])
  })

  it('explains the next step when a course has no searchable documents', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    useStudyStore().selectedCourseId = 'course-1'
    vi.mocked(api.listChatSessions).mockResolvedValue([])
    vi.mocked(api.listDocuments).mockResolvedValue([])

    const wrapper = mount(ChatPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    expect(wrapper.text()).toContain('还没有可检索资料')
    expect(wrapper.text()).toContain('先在课程资料库上传并等待解析完成')
    expect(wrapper.find('[data-testid="ask-button"]').attributes('disabled')).toBeDefined()
    expect(wrapper.text()).not.toMatch(/璇|妫|鍒|鎬|�/)
  })
})
