import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'

vi.mock('../composables/useApi.js', () => ({
  useApi: vi.fn(() => ({
    fetchItems: vi.fn().mockResolvedValue([
      { id: 'item1', name: 'National ID 123', region: 'me-central2' },
    ]),
    fetchDocuments: vi.fn().mockResolvedValue([]),
    uploadDocument: vi.fn(),
  })),
}))

// Stub DocumentUpload to isolate RecordList behavior
vi.mock('../components/DocumentUpload.vue', () => ({
  default: {
    template: '<div class="doc-stub"></div>',
    props: ['itemId', 'token'],
  },
}))

const { default: RecordList } = await import('../components/RecordList.vue')

describe('RecordList', () => {
  it('renders items after mount', async () => {
    const wrapper = mount(RecordList, { props: { token: ref('tok') } })
    await flushPromises()
    expect(wrapper.text()).toContain('National ID 123')
    expect(wrapper.text()).toContain('me-central2')
  })

  it('shows empty state when no items', async () => {
    const { useApi } = await import('../composables/useApi.js')
    useApi.mockReturnValueOnce({
      fetchItems: vi.fn().mockResolvedValue([]),
      fetchDocuments: vi.fn().mockResolvedValue([]),
      uploadDocument: vi.fn(),
    })
    const wrapper = mount(RecordList, { props: { token: ref('tok') } })
    await flushPromises()
    expect(wrapper.text()).toContain('No records found')
  })

  it('exposes refresh() that reloads items', async () => {
    const { useApi } = await import('../composables/useApi.js')
    const fetchItems = vi.fn()
      .mockResolvedValueOnce([{ id: '1', name: 'First Record', region: 'me-central2' }])
      .mockResolvedValueOnce([{ id: '2', name: 'Second Record', region: 'me-central2' }])
    useApi.mockReturnValueOnce({ fetchItems, fetchDocuments: vi.fn().mockResolvedValue([]), uploadDocument: vi.fn() })

    const wrapper = mount(RecordList, { props: { token: ref('tok') } })
    await flushPromises()
    expect(wrapper.text()).toContain('First Record')

    await wrapper.vm.refresh()
    await flushPromises()
    expect(wrapper.text()).toContain('Second Record')
  })
})
