<!-- components/BottomTabBar.vue -->
<script setup>
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const tabs = [
  { path: '/', label: 'Привычки', icon: '📅' },
  { path: '/groups', label: 'Группы', icon: '👥' },
  { path: '/profile', label: 'Профиль', icon: '🙋' }
]

const isActive = (path) => route.path === path

const go = (path) => {
  if (!isActive(path)) router.push(path)
}
</script>

<template>
  <nav class="tab-bar">
    <button
      v-for="tab in tabs"
      :key="tab.path"
      class="tab"
      :class="{ active: isActive(tab.path) }"
      @click="go(tab.path)"
    >
      <span class="tab-icon">{{ tab.icon }}</span>
      <span class="tab-label">{{ tab.label }}</span>
    </button>
  </nav>
</template>

<style scoped>
.tab-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  height: calc(var(--tab-bar-height) + env(safe-area-inset-bottom));
  padding-bottom: env(safe-area-inset-bottom);
  background: var(--surface-header);
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
  border-top: 1px solid var(--border-subtle);
  display: flex;
  z-index: var(--z-tabbar);
}

.tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-tertiary);
}

.tab.active {
  color: var(--color-ios-blue);
}

.tab-icon {
  font-size: 22px;
  line-height: 1;
}

.tab-label {
  font-size: 11px;
  font-weight: 500;
}
</style>
