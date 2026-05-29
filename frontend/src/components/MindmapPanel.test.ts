import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '../api'
import { useStudyStore } from '../stores/study'
import MindmapPanel from './MindmapPanel.vue'

vi.mock('markmap-lib', () => ({
  Transformer: class {
    transform(markdown: string) {
      return { root: { markdown } }
    }
  }
}))

vi.mock('markmap-view', () => ({
  Markmap: {
    create: vi.fn(() => ({ fit: vi.fn(), setData: vi.fn() }))
  }
}))

vi.mock('../api', () => ({
  api: {
    deleteMindmap: vi.fn(),
    generateMindmap: vi.fn(),
    listMindmaps: vi.fn()
  }
}))

describe('MindmapPanel bundle boundary', () => {
  it('loads markmap libraries lazily instead of in the main bundle', () => {
    const source = readFileSync(resolve(process.cwd(), 'src/components/MindmapPanel.vue'), 'utf8')

    expect(source).not.toContain("from 'markmap-lib'")
    expect(source).not.toContain("from 'markmap-view'")
  })

  beforeEach(() => {
    vi.mocked(api.listMindmaps).mockReset()
    vi.mocked(api.deleteMindmap).mockReset()
    vi.spyOn(window, 'confirm').mockReturnValue(true)
  })

  it('deletes the selected mindmap from the saved list', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useStudyStore()
    store.selectedCourseId = 'course-1'

    vi.mocked(api.listMindmaps).mockResolvedValue([
      {
        id: 'mindmap-1',
        course_id: 'course-1',
        title: 'SNMP 导图',
        markdown: '# SNMP\n- Trap',
        created_at: '2026-05-29T15:00:00'
      }
    ])
    vi.mocked(api.deleteMindmap).mockResolvedValue({ ok: true })

    const wrapper = mount(MindmapPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    await wrapper.find('[title="删除思维导图"]').trigger('click')
    await flushPromises()

    expect(api.listMindmaps).toHaveBeenCalledWith('course-1')
    expect(api.deleteMindmap).toHaveBeenCalledWith('mindmap-1')
    expect(wrapper.text()).not.toContain('SNMP 导图')
  })
})
