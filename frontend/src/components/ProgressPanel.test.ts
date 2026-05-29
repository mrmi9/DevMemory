import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '../api'
import { useStudyStore } from '../stores/study'
import ProgressPanel from './ProgressPanel.vue'

vi.mock('../api', () => ({
  api: {
    progressOverview: vi.fn(),
    updateStudyCardMastery: vi.fn()
  }
}))

describe('ProgressPanel', () => {
  beforeEach(() => {
    vi.mocked(api.progressOverview).mockReset()
    vi.mocked(api.updateStudyCardMastery).mockReset()
  })

  it('reloads overview when study progress changes', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    vi.mocked(api.progressOverview)
      .mockResolvedValueOnce({ courses: 1, records: 1, average_mastery: 2, items: [] })
      .mockResolvedValueOnce({ courses: 1, records: 1, average_mastery: 4, items: [] })

    const wrapper = mount(ProgressPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    expect(wrapper.text()).toContain('2')

    ;(useStudyStore() as unknown as { markProgressChanged: () => void }).markProgressChanged()
    await flushPromises()

    expect(api.progressOverview).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('4')
  })

  it('shows a daily review queue and records review actions', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    vi.mocked(api.progressOverview).mockResolvedValue({
      courses: 1,
      records: 2,
      average_mastery: 1,
      items: [],
      review: {
        today_due: 2,
        low_mastery: 2,
        mastered: 0,
        cards: [
          {
            id: 'card-1',
            course_id: 'course-1',
            front: 'What is SNMP trap?',
            back: 'A device notification.',
            source: 'chat',
            mastery: 0,
            review_count: 0,
            last_reviewed_at: null,
            next_review_at: null,
            review_state: 'not_started',
            next_review_label: '今天'
          }
        ],
        recent_wrong_notes: [
          {
            id: 'wrong-1',
            course_id: 'course-1',
            title: 'SNMP trap mistake',
            original_question: 'Trap timing?',
            user_answer: '',
            correct_answer: 'Event driven.',
            analysis: 'Review trap triggers.',
            tags: ['重点'],
            created_at: '2026-05-29T13:00:00'
          }
        ]
      }
    })
    vi.mocked(api.updateStudyCardMastery).mockResolvedValue({
      id: 'card-1',
      course_id: 'course-1',
      front: 'What is SNMP trap?',
      back: 'A device notification.',
      source: 'chat',
      mastery: 4,
      review_count: 1,
      last_reviewed_at: '2026-05-29T12:00:00',
      next_review_at: '2026-06-01T12:00:00',
      created_at: '2026-05-29T14:00:00'
    })

    const wrapper = mount(ProgressPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    expect(wrapper.text()).toContain('今日待复习')
    expect(wrapper.text()).toContain('2')
    expect(wrapper.text()).toContain('低掌握')
    expect(wrapper.text()).toContain('What is SNMP trap?')
    expect(wrapper.text()).toContain('下次复习：今天')
    expect(wrapper.text()).toContain('已复习 0 次')
    expect(wrapper.text()).toContain('SNMP trap mistake')

    await wrapper.find('[data-testid="review-good"]').trigger('click')
    await flushPromises()

    expect(api.updateStudyCardMastery).toHaveBeenCalledWith('card-1', 4)
    expect(api.progressOverview).toHaveBeenCalledTimes(2)
  })

  it('labels mastered cards clearly when they return to the due queue', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    vi.mocked(api.progressOverview).mockResolvedValue({
      courses: 1,
      records: 1,
      average_mastery: 4,
      items: [],
      review: {
        today_due: 1,
        low_mastery: 0,
        mastered: 1,
        cards: [
          {
            id: 'card-mastered-due',
            course_id: 'course-1',
            front: 'Mastered but due',
            back: 'Long term retention.',
            source: 'ai',
            mastery: 4,
            review_count: 3,
            last_reviewed_at: '2026-05-20T10:00:00',
            next_review_at: '2026-05-28T10:00:00',
            review_state: 'mastered',
            next_review_label: '已逾期',
            created_at: '2026-05-20T09:00:00'
          }
        ],
        recent_wrong_notes: []
      }
    })

    const wrapper = mount(ProgressPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    const cardText = wrapper.find('.review-card').text()
    expect(cardText).toContain('Mastered but due')
    expect(cardText).toContain('已掌握')
    expect(cardText).toContain('下次复习：已逾期')
    expect(cardText).toContain('已复习 3 次')
  })
})
