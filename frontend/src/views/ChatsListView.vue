<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '../stores/chat'
import { useUserStore } from '../stores/user'
import { users } from '../api/user'
import AppHeader from '../components/AppHeader.vue'

const router = useRouter()
const chatStore = useChatStore()
const userStore = useUserStore()

const isPickerOpen = ref(false)
const userList = ref([])
const isPickerLoading = ref(false)
const pickerError = ref(null)

const activeConversations = computed(() => chatStore.activeConversations)
const pendingRequests = computed(() => chatStore.pendingRequests)

// Себе писать нельзя, бэкенд такой диалог не откроет
const availableUsers = computed(() =>
  userList.value.filter((u) => u.id !== userStore.user?.id)
)

const loadConversations = async () => {
  try {
    await chatStore.fetchConversations()
  } catch (err) {
    console.error('Ошибка загрузки диалогов:', err)
  }
}

const openPicker = async () => {
  isPickerOpen.value = true
  isPickerLoading.value = true
  pickerError.value = null

  try {
    const response = await users.getAll(0, 50)
    userList.value = response.data
  } catch (err) {
    pickerError.value = err.response?.data?.detail || 'Не удалось загрузить пользователей'
  } finally {
    isPickerLoading.value = false
  }
}

const startConversation = async (userId) => {
  try {
    const conversation = await chatStore.openConversation(userId)
    isPickerOpen.value = false
    router.push(`/chats/${conversation.id}`)
  } catch (err) {
    pickerError.value = err.response?.data?.detail || 'Не удалось открыть диалог'
  }
}

const preview = (conversation) => {
  if (conversation.status === 'pending') return 'Ожидает ответа'
  if (!conversation.last_message) return 'Нет сообщений'
  const text = conversation.last_message.text
  return text.length > 60 ? `${text.slice(0, 60)}…` : text
}

onMounted(() => {
  loadConversations()
  chatStore.connectSocket()
})
</script>

<template>
  <div class="chats">
    <AppHeader title="Чаты" :show-back="false">
      <template #right>
        <button class="add" @click="openPicker">+</button>
      </template>
    </AppHeader>

    <div class="content">
      <div
        v-if="chatStore.isLoading && activeConversations.length === 0 && pendingRequests.length === 0"
        class="loading"
      >
        Загрузка...
      </div>

      <div v-else-if="chatStore.error" class="error">
        <p>{{ chatStore.error }}</p>
        <button @click="loadConversations">Повторить</button>
      </div>

      <template v-else>
        <div v-if="pendingRequests.length > 0" class="section">
          <div class="section-title">Запросы</div>
          <div class="list">
            <div
              v-for="conversation in pendingRequests"
              :key="conversation.id"
              class="item"
              @click="router.push(`/chats/${conversation.id}`)"
            >
              <div class="item-body">
                <div class="title">{{ conversation.companion.username }}</div>
                <div class="description">Хочет тебе написать</div>
              </div>
              <span class="badge">1</span>
            </div>
          </div>
        </div>

        <div v-if="activeConversations.length === 0 && pendingRequests.length === 0" class="empty">
          <p>Пока нет диалогов</p>
          <button @click="openPicker">Написать кому-нибудь</button>
        </div>

        <div v-else-if="activeConversations.length > 0" class="list">
          <div
            v-for="conversation in activeConversations"
            :key="conversation.id"
            class="item"
            @click="router.push(`/chats/${conversation.id}`)"
          >
            <div class="item-body">
              <div class="title">{{ conversation.companion.username }}</div>
              <div class="description">{{ preview(conversation) }}</div>
            </div>
            <span v-if="conversation.unread_count > 0" class="badge">
              {{ conversation.unread_count }}
            </span>
          </div>
        </div>
      </template>
    </div>

    <!-- Выбор собеседника -->
    <div v-if="isPickerOpen" class="picker-backdrop" @click.self="isPickerOpen = false">
      <div class="picker">
        <div class="picker-header">
          <h2>Кому написать</h2>
          <button class="close" @click="isPickerOpen = false">✕</button>
        </div>

        <div v-if="isPickerLoading" class="loading">Загрузка...</div>
        <div v-else-if="pickerError" class="error"><p>{{ pickerError }}</p></div>
        <div v-else-if="availableUsers.length === 0" class="empty">
          <p>Других пользователей пока нет</p>
        </div>

        <div v-else class="picker-list">
          <button
            v-for="user in availableUsers"
            :key="user.id"
            class="picker-item"
            @click="startConversation(user.id)"
          >
            {{ user.username }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chats {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.add {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-pill);
  background: var(--surface-card);
  border: none;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  font-size: 22px;
  color: var(--color-ios-blue);
}

.content {
  flex: 1;
  overflow-y: auto;
  max-width: 600px;
  width: 100%;
  margin: 0 auto;
  padding: var(--space-4);
  padding-bottom: calc(var(--tab-bar-height) + env(safe-area-inset-bottom) + var(--space-4));
}

.loading {
  text-align: center;
  padding: 40px 0;
  color: var(--text-tertiary);
}

.error {
  text-align: center;
  padding: 40px 0;
  color: var(--color-danger);
}

.error button {
  margin-top: var(--space-4);
  padding: var(--space-2) var(--space-5);
  border-radius: var(--radius-pill);
  background: var(--surface-card);
  border: none;
  color: var(--color-ios-blue);
  cursor: pointer;
  box-shadow: var(--shadow-sm);
}

.empty {
  text-align: center;
  padding: 60px 0;
}

.empty p {
  color: var(--text-tertiary);
  margin-bottom: var(--space-5);
}

.empty button {
  padding: var(--space-3) var(--space-6);
  border-radius: var(--radius-pill);
  background: var(--color-ios-blue);
  border: none;
  color: #fff;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: var(--shadow-md);
}

.section {
  margin-bottom: var(--space-5);
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.02em;
  margin-bottom: var(--space-2);
  padding: 0 var(--space-1);
}

.list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.item {
  background: var(--surface-card);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
}

.item-body {
  min-width: 0;
}

.title {
  font-size: 17px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.description {
  font-size: 14px;
  color: var(--text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.badge {
  flex-shrink: 0;
  min-width: 22px;
  height: 22px;
  padding: 0 7px;
  border-radius: var(--radius-pill);
  background: var(--color-danger);
  color: var(--text-on-accent);
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.picker-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: var(--z-modal);
}

.picker {
  background: #fff;
  width: 100%;
  max-width: 600px;
  border-radius: 20px 20px 0 0;
  padding: 16px;
  max-height: 70vh;
  overflow-y: auto;
}

.picker-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.picker-header h2 {
  font-size: 18px;
  font-weight: 600;
}

.close {
  background: none;
  border: none;
  font-size: 18px;
  color: #8E8E93;
  cursor: pointer;
}

.picker-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.picker-item {
  text-align: left;
  padding: 14px 16px;
  border: none;
  border-radius: 12px;
  background: #F2F2F7;
  font-size: 16px;
  color: #000;
  cursor: pointer;
}
</style>
