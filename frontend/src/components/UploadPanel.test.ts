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
    updateDocumentMetadata: vi.fn(),
    uploadDocument: vi.fn()
  }
}))

describe('UploadPanel', () => {
  beforeEach(() => {
    vi.mocked(api.listDocuments).mockReset()
    vi.mocked(api.listDocumentChunks).mockReset()
    vi.mocked(api.listDocumentJobs).mockReset()
    vi.mocked(api.deleteDocument).mockReset()
    vi.mocked(api.retryDocument).mockReset()
    vi.mocked(api.updateDocumentMetadata).mockReset()
    vi.mocked(api.uploadDocument).mockReset()
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

  it('searches, filters, and sorts large document libraries', async () => {
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
        status: 'failed',
        error_message: 'parse failed',
        text_preview: 'routing protocols',
        created_at: '2026-05-29T16:00:00',
        updated_at: '2026-05-29T16:01:00',
        chunk_count: 0,
        latest_job: { id: 'job-2', status: 'failed', progress: 45, error_message: 'OCR timeout' }
      },
      {
        id: 'document-3',
        course_id: 'course-1',
        title: 'chapter-one.docx',
        original_filename: 'chapter-one.docx',
        kind: 'word',
        status: 'processing',
        error_message: '',
        text_preview: 'chapter one notes',
        created_at: '2026-05-29T15:00:00',
        updated_at: '2026-05-29T15:01:00',
        chunk_count: 0,
        latest_job: { id: 'job-3', status: 'processing', progress: 30, error_message: '' }
      }
    ])

    const wrapper = mount(UploadPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    await wrapper.find('[data-testid="document-search"]').setValue('routing')
    expect(wrapper.text()).toContain('routing.md')
    expect(wrapper.text()).not.toContain('network.pdf')

    await wrapper.find('[data-testid="document-search"]').setValue('')
    await wrapper.find('[data-testid="document-status-filter"]').setValue('searchable')
    expect(wrapper.text()).toContain('network.pdf')
    expect(wrapper.text()).not.toContain('routing.md')
    expect(wrapper.text()).not.toContain('chapter-one.docx')

    await wrapper.find('[data-testid="document-status-filter"]').setValue('all')
    await wrapper.find('[data-testid="document-sort"]').setValue('type')
    const renderedTitles = wrapper.findAll('[data-testid="document-title"]').map((node) => node.text())
    expect(renderedTitles).toEqual(['routing.md', 'network.pdf', 'chapter-one.docx'])
  })

  it('retries every failed document in a batch', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useStudyStore()
    store.selectedCourseId = 'course-1'
    vi.mocked(api.listDocuments).mockResolvedValue([
      {
        id: 'document-1',
        course_id: 'course-1',
        title: 'failed-a.pdf',
        original_filename: 'failed-a.pdf',
        kind: 'pdf',
        status: 'failed',
        error_message: 'parse failed',
        text_preview: '',
        created_at: '2026-05-29T14:00:00',
        updated_at: '2026-05-29T14:01:00',
        chunk_count: 0,
        latest_job: { id: 'job-1', status: 'failed', progress: 45, error_message: 'OCR timeout' }
      },
      {
        id: 'document-2',
        course_id: 'course-1',
        title: 'ready.md',
        original_filename: 'ready.md',
        kind: 'markdown',
        status: 'ready',
        error_message: '',
        text_preview: 'ready notes',
        created_at: '2026-05-29T15:00:00',
        updated_at: '2026-05-29T15:01:00',
        chunk_count: 2,
        latest_job: null
      },
      {
        id: 'document-3',
        course_id: 'course-1',
        title: 'failed-b.docx',
        original_filename: 'failed-b.docx',
        kind: 'word',
        status: 'ready',
        error_message: '',
        text_preview: '',
        created_at: '2026-05-29T16:00:00',
        updated_at: '2026-05-29T16:01:00',
        chunk_count: 0,
        latest_job: { id: 'job-3', status: 'failed', progress: 20, error_message: 'parse failed' }
      }
    ])
    vi.mocked(api.retryDocument).mockResolvedValue({
      id: 'document-1',
      course_id: 'course-1',
      title: 'failed-a.pdf',
      original_filename: 'failed-a.pdf',
      kind: 'pdf',
      status: 'uploaded',
      error_message: '',
      text_preview: '',
      created_at: '2026-05-29T14:00:00',
      updated_at: '2026-05-29T14:01:00',
      chunk_count: 0,
      latest_job: { id: 'job-retry', status: 'queued', progress: 0, error_message: '' }
    })

    const wrapper = mount(UploadPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    await wrapper.find('[data-testid="retry-failed-documents"]').trigger('click')
    await flushPromises()

    expect(api.retryDocument).toHaveBeenCalledWith('document-1')
    expect(api.retryDocument).toHaveBeenCalledWith('document-3')
    expect(api.retryDocument).not.toHaveBeenCalledWith('document-2')
    expect(wrapper.text()).toContain('已重新加入 2 份失败资料的解析队列')
  })

  it('warns before uploading a duplicate filename', async () => {
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
        status: 'ready',
        error_message: '',
        text_preview: 'network basics',
        created_at: '2026-05-29T14:00:00',
        updated_at: '2026-05-29T14:01:00',
        chunk_count: 3,
        latest_job: null
      }
    ])

    const wrapper = mount(UploadPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    const input = wrapper.find('input[type="file"]')
    Object.defineProperty(input.element, 'files', {
      value: [new File(['duplicate'], 'network.pdf', { type: 'application/pdf' })],
      configurable: true
    })
    await input.trigger('change')
    await flushPromises()

    expect(api.uploadDocument).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('已存在同名资料“network.pdf”')
  })

  it('edits document chapter and tags for course material grouping', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useStudyStore()
    store.selectedCourseId = 'course-1'
    vi.mocked(api.listDocuments).mockResolvedValue([
      {
        id: 'document-1',
        course_id: 'course-1',
        title: 'transport.md',
        original_filename: 'transport.md',
        kind: 'markdown',
        status: 'ready',
        error_message: '',
        text_preview: 'transport layer notes',
        created_at: '2026-05-29T14:00:00',
        updated_at: '2026-05-29T14:01:00',
        chunk_count: 3,
        chapter: '第 1 章',
        tags: ['重点'],
        latest_job: null
      }
    ])
    vi.mocked(api.listDocumentChunks).mockResolvedValue([])
    vi.mocked(api.listDocumentJobs).mockResolvedValue([])
    vi.mocked(api.updateDocumentMetadata).mockResolvedValue({
      id: 'document-1',
      course_id: 'course-1',
      title: 'transport.md',
      original_filename: 'transport.md',
      kind: 'markdown',
      status: 'ready',
      error_message: '',
      text_preview: 'transport layer notes',
      created_at: '2026-05-29T14:00:00',
      updated_at: '2026-05-29T14:01:00',
      chunk_count: 3,
      chapter: '第 2 章 传输层',
      tags: ['重点', '考试'],
      latest_job: null
    })

    const wrapper = mount(UploadPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    await wrapper.find('.document-row').trigger('click')
    await flushPromises()
    await wrapper.find('[data-testid="document-chapter-input"]').setValue('第 2 章 传输层')
    await wrapper.find('[data-testid="document-tags-input"]').setValue('重点, 考试, 重点')
    await wrapper.find('[data-testid="save-document-metadata"]').trigger('click')
    await flushPromises()

    expect(api.updateDocumentMetadata).toHaveBeenCalledWith('document-1', {
      chapter: '第 2 章 传输层',
      tags: ['重点', '考试']
    })
    expect(wrapper.text()).toContain('第 2 章 传输层')
    expect(wrapper.text()).toContain('考试')

    await wrapper.find('[data-testid="document-search"]').setValue('考试')
    expect(wrapper.text()).toContain('transport.md')
  })
})
