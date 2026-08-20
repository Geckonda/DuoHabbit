// stores/chat.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { chat } from '../api/chat'
import { createChatSocket } from '../api/ws'

export const useChatStore = defineStore('chat', () => {
  // Состояние
  const conversations = ref([])
  const messagesByConversation = ref({}) // { [conversationId]: Message[] }
  const activeConversationId = ref(null)
  const socketStatus = ref('closed')
  const isLoading = ref(false)
  const error = ref(null)

  let socket = null

  // Геттеры
  const unreadTotal = computed(() =>
    conversations.value.reduce((sum, c) => sum + (c.unread_count || 0), 0)
  )

  const activeMessages = computed(() =>
    activeConversationId.value
      ? messagesByConversation.value[activeConversationId.value] || []
      : []
  )

  const findConversation = (conversationId) =>
    conversations.value.find((c) => c.id === conversationId)

  // ===== Загрузка =====

  const fetchConversations = async () => {
    isLoading.value = true
    error.value = null

    try {
      const response = await chat.getConversations()
      conversations.value = response.data
      return conversations.value
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка загрузки диалогов'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const fetchMessages = async (conversationId) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await chat.getMessages(conversationId)
      messagesByConversation.value[conversationId] = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка загрузки сообщений'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Подгрузка истории вверх по курсору
  const fetchOlderMessages = async (conversationId) => {
    const loaded = messagesByConversation.value[conversationId] || []
    if (loaded.length === 0) return []

    const oldest = loaded[0]
    const response = await chat.getMessages(conversationId, oldest.id)

    if (response.data.length > 0) {
      messagesByConversation.value[conversationId] = [...response.data, ...loaded]
    }

    return response.data
  }

  const openConversation = async (userId) => {
    const response = await chat.openConversation(userId)
    const conversation = response.data

    if (!findConversation(conversation.id)) {
      conversations.value = [conversation, ...conversations.value]
    }

    return conversation
  }

  // ===== Отправка и прочтение =====

  const sendMessage = async (conversationId, text) => {
    const response = await chat.sendMessage(conversationId, text)
    // Сообщение вернется и по сокету, addMessage защищен от дублей
    addMessage(response.data)
    return response.data
  }

  const markRead = async (conversationId) => {
    const messages = messagesByConversation.value[conversationId] || []
    if (messages.length === 0) return

    const lastId = messages[messages.length - 1].id
    await chat.markRead(conversationId, lastId)

    const conversation = findConversation(conversationId)
    if (conversation) conversation.unread_count = 0
  }

  // ===== Входящие события =====

  const addMessage = (message) => {
    const list = messagesByConversation.value[message.conversation_id]

    if (list) {
      // Свое же сообщение уже могло прийти ответом на POST
      if (list.some((m) => m.id === message.id)) return
      list.push(message)
    }

    const conversation = findConversation(message.conversation_id)
    if (conversation) {
      conversation.last_message = message
      // Диалог с новым сообщением поднимается наверх
      conversations.value = [
        conversation,
        ...conversations.value.filter((c) => c.id !== conversation.id),
      ]
    }
  }

  const handleEvent = (payload) => {
    if (payload.type === 'message') {
      const message = payload.message
      addMessage(message)

      const conversation = findConversation(message.conversation_id)
      const isOpen = activeConversationId.value === message.conversation_id

      if (conversation && !isOpen) {
        conversation.unread_count = (conversation.unread_count || 0) + 1
      }

      // Диалога еще нет в списке - его только что завели с той стороны
      if (!conversation) {
        fetchConversations().catch(() => {})
      }

      if (isOpen) {
        markRead(message.conversation_id).catch(() => {})
      }
    }
  }

  // ===== Сокет =====

  const connectSocket = () => {
    if (socket) return

    socket = createChatSocket({
      onEvent: handleEvent,
      onStatusChange: (status) => {
        socketStatus.value = status
      },
    })
    socket.connect()
  }

  const disconnectSocket = () => {
    if (!socket) return
    socket.close()
    socket = null
  }

  const setActiveConversation = (conversationId) => {
    activeConversationId.value = conversationId
  }

  // Очистка стора (например при логауте), как в сторе привычек
  const $reset = () => {
    disconnectSocket()
    conversations.value = []
    messagesByConversation.value = {}
    activeConversationId.value = null
    error.value = null
  }

  return {
    conversations,
    messagesByConversation,
    activeConversationId,
    socketStatus,
    isLoading,
    error,
    unreadTotal,
    activeMessages,
    fetchConversations,
    fetchMessages,
    fetchOlderMessages,
    openConversation,
    sendMessage,
    markRead,
    connectSocket,
    disconnectSocket,
    setActiveConversation,
    $reset,
  }
})
