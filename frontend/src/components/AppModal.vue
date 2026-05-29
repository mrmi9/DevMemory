<script setup lang="ts">
withDefaults(
  defineProps<{
    open: boolean
    title: string
    confirmLabel?: string
    cancelLabel?: string
    busy?: boolean
    danger?: boolean
    error?: string
  }>(),
  {
    confirmLabel: '确认',
    cancelLabel: '取消',
    busy: false,
    danger: false,
    error: ''
  }
)

const emit = defineEmits<{
  close: []
  confirm: []
}>()
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="modal-backdrop" @click.self="!busy && emit('close')">
      <section class="modal-dialog" role="dialog" aria-modal="true">
        <header class="modal-header">
          <h3>{{ title }}</h3>
        </header>
        <div class="modal-body">
          <slot />
        </div>
        <p v-if="error" class="inline-error">{{ error }}</p>
        <footer class="modal-actions">
          <button
            class="secondary-button"
            type="button"
            data-testid="modal-cancel"
            :disabled="busy"
            @click="emit('close')"
          >
            {{ cancelLabel }}
          </button>
          <button
            :class="danger ? 'danger-button' : ''"
            type="button"
            data-testid="modal-confirm"
            :disabled="busy"
            @click="emit('confirm')"
          >
            {{ busy ? '处理中' : confirmLabel }}
          </button>
        </footer>
      </section>
    </div>
  </Teleport>
</template>
