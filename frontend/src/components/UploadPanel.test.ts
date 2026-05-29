import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '../api'
import { useStudyStore } from '../stores/study'
import UploadPanel from './UploadPanel.vue'

vi.mock('../api', () => ({
  api: {
    deleteDocument: vi.fn(),
    listDocumentChunks: vi.fn(),
    listDocumentJobs: vi.fn(),
    listDocuments: vi.fn(),
    retryDocument: vi.fn(),
    uploadDocument: vi.fn()
  }
}))

describe('UploadPanel', () => {
  beforeEach(() => {
    vi.mocked(api.listDocuments).mockReset()
    vi.mocked(api.listDocumentChunks).mockReset()
    vi.mocked(api.listDocumentJobs).mockReset()
    vi.mocked(api.deleteDocument).mockReset()
  })

  it('loads and renders document job history when a document is selected', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useStudyStore()
    store.selectedCourseId = 'course-1'
    vi.mocked(api.listDocuments).mockResolvedValue([
      {
        id: 'document-1',
        course_id: 'course-1',
        title: 'network.pdf',
        original_filename: 'network.pdf',
        kind: 'pdf',
        status: 'failed',
        error_message: 'parse failed',
        text_preview: '',
        created_at: '2026-05-29T14:00:00',
        updated_at: '2026-05-29T14:01:00',
        chunk_count: 0,
        latest_job: {
          id: 'job-2',
          status: 'failed',
          progress: 45,
          error_message: 'OCR timeout'
        }
      }
    ])
    vi.mocked(api.listDocumentChunks).mockResolvedValue([])
    vi.mocked(api.listDocumentJobs).mockResolvedValue([
      {
        id: 'job-2',
        document_id: 'document-1',
        job_type: 'ingest',
        status: 'failed',
        progress: 45,
        error_message: 'OCR timeout'
      },
      {
        id: 'job-1',
        document_id: 'document-1',
        job_type: 'ingest',
        status: 'queued',
        progress: 0,
        error_message: ''
      }
    ])

    const wrapper = mount(UploadPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    await wrapper.find('.document-row').trigger('click')
    await flushPromises()

    expect(api.listDocumentJobs).toHaveBeenCalledWith('document-1')
    expect(wrapper.text()).toContain('job-2')
    expect(wrapper.text()).toContain('OCR timeout')
    expect(wrapper.text()).toContain('45%')
  })

  it('deletes selected documents as a batch and clears removed rows', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useStudyStore()
    store.selectedCourseId = 'course-1'
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.mocked(api.listDocuments).mockResolvedValue([
      {
        id: 'document-1',
        course_id: 'course-1',
        title: 'network.pdf',
        original_filename: 'network.pdf',
        kind: 'pdf',
        status: 'ready',
        error_message: '',
        text_preview: 'network basics',
        created_at: '2026-05-29T14:00:00',
        updated_at: '2026-05-29T14:01:00',
        chunk_count: 3,
        latest_job: null
      },
      {
        id: 'document-2',
        course_id: 'course-1',
        title: 'routing.md',
        original_filename: 'routing.md',
        kind: 'markdown',
        status: 'ready',
        error_message: '',
        text_preview: 'routing notes',
        created_at: '2026-05-29T15:00:00',
        updated_at: '2026-05-29T15:01:00',
        chunk_count: 2,
        latest_job: null
      }
    ])
    vi.mocked(api.listDocumentChunks).mockResolvedValue([])
    vi.mocked(api.listDocumentJobs).mockResolvedValue([])
    vi.mocked(api.deleteDocument).mockResolvedValue({ ok: true })

    const wrapper = mount(UploadPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    await wrapper.findAll('[data-testid="document-select"]')[0].setValue(true)
    await wrapper.findAll('[data-testid="document-select"]')[1].setValue(true)
    await wrapper.find('[title="批量删除资料"]').trigger('click')
    await flushPromises()

    expect(api.deleteDocument).toHaveBeenCalledWith('document-1')
    expect(api.deleteDocument).toHaveBeenCalledWith('document-2')
    expect(wrapper.text()).not.toContain('network.pdf')
    expect(wrapper.text()).not.toContain('routing.md')
  })

  it('shows troubleshooting guidance for failed parsing jobs in readable Chinese', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useStudyStore()
    store.selectedCourseId = 'course-1'
    vi.mocked(api.listDocuments).mockResolvedValue([
      {
        id: 'document-1',
        course_id: 'course-1',
        title: 'scan.pdf',
        original_filename: 'scan.pdf',
        kind: 'pdf',
        status: 'failed',
        error_message: 'parse failed',
        text_preview: '',
        created_at: '2026-05-29T14:00:00',
        updated_at: '2026-05-29T14:01:00',
        chunk_count: 0,
        latest_job: {
          id: 'job-2',
          status: 'failed',
          progress: 45,
          error_message: 'OCR timeout'
        }
      }
    ])
    vi.mocked(api.listDocumentChunks).mockResolvedValue([])
    vi.mocked(api.listDocumentJobs).mockResolvedValue([])

    const wrapper = mount(UploadPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    await wrapper.find('.document-row').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('解析失败排查')
    expect(wrapper.text()).toContain('可以先重试解析')
    expect(wrapper.text()).toContain('OCR timeout')
    expect(wrapper.text()).not.toMatch(/璇|妫|鍒|鎬|�/)
  })
})
