<!-- components/BottomTabBar.vue -->
<script setup>
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useChatStore } from '../stores/chat'

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()

const tabs = [
  { path: '/', label: 'Привычки', icon: '📅' },
  { path: '/groups', label: 'Группы', icon: '👥' },
  { path: '/chats', label: 'Чат', icon: '💬' },
  { path: '/profile', label: 'Профиль', icon: '🙋' }
]

const isActive = (path) => route.path === path

const go = (path) => {
  if (!isActive(path)) router.push(path)
}

// Таб-бар смонтирован — значит юзер уже авторизован (см. meta.tabBar в роутере).
// Подключаемся сразу, чтобы бейдж непрочитанных был виден с любой вкладки,
// а не только после захода в сам чат.
onMounted(() => {
  chatStore.fetchConversations().catch(() => {})
  chatStore.connectSocket()
})
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
      <span class="tab-icon-wrap">
        <span class="tab-icon">{{ tab.icon }}</span>
        <span v-if="tab.path === '/chats' && chatStore.unreadTotal > 0" class="tab-badge">
          {{ chatStore.unreadTotal > 9 ? '9+' : chatStore.unreadTotal }}
        </span>
      </span>
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

.tab-icon-wrap {
  position: relative;
  display: inline-flex;
}

.tab-icon {
  font-size: 22px;
  line-height: 1;
}

.tab-badge {
  position: absolute;
  top: -4px;
  right: -8px;
  min-width: 15px;
  height: 15px;
  padding: 0 3px;
  border-radius: var(--radius-pill);
  background: var(--color-danger);
  color: var(--text-on-accent);
  font-size: 10px;
  font-weight: 700;
  line-height: 15px;
  text-align: center;
}

.tab-label {
  font-size: 11px;
  font-weight: 500;
}
</style>
