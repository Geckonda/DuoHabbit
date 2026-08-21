<!-- components/ActionMenu.vue -->
<script setup>
import { watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false }
})
const emit = defineEmits(['update:modelValue'])

const close = () => emit('update:modelValue', false)

const handleKeydown = (e) => {
  if (e.key === 'Escape') close()
}

watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) {
      window.addEventListener('keydown', handleKeydown)
    } else {
      window.removeEventListener('keydown', handleKeydown)
    }
  }
)
</script>

<template>
  <div v-if="modelValue" class="action-menu-backdrop" @click="close"></div>
  <div v-if="modelValue" class="action-menu-dropdown" @click="close">
    <slot></slot>
  </div>
</template>

<style scoped>
.action-menu-backdrop {
  position: fixed;
  inset: 0;
  z-index: var(--z-dropdown);
  background: transparent;
}

.action-menu-dropdown {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  z-index: calc(var(--z-dropdown) + 1);
  background: var(--surface-overlay);
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
  border-radius: var(--radius-md);
  padding: var(--space-2);
  min-width: 220px;
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--border-subtle);
}

.action-menu-dropdown :deep(.menu-item) {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 15px;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  cursor: pointer;
  text-align: left;
}

.action-menu-dropdown :deep(.menu-item:active) {
  background: rgba(0, 0, 0, 0.05);
}

.action-menu-dropdown :deep(.menu-item.delete) {
  color: var(--color-danger);
}

.action-menu-dropdown :deep(.menu-icon) {
  font-size: 18px;
}
</style>
