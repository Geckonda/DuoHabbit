<!-- components/PushPromptBanner.vue -->
<!-- Ненавязчивое предложение включить push, показывается один раз при первом
     открытом чате (а не сразу при заходе в приложение и не каждый раз) -->
<script setup>
import { useNotificationsStore } from '../stores/notifications'

const notificationsStore = useNotificationsStore()

const handleEnable = async () => {
  await notificationsStore.enable()
  notificationsStore.markPrompted()
}

const handleDismiss = () => {
  notificationsStore.markPrompted()
}
</script>

<template>
  <div v-if="notificationsStore.shouldPrompt" class="push-prompt">
    <span class="push-prompt-icon">🔔</span>
    <div class="push-prompt-text">
      <div class="push-prompt-title">Включить уведомления?</div>
      <div class="push-prompt-subtitle">Узнаешь о новых сообщениях, даже когда приложение закрыто</div>
    </div>
    <div class="push-prompt-actions">
      <button class="push-prompt-later" @click="handleDismiss">Позже</button>
      <button class="push-prompt-enable" @click="handleEnable">Включить</button>
    </div>
  </div>
</template>

<style scoped>
.push-prompt {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  margin: var(--space-3);
  background: var(--surface-card);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}

.push-prompt-icon {
  font-size: 22px;
  flex-shrink: 0;
}

.push-prompt-text {
  flex: 1;
  min-width: 0;
}

.push-prompt-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.push-prompt-subtitle {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

.push-prompt-actions {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  flex-shrink: 0;
}

.push-prompt-later,
.push-prompt-enable {
  border: none;
  border-radius: var(--radius-pill);
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.push-prompt-later {
  background: transparent;
  color: var(--text-tertiary);
}

.push-prompt-enable {
  background: var(--color-accent);
  color: var(--text-on-accent);
}
</style>
