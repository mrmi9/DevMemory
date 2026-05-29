import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

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
  afterEach(() => {
    vi.restoreAllMocks()
    document.body.innerHTML = ''
  })

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
  })

  it('keeps the study topic as placeholder guidance and disables generation until users type', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useStudyStore()
    store.selectedCourseId = 'course-1'
    vi.mocked(api.listStudyCards).mockResolvedValue([])
    vi.mocked(api.listGeneratedQuestions).mockResolvedValue([])
    vi.mocked(api.listWrongNotes).mockResolvedValue([])

    const wrapper = mount(StudyToolsPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    const topicInput = wrapper.find('input')
    expect((topicInput.element as HTMLInputElement).value).toBe('')
    expect(topicInput.attributes('placeholder')).toBe('例如：SNMP 协议')
    expect((wrapper.find('[data-testid="generate-cards-button"]').element as HTMLButtonElement).disabled).toBe(true)
    expect((wrapper.find('[data-testid="generate-questions-button"]').element as HTMLButtonElement).disabled).toBe(true)

    await topicInput.setValue('SNMP 协议')

    expect((wrapper.find('[data-testid="generate-cards-button"]').element as HTMLButtonElement).disabled).toBe(false)
    expect((wrapper.find('[data-testid="generate-questions-button"]').element as HTMLButtonElement).disabled).toBe(false)
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

  it('deletes study assets from their lists with readable controls', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useStudyStore()
    store.selectedCourseId = 'course-1'
    const markProgressChanged = vi.spyOn(store, 'markProgressChanged')
    const confirmSpy = vi.spyOn(window, 'confirm').mockImplementation(() => {
      throw new Error('window.confirm should not be used')
    })
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
    await flushPromises()
    expect(document.body.textContent).toContain('删除复习卡片')
    ;(document.body.querySelector('[data-testid="modal-confirm"]') as HTMLButtonElement).click()
    await flushPromises()

    await wrapper.find('[title="删除试题"]').trigger('click')
    await flushPromises()
    expect(document.body.textContent).toContain('删除练习题')
    ;(document.body.querySelector('[data-testid="modal-confirm"]') as HTMLButtonElement).click()
    await flushPromises()

    await wrapper.find('[title="删除错题"]').trigger('click')
    await flushPromises()
    expect(document.body.textContent).toContain('删除错题记录')
    ;(document.body.querySelector('[data-testid="modal-confirm"]') as HTMLButtonElement).click()
    await flushPromises()

    expect(api.deleteStudyCard).toHaveBeenCalledWith('card-1')
    expect(api.deleteGeneratedQuestion).toHaveBeenCalledWith('question-1')
    expect(api.deleteWrongNote).toHaveBeenCalledWith('wrong-1')
    expect(wrapper.text()).not.toContain('What is SNMP trap?')
    expect(wrapper.text()).not.toContain('Explain SNMP trap.')
    expect(wrapper.text()).not.toContain('SNMP mistake')
    expect(markProgressChanged).toHaveBeenCalledTimes(1)
    expect(confirmSpy).not.toHaveBeenCalled()
  })

  it('edits a study card front and back in place', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useStudyStore()
    store.selectedCourseId = 'course-1'
    const promptSpy = vi.spyOn(window, 'prompt').mockImplementation(() => {
      throw new Error('window.prompt should not be used')
    })
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
    ;(document.body.querySelector('[data-testid="card-front-input"]') as HTMLTextAreaElement).value = 'What is an SNMP trap?'
    ;(document.body.querySelector('[data-testid="card-front-input"]') as HTMLTextAreaElement).dispatchEvent(new Event('input'))
    ;(document.body.querySelector('[data-testid="card-back-input"]') as HTMLTextAreaElement).value = 'An event notification sent by a device.'
    ;(document.body.querySelector('[data-testid="card-back-input"]') as HTMLTextAreaElement).dispatchEvent(new Event('input'))
    ;(document.body.querySelector('[data-testid="modal-confirm"]') as HTMLButtonElement).click()
    await flushPromises()

    expect(api.updateStudyCard).toHaveBeenCalledWith('card-1', {
      front: 'What is an SNMP trap?',
      back: 'An event notification sent by a device.'
    })
    expect(wrapper.text()).toContain('What is an SNMP trap?')
    expect(wrapper.text()).toContain('An event notification sent by a device.')
    expect(promptSpy).not.toHaveBeenCalled()
  })

  it('edits a generated question in place', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useStudyStore()
    store.selectedCourseId = 'course-1'
    const promptSpy = vi.spyOn(window, 'prompt').mockImplementation(() => {
      throw new Error('window.prompt should not be used')
    })
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
    ;(document.body.querySelector('[data-testid="question-prompt-input"]') as HTMLTextAreaElement).value = 'Explain an SNMP trap.'
    ;(document.body.querySelector('[data-testid="question-prompt-input"]') as HTMLTextAreaElement).dispatchEvent(new Event('input'))
    ;(document.body.querySelector('[data-testid="question-answer-input"]') as HTMLTextAreaElement).value = 'It is an event notification sent by a managed device.'
    ;(document.body.querySelector('[data-testid="question-answer-input"]') as HTMLTextAreaElement).dispatchEvent(new Event('input'))
    ;(document.body.querySelector('[data-testid="question-explanation-input"]') as HTMLTextAreaElement).value = 'Trap messages are device initiated.'
    ;(document.body.querySelector('[data-testid="question-explanation-input"]') as HTMLTextAreaElement).dispatchEvent(new Event('input'))
    ;(document.body.querySelector('[data-testid="modal-confirm"]') as HTMLButtonElement).click()
    await flushPromises()

    expect(api.updateGeneratedQuestion).toHaveBeenCalledWith('question-1', {
      prompt: 'Explain an SNMP trap.',
      answer: 'It is an event notification sent by a managed device.',
      explanation: 'Trap messages are device initiated.'
    })
    expect(wrapper.text()).toContain('Explain an SNMP trap.')
    expect(wrapper.text()).toContain('It is an event notification sent by a managed device.')
    expect(wrapper.text()).toContain('Trap messages are device initiated.')
    expect(promptSpy).not.toHaveBeenCalled()
  })
})
