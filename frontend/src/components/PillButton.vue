<!-- components/PillButton.vue -->
<script setup>
defineProps({
  variant: { type: String, default: 'primary' }, // primary | secondary | danger | ghost
  loading: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  type: { type: String, default: 'button' }
})

defineEmits(['click'])
</script>

<template>
  <button
    :type="type"
    class="pill-btn"
    :class="variant"
    :disabled="disabled || loading"
    @click="$emit('click', $event)"
  >
    <span v-if="!loading"><slot></slot></span>
    <span v-else class="pill-loader"></span>
  </button>
</template>

<style scoped>
.pill-btn {
  width: 100%;
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: transform 0.15s ease, opacity 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
}

.pill-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.pill-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.pill-btn.primary {
  background: var(--color-accent);
  color: var(--text-on-accent);
  box-shadow: var(--shadow-md);
}

.pill-btn.secondary {
  background: rgba(0, 0, 0, 0.06);
  color: var(--text-primary);
}

.pill-btn.danger {
  background: var(--color-danger);
  color: var(--text-on-accent);
}

.pill-btn.ghost {
  background: var(--surface-card);
  color: var(--color-ios-blue);
  box-shadow: var(--shadow-sm);
}

.pill-loader {
  display: inline-block;
  width: 22px;
  height: 22px;
  border: 3px solid rgba(255, 255, 255, 0.4);
  border-radius: 50%;
  border-top-color: white;
  animation: pill-spin 0.8s linear infinite;
}

.pill-btn.secondary .pill-loader,
.pill-btn.ghost .pill-loader {
  border-color: rgba(0, 0, 0, 0.15);
  border-top-color: var(--text-primary);
}

@keyframes pill-spin {
  to { transform: rotate(360deg); }
}
</style>
