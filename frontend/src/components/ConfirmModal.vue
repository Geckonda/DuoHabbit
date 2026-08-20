<!-- components/ConfirmModal.vue -->
<script setup>
const props = defineProps({
  modelValue: { type: Boolean, default: false },
  icon: { type: String, default: '⚠️' },
  title: { type: String, required: true },
  text: { type: String, default: '' },
  confirmLabel: { type: String, default: 'Подтвердить' },
  cancelLabel: { type: String, default: 'Отмена' },
  danger: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue', 'confirm'])

const close = () => emit('update:modelValue', false)
const confirm = () => emit('confirm')
</script>

<template>
  <div v-if="modelValue" class="modal-overlay" @click="close">
    <div class="modal-content" @click.stop>
      <div class="modal-icon">{{ icon }}</div>
      <h3 class="modal-title">{{ title }}</h3>
      <p v-if="text" class="modal-text">{{ text }}</p>
      <div class="modal-actions">
        <button class="modal-cancel" @click="close">{{ cancelLabel }}</button>
        <button class="modal-confirm" :class="{ danger }" @click="confirm">{{ confirmLabel }}</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-4);
  z-index: var(--z-modal);
}

.modal-content {
  background: var(--surface-overlay);
  border-radius: var(--radius-xl);
  padding: var(--space-8);
  max-width: 400px;
  width: 100%;
  text-align: center;
  animation: modalSlideUp 0.25s ease;
}

.modal-icon {
  font-size: 48px;
  margin-bottom: var(--space-4);
}

.modal-title {
  font-size: 22px;
  font-weight: 600;
  margin-bottom: var(--space-3);
  color: var(--text-primary);
}

.modal-text {
  color: var(--text-secondary);
  margin-bottom: var(--space-6);
  line-height: 1.5;
  font-size: 15px;
}

.modal-actions {
  display: flex;
  gap: var(--space-3);
}

.modal-cancel,
.modal-confirm {
  flex: 1;
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  border: none;
}

.modal-cancel {
  background: rgba(0, 0, 0, 0.06);
  color: var(--text-secondary);
}

.modal-confirm {
  background: var(--color-accent);
  color: var(--text-on-accent);
}

.modal-confirm.danger {
  background: var(--color-danger);
}

@keyframes modalSlideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
