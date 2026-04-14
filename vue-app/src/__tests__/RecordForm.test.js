import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'

vi.mock('../composables/useApi.js', () => ({
  useApi: vi.fn(() => ({
    createItem: vi.fn().mockResolvedValue({ id: 'new-id', name: 'Test Item', region: 'me-central2' }),
  })),
}))

const { default: RecordForm } = await import('../components/RecordForm.vue')

describe('RecordForm', () => {
  it('renders the text input and SAVE button', () => {
    const wrapper = mount(RecordForm, { props: { token: ref('tok') } })
    expect(wrapper.find('input[type="text"]').exists()).toBe(true)
    expect(wrapper.find('button[type="submit"]').text()).toMatch(/SAVE/i)
  })

  it('emits created event after successful submit', async () => {
    const wrapper = mount(RecordForm, { props: { token: ref('tok') } })
    await wrapper.find('input').setValue('National ID 12345')
    await wrapper.find('form').trigger('submit')
    await new Promise(r => setTimeout(r, 0)) // flush microtasks
    expect(wrapper.emitted('created')).toBeTruthy()
  })

  it('clears the input after successful submit', async () => {
    const wrapper = mount(RecordForm, { props: { token: ref('tok') } })
    await wrapper.find('input').setValue('National ID 12345')
    await wrapper.find('form').trigger('submit')
    await new Promise(r => setTimeout(r, 0))
    expect(wrapper.find('input').element.value).toBe('')
  })

  it('shows error message when API call fails', async () => {
    const { useApi } = await import('../composables/useApi.js')
    useApi.mockReturnValueOnce({
      createItem: vi.fn().mockRejectedValue(new Error('POST /items failed: 500')),
    })
    const wrapper = mount(RecordForm, { props: { token: ref('tok') } })
    await wrapper.find('input').setValue('Test')
    await wrapper.find('form').trigger('submit')
    await new Promise(r => setTimeout(r, 0))
    expect(wrapper.text()).toContain('POST /items failed: 500')
  })
})
