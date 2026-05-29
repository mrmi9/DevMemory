import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '../api'
import { useStudyStore } from '../stores/study'
import ProgressPanel from './ProgressPanel.vue'

vi.mock('../api', () => ({
  api: {
    progressOverview: vi.fn()
  }
}))

describe('ProgressPanel', () => {
  beforeEach(() => {
    vi.mocked(api.progressOverview).mockReset()
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
})
