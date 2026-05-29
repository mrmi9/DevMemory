<script setup lang="ts">
import { ref } from 'vue'
import { ChevronDown, ChevronRight } from 'lucide-vue-next'

const props = withDefaults(defineProps<{
  title: string
  panelClass?: string
  defaultOpen?: boolean
}>(), {
  panelClass: '',
  defaultOpen: true
})

const expanded = ref(props.defaultOpen)

function toggleExpanded() {
  expanded.value = !expanded.value
}
</script>

<template>
  <section class="panel collapsible-panel" :class="[panelClass, { collapsed: !expanded }]">
    <header class="panel-header collapsible-panel-header">
      <button
        class="icon-button panel-toggle-button"
        type="button"
        :title="expanded ? '收起' : '展开'"
        :aria-expanded="expanded"
        data-testid="panel-toggle"
        @click="toggleExpanded"
      >
        <ChevronDown v-if="expanded" :size="17" />
        <ChevronRight v-else :size="17" />
      </button>
      <slot name="icon" />
      <h2>{{ title }}</h2>
      <div v-if="$slots.actions" class="panel-header-actions">
        <slot name="actions" />
      </div>
    </header>
    <div v-if="expanded" class="panel-content" data-testid="panel-content">
      <slot />
    </div>
  </section>
</template>
