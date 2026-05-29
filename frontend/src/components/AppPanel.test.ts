import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import AppPanel from './AppPanel.vue'

describe('AppPanel', () => {
  it('collapses and expands panel content from the header toggle', async () => {
    const wrapper = mount(AppPanel, {
      props: {
        title: '学习材料'
      },
      slots: {
        default: '<p>panel body</p>'
      }
    })

    expect(wrapper.text()).toContain('panel body')
    expect(wrapper.find('[data-testid="panel-toggle"]').attributes('aria-expanded')).toBe('true')

    await wrapper.find('[data-testid="panel-toggle"]').trigger('click')

    expect(wrapper.text()).not.toContain('panel body')
    expect(wrapper.find('[data-testid="panel-toggle"]').attributes('aria-expanded')).toBe('false')

    await wrapper.find('[data-testid="panel-toggle"]').trigger('click')

    expect(wrapper.text()).toContain('panel body')
    expect(wrapper.find('[data-testid="panel-toggle"]').attributes('aria-expanded')).toBe('true')
  })
})
