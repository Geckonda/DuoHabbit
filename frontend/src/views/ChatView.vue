<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useChatStore } from '../stores/chat'
import { useUserStore } from '../stores/user'
import { useNotificationsStore } from '../stores/notifications'
import PushPromptBanner from '../components/PushPromptBanner.vue'

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()
const userStore = useUserStore()
const notificationsStore = useNotificationsStore()

const conversationId = computed(() => Number(route.params.id))
const messagesBox = ref(null)
const draft = ref('')
const isSending = ref(false)
const hasMoreHistory = ref(true)
const sendError = ref(null)

const messages = computed(
  () => chatStore.messagesByConversation[conversationId.value] || []
)

const conversation = computed(() =>
  chatStore.conversations.find((c) => c.id === conversationId.value)
)

const companionName = computed(
  () => conversation.value?.companion?.username || 'Диалог'
)

const isOwn = (message) => message.sender_id === userStore.user?.id

const formatTime = (isoString) =>
  new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

const scrollToBottom = async () => {
  await nextTick()
  if (messagesBox.value) {
    messagesBox.value.scrollTop = messagesBox.value.scrollHeight
  }
}

const loadHistory = async () => {
  try {
    const loaded = await chatStore.fetchMessages(conversationId.value)
    hasMoreHistory.value = loaded.length > 0
    await scrollToBottom()
    await chatStore.markRead(conversationId.value)
  } catch (err) {
    console.error('Ошибка загрузки сообщений:', err)
  }
}

const loadOlder = async () => {
  const box = messagesBox.value
  const prevHeight = box ? box.scrollHeight : 0

  const older = await chatStore.fetchOlderMessages(conversationId.value)
  hasMoreHistory.value = older.length > 0

  // Держим позицию чтения на месте после подстановки истории сверху
  await nextTick()
  if (box) {
    box.scrollTop = box.scrollHeight - prevHeight
  }
}

const handleSend = async () => {
  const text = draft.value.trim()
  if (!text || isSending.value) return

  isSending.value = true
  sendError.value = null

  try {
    await chatStore.sendMessage(conversationId.value, text)
    draft.value = ''
    await scrollToBottom()
  } catch (err) {
    sendError.value = err.response?.data?.detail || 'Не удалось отправить'
  } finally {
    isSending.value = false
  }
}

// Новое сообщение по сокету - доскроллим вниз
watch(
  () => messages.value.length,
  () => scrollToBottom()
)

onMounted(async () => {
  chatStore.setActiveConversation(conversationId.value)
  chatStore.connectSocket()
  notificationsStore.syncStatus()

  // Диалог мог быть открыт по прямой ссылке, тогда списка еще нет
  if (chatStore.conversations.length === 0) {
    await chatStore.fetchConversations().catch(() => {})
  }

  await loadHistory()
})

onUnmounted(() => {
  chatStore.setActiveConversation(null)
})
</script>

<template>
  <div class="chat">
    <div class="header">
      <button class="back" @click="router.push('/chats')">‹</button>
      <h1>{{ companionName }}</h1>
      <span
        class="status"
        :class="{ online: chatStore.socketStatus === 'connected' }"
      ></span>
    </div>

    <PushPromptBanner />

    <div ref="messagesBox" class="messages">
      <button
        v-if="hasMoreHistory && messages.length > 0"
        class="load-more"
        @click="loadOlder"
      >
        Загрузить ещё
      </button>

      <div v-if="messages.length === 0" class="empty">
        <p>Сообщений пока нет</p>
      </div>

      <div
        v-for="message in messages"
        :key="message.id"
        class="bubble-row"
        :class="{ own: isOwn(message) }"
      >
        <div class="bubble" :class="{ own: isOwn(message) }">
          <div class="text">{{ message.text }}</div>
          <div class="time">{{ formatTime(message.created_at) }}</div>
        </div>
      </div>
    </div>

    <div class="composer">
      <p v-if="sendError" class="send-error">{{ sendError }}</p>
      <form class="composer-row" @submit.prevent="handleSend">
        <input
          v-model="draft"
          type="text"
          placeholder="Сообщение"
          maxlength="4000"
          :disabled="isSending"
        />
        <button type="submit" :disabled="isSending || !draft.trim()">→</button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.chat {
  height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
}

.header {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
}

.header h1 {
  font-size: 20px;
  font-weight: 600;
  color: #000;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  flex-shrink: 0;
}

.status {
  width: 10px;
  height: 10px;
  border-radius: 5px;
  background: #C7C7CC;
  flex-shrink: 0;
}

.status.online {
  background: #34C759;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 600px;
  width: 100%;
  margin: 0 auto;
}

.load-more {
  align-self: center;
  padding: 6px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.8);
  border: none;
  color: #007AFF;
  font-size: 14px;
  cursor: pointer;
}

.empty {
  text-align: center;
  padding: 40px 0;
  color: #8E8E93;
}

.bubble-row {
  display: flex;
  justify-content: flex-start;
}

.bubble-row.own {
  justify-content: flex-end;
}

.bubble {
  max-width: 75%;
  background: #fff;
  border-radius: 16px;
  padding: 10px 14px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.bubble.own {
  background: #007AFF;
}

.text {
  font-size: 16px;
  color: #000;
  word-wrap: break-word;
  white-space: pre-wrap;
}

.bubble.own .text {
  color: #fff;
}

.time {
  font-size: 11px;
  color: #8E8E93;
  text-align: right;
  margin-top: 4px;
}

.bubble.own .time {
  color: rgba(255, 255, 255, 0.7);
}

.composer {
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  padding: 12px 16px;
}

.send-error {
  color: #FF3B30;
  font-size: 13px;
  margin-bottom: 8px;
  text-align: center;
}

.composer-row {
  display: flex;
  gap: 8px;
  max-width: 600px;
  margin: 0 auto;
}

.composer-row input {
  flex: 1;
  padding: 12px 16px;
  border-radius: 20px;
  border: none;
  background: #fff;
  font-size: 16px;
  outline: none;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.composer-row button {
  width: 44px;
  height: 44px;
  border-radius: 22px;
  background: #007AFF;
  border: none;
  color: #fff;
  font-size: 20px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,122,255,0.3);
}

.composer-row button:disabled {
  background: #C7C7CC;
  box-shadow: none;
  cursor: default;
}
</style>
