<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '../stores/chat'
import { useUserStore } from '../stores/user'
import { users } from '../api/user'

const router = useRouter()
const chatStore = useChatStore()
const userStore = useUserStore()

const isPickerOpen = ref(false)
const userList = ref([])
const isPickerLoading = ref(false)
const pickerError = ref(null)

const conversations = computed(() => chatStore.conversations)

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
    <div class="header">
      <button class="back" @click="router.push('/')">‹</button>
      <h1>Чаты</h1>
      <button class="add" @click="openPicker">+</button>
    </div>

    <div class="content">
      <div v-if="chatStore.isLoading && conversations.length === 0" class="loading">
        Загрузка...
      </div>

      <div v-else-if="chatStore.error" class="error">
        <p>{{ chatStore.error }}</p>
        <button @click="loadConversations">Повторить</button>
      </div>

      <div v-else-if="conversations.length === 0" class="empty">
        <p>Пока нет диалогов</p>
        <button @click="openPicker">Написать кому-нибудь</button>
      </div>

      <div v-else class="list">
        <div
          v-for="conversation in conversations"
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
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
}

.header {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #000;
}

.back {
  width: 40px;
  height: 40px;
  border-radius: 20px;
  background: #fff;
  border: none;
  font-size: 24px;
  color: #007AFF;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.add {
  width: 40px;
  height: 40px;
  border-radius: 20px;
  background: #fff;
  border: none;
  font-size: 24px;
  color: #007AFF;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.content {
  max-width: 600px;
  margin: 0 auto;
  padding: 16px;
}

.loading {
  text-align: center;
  padding: 40px 0;
  color: #8E8E93;
}

.error {
  text-align: center;
  padding: 40px 0;
  color: #FF3B30;
}

.error button {
  margin-top: 16px;
  padding: 8px 20px;
  border-radius: 20px;
  background: #fff;
  border: none;
  color: #007AFF;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.empty {
  text-align: center;
  padding: 60px 0;
}

.empty p {
  color: #8E8E93;
  margin-bottom: 20px;
}

.empty button {
  padding: 12px 24px;
  border-radius: 24px;
  background: #007AFF;
  border: none;
  color: #fff;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,122,255,0.3);
}

.list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.item {
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.item-body {
  min-width: 0;
}

.title {
  font-size: 17px;
  font-weight: 500;
  color: #000;
  margin-bottom: 4px;
}

.description {
  font-size: 14px;
  color: #8E8E93;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.badge {
  flex-shrink: 0;
  min-width: 22px;
  height: 22px;
  padding: 0 7px;
  border-radius: 11px;
  background: #FF3B30;
  color: #fff;
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
  z-index: 10;
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
