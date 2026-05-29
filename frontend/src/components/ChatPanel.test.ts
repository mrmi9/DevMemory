import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '../api'
import { useStudyStore } from '../stores/study'
import ChatPanel from './ChatPanel.vue'

vi.mock('../api', () => ({
  api: {
    ask: vi.fn(),
    deleteChatSession: vi.fn(),
    getDocument: vi.fn(),
    addChatMessageToWrongNotes: vi.fn(),
    generateQuestionsFromChatMessage: vi.fn(),
    listChatMessages: vi.fn(),
    listChatSessions: vi.fn(),
    listDocuments: vi.fn(),
    saveChatMessageAsStudyCard: vi.fn(),
    updateChatSession: vi.fn()
  }
}))

describe('ChatPanel', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    document.body.innerHTML = ''
  })

  beforeEach(() => {
    vi.mocked(api.ask).mockReset()
    vi.mocked(api.addChatMessageToWrongNotes).mockReset()
    vi.mocked(api.deleteChatSession).mockReset()
    vi.mocked(api.generateQuestionsFromChatMessage).mockReset()
    vi.mocked(api.getDocument).mockReset()
    vi.mocked(api.listChatMessages).mockReset()
    vi.mocked(api.listChatSessions).mockReset()
    vi.mocked(api.listDocuments).mockReset()
    vi.mocked(api.saveChatMessageAsStudyCard).mockReset()
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
    const promptSpy = vi.spyOn(window, 'prompt').mockImplementation(() => {
      throw new Error('window.prompt should not be used')
    })
    const confirmSpy = vi.spyOn(window, 'confirm').mockImplementation(() => {
      throw new Error('window.confirm should not be used')
    })
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
    const renameInput = document.body.querySelector('[data-testid="session-title-input"]') as HTMLInputElement
    expect(document.body.textContent).toContain('重命名会话')
    renameInput.value = '期末复习'
    renameInput.dispatchEvent(new Event('input'))
    ;(document.body.querySelector('[data-testid="modal-confirm"]') as HTMLButtonElement).click()
    await flushPromises()

    expect(api.updateChatSession).toHaveBeenCalledWith('session-1', '期末复习')
    expect(wrapper.text()).toContain('期末复习')
    expect(promptSpy).not.toHaveBeenCalled()

    await wrapper.find('[title="删除会话"]').trigger('click')
    await flushPromises()
    expect(document.body.textContent).toContain('该会话历史也会被删除')
    ;(document.body.querySelector('[data-testid="modal-confirm"]') as HTMLButtonElement).click()
    await flushPromises()

    expect(api.deleteChatSession).toHaveBeenCalledWith('session-1')
    expect(wrapper.text()).not.toContain('期末复习')
    expect(confirmSpy).not.toHaveBeenCalled()
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

  it('turns a cited assistant answer into study assets', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    useStudyStore().selectedCourseId = 'course-1'
    vi.mocked(api.listChatSessions).mockResolvedValue([
      {
        id: 'session-1',
        course_id: 'course-1',
        title: 'SNMP 问答',
        created_at: '2026-05-29T14:00:00'
      }
    ])
    vi.mocked(api.listChatMessages).mockResolvedValue([
      {
        id: 'message-1',
        role: 'user',
        content: '什么是 SNMP trap？',
        citations: [],
        created_at: '2026-05-29T14:00:00'
      },
      {
        id: 'message-2',
        role: 'assistant',
        content: 'SNMP trap 是设备主动发送的事件通知。',
        citations: [
          {
            chunk_id: 7,
            document_id: 'document-1',
            document_title: 'network.pdf',
            course_title: 'Computer Networks',
            text_preview: 'trap notification',
            page_number: 3,
            similarity: 0.92
          }
        ],
        created_at: '2026-05-29T14:01:00'
      }
    ])
    vi.mocked(api.saveChatMessageAsStudyCard).mockResolvedValue({
      id: 'card-1',
      course_id: 'course-1',
      front: '什么是 SNMP trap？',
      back: 'SNMP trap 是设备主动发送的事件通知。',
      source: 'chat',
      mastery: 0,
      created_at: '2026-05-29T14:02:00'
    })
    vi.mocked(api.generateQuestionsFromChatMessage).mockResolvedValue([
      {
        id: 'question-1',
        course_id: 'course-1',
        question_type: 'short-answer',
        prompt: 'SNMP trap 的触发方式是什么？',
        answer: '设备主动触发。',
        explanation: 'trap 是事件驱动。',
        created_at: '2026-05-29T14:03:00'
      }
    ])
    vi.mocked(api.addChatMessageToWrongNotes).mockResolvedValue({
      id: 'wrong-1',
      course_id: 'course-1',
      title: '什么是 SNMP trap？',
      original_question: '什么是 SNMP trap？',
      user_answer: '',
      correct_answer: 'SNMP trap 是设备主动发送的事件通知。',
      analysis: '来源：network.pdf',
      tags: ['chat-answer', '重点'],
      created_at: '2026-05-29T14:04:00'
    })

    const wrapper = mount(ChatPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    await wrapper.find('.session-open-button').trigger('click')
    await flushPromises()
    await wrapper.find('[data-testid="save-answer-card"]').trigger('click')
    await wrapper.find('[data-testid="generate-answer-questions"]').trigger('click')
    await wrapper.find('[data-testid="add-answer-wrong-note"]').trigger('click')
    await flushPromises()

    expect(api.saveChatMessageAsStudyCard).toHaveBeenCalledWith('message-2')
    expect(api.generateQuestionsFromChatMessage).toHaveBeenCalledWith('message-2', 5)
    expect(api.addChatMessageToWrongNotes).toHaveBeenCalledWith('message-2')
    expect(wrapper.text()).toContain('已保存为复习卡片')
    expect(wrapper.text()).toContain('已生成 1 道练习题')
    expect(wrapper.text()).toContain('已加入重点')
  })

  it('does not offer asset actions for answers without citations', async () => {
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
      answer: '资料不足时的占位回答。',
      session_id: 'session-1',
      assistant_message_id: 'message-2',
      retrieval_confidence: 'none',
      quality_notes: ['没有检索到资料'],
      citations: []
    })

    const wrapper = mount(ChatPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    await wrapper.find('[data-testid="ask-button"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-testid="save-answer-card"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('资料不足')
  })

  it('supports following up from an answer and reusing cited documents as the ask scope', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    useStudyStore().selectedCourseId = 'course-1'
    vi.mocked(api.listChatSessions).mockResolvedValue([
      {
        id: 'session-1',
        course_id: 'course-1',
        title: 'SNMP 问答',
        created_at: '2026-05-29T14:00:00'
      }
    ])
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
      },
      {
        id: 'document-2',
        course_id: 'course-1',
        title: 'other.pdf',
        original_filename: 'other.pdf',
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
    vi.mocked(api.listChatMessages).mockResolvedValue([
      {
        id: 'message-2',
        role: 'assistant',
        content: 'SNMP trap 是设备主动发送的事件通知。',
        citations: [
          {
            chunk_id: 7,
            document_id: 'document-1',
            document_title: 'network.pdf',
            course_title: 'Computer Networks',
            text_preview: 'trap notification',
            page_number: 3,
            similarity: 0.92
          }
        ],
        created_at: '2026-05-29T14:01:00'
      }
    ])

    const wrapper = mount(ChatPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    await wrapper.find('.session-open-button').trigger('click')
    await flushPromises()
    await wrapper.find('[data-testid="follow-up-answer"]').trigger('click')
    expect((wrapper.find('textarea').element as HTMLTextAreaElement).value).toContain('基于上面的回答')

    await wrapper.find('[data-testid="use-cited-documents"]').trigger('click')
    expect(wrapper.findAll('[data-testid="chat-document-filter"]')[0].element).toHaveProperty('checked', true)
    expect(wrapper.findAll('[data-testid="chat-document-filter"]')[1].element).toHaveProperty('checked', false)
  })
})
