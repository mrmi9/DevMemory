import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '../api'
import { useStudyStore } from '../stores/study'
import StudyToolsPanel from './StudyToolsPanel.vue'

vi.mock('../api', () => ({
  api: {
    addGeneratedQuestionToWrongNotes: vi.fn(),
    addWrongNote: vi.fn(),
    deleteGeneratedQuestion: vi.fn(),
    deleteStudyCard: vi.fn(),
    deleteWrongNote: vi.fn(),
    generate: vi.fn(),
    listGeneratedQuestions: vi.fn(),
    listStudyCards: vi.fn(),
    listWrongNotes: vi.fn(),
    updateGeneratedQuestion: vi.fn(),
    updateStudyCard: vi.fn(),
    updateStudyCardMastery: vi.fn()
  }
}))

describe('StudyToolsPanel', () => {
  beforeEach(() => {
    vi.mocked(api.listStudyCards).mockReset()
    vi.mocked(api.listGeneratedQuestions).mockReset()
    vi.mocked(api.listWrongNotes).mockReset()
    vi.mocked(api.updateGeneratedQuestion).mockReset()
    vi.mocked(api.updateStudyCard).mockReset()
    vi.mocked(api.updateStudyCardMastery).mockReset()
    vi.mocked(api.deleteGeneratedQuestion).mockReset()
    vi.mocked(api.deleteStudyCard).mockReset()
    vi.mocked(api.deleteWrongNote).mockReset()
    vi.spyOn(window, 'confirm').mockReturnValue(true)
  })

  it('notifies progress listeners after card mastery changes', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useStudyStore()
    store.selectedCourseId = 'course-1'
    const markProgressChanged = vi.spyOn(store, 'markProgressChanged')
    vi.mocked(api.listStudyCards).mockResolvedValue([
      {
        id: 'card-1',
        course_id: 'course-1',
        front: 'What is SNMP trap?',
        back: 'A device-initiated notification.',
        source: 'ai',
        mastery: 2,
        created_at: '2026-05-29T14:00:00'
      }
    ])
    vi.mocked(api.listGeneratedQuestions).mockResolvedValue([])
    vi.mocked(api.listWrongNotes).mockResolvedValue([])
    vi.mocked(api.updateStudyCardMastery).mockResolvedValue({
      id: 'card-1',
      course_id: 'course-1',
      front: 'What is SNMP trap?',
      back: 'A device-initiated notification.',
      source: 'ai',
      mastery: 3,
      created_at: '2026-05-29T14:00:00'
    })

    const wrapper = mount(StudyToolsPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    await wrapper.findAll('.mastery-control button')[1].trigger('click')
    await flushPromises()

    expect(api.updateStudyCardMastery).toHaveBeenCalledWith('card-1', 3)
    expect(markProgressChanged).toHaveBeenCalledTimes(1)
  })

  it('deletes study assets from their lists', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useStudyStore()
    store.selectedCourseId = 'course-1'
    const markProgressChanged = vi.spyOn(store, 'markProgressChanged')
    vi.mocked(api.listStudyCards).mockResolvedValue([
      {
        id: 'card-1',
        course_id: 'course-1',
        front: 'What is SNMP trap?',
        back: 'A device-initiated notification.',
        source: 'ai',
        mastery: 2,
        created_at: '2026-05-29T14:00:00'
      }
    ])
    vi.mocked(api.listGeneratedQuestions).mockResolvedValue([
      {
        id: 'question-1',
        course_id: 'course-1',
        question_type: 'short-answer',
        prompt: 'Explain SNMP trap.',
        answer: 'A notification.',
        explanation: '',
        created_at: '2026-05-29T14:00:00'
      }
    ])
    vi.mocked(api.listWrongNotes).mockResolvedValue([
      {
        id: 'wrong-1',
        course_id: 'course-1',
        title: 'SNMP mistake',
        original_question: 'What is trap?',
        user_answer: '',
        correct_answer: 'Notification.',
        analysis: 'Review trap flow.',
        tags: [],
        created_at: '2026-05-29T14:00:00'
      }
    ])
    vi.mocked(api.deleteStudyCard).mockResolvedValue({ ok: true })
    vi.mocked(api.deleteGeneratedQuestion).mockResolvedValue({ ok: true })
    vi.mocked(api.deleteWrongNote).mockResolvedValue({ ok: true })

    const wrapper = mount(StudyToolsPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    await wrapper.find('[title="删除卡片"]').trigger('click')
    await wrapper.find('[title="删除试题"]').trigger('click')
    await wrapper.find('[title="删除错题"]').trigger('click')
    await flushPromises()

    expect(api.deleteStudyCard).toHaveBeenCalledWith('card-1')
    expect(api.deleteGeneratedQuestion).toHaveBeenCalledWith('question-1')
    expect(api.deleteWrongNote).toHaveBeenCalledWith('wrong-1')
    expect(wrapper.text()).not.toContain('What is SNMP trap?')
    expect(wrapper.text()).not.toContain('Explain SNMP trap.')
    expect(wrapper.text()).not.toContain('SNMP mistake')
    expect(markProgressChanged).toHaveBeenCalledTimes(1)
  })

  it('edits a study card front and back in place', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useStudyStore()
    store.selectedCourseId = 'course-1'
    vi.spyOn(window, 'prompt')
      .mockReturnValueOnce('What is an SNMP trap?')
      .mockReturnValueOnce('An event notification sent by a device.')
    vi.mocked(api.listStudyCards).mockResolvedValue([
      {
        id: 'card-1',
        course_id: 'course-1',
        front: 'What is SNMP trap?',
        back: 'A device-initiated notification.',
        source: 'ai',
        mastery: 2,
        created_at: '2026-05-29T14:00:00'
      }
    ])
    vi.mocked(api.listGeneratedQuestions).mockResolvedValue([])
    vi.mocked(api.listWrongNotes).mockResolvedValue([])
    vi.mocked(api.updateStudyCard).mockResolvedValue({
      id: 'card-1',
      course_id: 'course-1',
      front: 'What is an SNMP trap?',
      back: 'An event notification sent by a device.',
      source: 'ai',
      mastery: 2,
      created_at: '2026-05-29T14:00:00'
    })

    const wrapper = mount(StudyToolsPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    await wrapper.find('[title="编辑卡片"]').trigger('click')
    await flushPromises()

    expect(api.updateStudyCard).toHaveBeenCalledWith('card-1', {
      front: 'What is an SNMP trap?',
      back: 'An event notification sent by a device.'
    })
    expect(wrapper.text()).toContain('What is an SNMP trap?')
    expect(wrapper.text()).toContain('An event notification sent by a device.')
  })

  it('edits a generated question in place', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useStudyStore()
    store.selectedCourseId = 'course-1'
    vi.spyOn(window, 'prompt')
      .mockReturnValueOnce('Explain an SNMP trap.')
      .mockReturnValueOnce('It is an event notification sent by a managed device.')
      .mockReturnValueOnce('Trap messages are device initiated.')
    vi.mocked(api.listStudyCards).mockResolvedValue([])
    vi.mocked(api.listGeneratedQuestions).mockResolvedValue([
      {
        id: 'question-1',
        course_id: 'course-1',
        question_type: 'short-answer',
        prompt: 'Explain SNMP trap.',
        answer: 'A notification.',
        explanation: '',
        created_at: '2026-05-29T14:00:00'
      }
    ])
    vi.mocked(api.listWrongNotes).mockResolvedValue([])
    vi.mocked(api.updateGeneratedQuestion).mockResolvedValue({
      id: 'question-1',
      course_id: 'course-1',
      question_type: 'short-answer',
      prompt: 'Explain an SNMP trap.',
      answer: 'It is an event notification sent by a managed device.',
      explanation: 'Trap messages are device initiated.',
      created_at: '2026-05-29T14:00:00'
    })

    const wrapper = mount(StudyToolsPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    await wrapper.find('[title="编辑试题"]').trigger('click')
    await flushPromises()

    expect(api.updateGeneratedQuestion).toHaveBeenCalledWith('question-1', {
      prompt: 'Explain an SNMP trap.',
      answer: 'It is an event notification sent by a managed device.',
      explanation: 'Trap messages are device initiated.'
    })
    expect(wrapper.text()).toContain('Explain an SNMP trap.')
    expect(wrapper.text()).toContain('It is an event notification sent by a managed device.')
    expect(wrapper.text()).toContain('Trap messages are device initiated.')
  })
})
