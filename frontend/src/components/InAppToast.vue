<!-- components/InAppToast.vue -->
<!-- Внутриприложенческое уведомление: приложение открыто, но не на этом экране -->
<script setup>
import { useRouter } from 'vue-router'
import { useToastStore } from '../stores/toast'

const router = useRouter()
const toastStore = useToastStore()

const handleClick = () => {
  const url = toastStore.current?.url
  toastStore.dismiss()
  if (url) router.push(url)
}
</script>

<template>
  <Transition name="toast-slide">
    <div v-if="toastStore.current" class="toast" @click="handleClick">
      <div class="toast-icon">💬</div>
      <div class="toast-body">
        <div class="toast-title">{{ toastStore.current.title }}</div>
        <div class="toast-text">{{ toastStore.current.body }}</div>
      </div>
      <button class="toast-close" @click.stop="toastStore.dismiss">✕</button>
    </div>
  </Transition>
</template>

<style scoped>
.toast {
  position: fixed;
  top: calc(env(safe-area-inset-top) + var(--space-3));
  left: var(--space-4);
  right: var(--space-4);
  z-index: var(--z-toast);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--surface-overlay);
  backdrop-filter: var(--blur);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  cursor: pointer;
  max-width: 480px;
  margin: 0 auto;
}

.toast-icon {
  font-size: 22px;
  flex-shrink: 0;
}

.toast-body {
  flex: 1;
  min-width: 0;
}

.toast-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.toast-text {
  font-size: 13px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-top: 2px;
}

.toast-close {
  flex-shrink: 0;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  font-size: 14px;
  padding: var(--space-2);
  cursor: pointer;
}

.toast-slide-enter-active,
.toast-slide-leave-active {
  transition: transform 0.25s ease, opacity 0.25s ease;
}

.toast-slide-enter-from,
.toast-slide-leave-to {
  transform: translateY(-16px);
  opacity: 0;
}
</style>
