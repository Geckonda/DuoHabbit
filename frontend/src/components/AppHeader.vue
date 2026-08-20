<!-- components/AppHeader.vue -->
<script setup>
import { useSafeBack } from '../composables/useSafeBack'

const props = defineProps({
  title: { type: String, default: '' },
  showBack: { type: Boolean, default: true },
  fallback: { type: String, default: '/' }
})

const goBack = useSafeBack()
const handleBack = () => goBack(props.fallback)
</script>

<template>
  <header class="app-header">
    <button v-if="showBack" class="back-btn" @click="handleBack" title="Назад">
      <span class="back-icon">‹</span>
    </button>
    <div v-else class="spacer"></div>

    <h1 class="header-title">{{ title }}</h1>

    <div class="header-right">
      <slot name="right"></slot>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  background: var(--surface-header);
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
  padding: var(--space-3) var(--space-4);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  position: sticky;
  top: 0;
  z-index: var(--z-header);
  border-bottom: 1px solid var(--border-subtle);
}

.header-title {
  flex: 1;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.back-btn,
.spacer {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
}

.back-btn {
  border-radius: var(--radius-pill);
  background: var(--surface-card);
  border: none;
  color: var(--color-ios-blue);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-sm);
}

.back-btn:active {
  transform: scale(0.92);
}

.back-icon {
  font-size: 24px;
  font-weight: 600;
  line-height: 1;
  margin-left: -2px;
}

.header-right {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 36px;
  justify-content: flex-end;
}
</style>
