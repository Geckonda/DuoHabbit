// api/chat.js
import api from './index'

export const chat = {
  // Список диалогов: собеседник, последнее сообщение, непрочитанные
  getConversations: (offset = 0, limit = 20) =>
    api.get('/chat/conversations', { params: { offset, limit } }),

  // Открыть диалог с пользователем (или получить существующий)
  openConversation: (userId) =>
    api.post('/chat/conversations', { user_id: userId }),

  // История: beforeId - курсор, отдаются сообщения старше него
  getMessages: (conversationId, beforeId = null, limit = 50) =>
    api.get(`/chat/conversations/${conversationId}/messages`, {
      params: beforeId ? { before_id: beforeId, limit } : { limit },
    }),

  // Отправить сообщение
  sendMessage: (conversationId, text) =>
    api.post(`/chat/conversations/${conversationId}/messages`, { text }),

  // Пометить прочитанным до сообщения
  markRead: (conversationId, messageId) =>
    api.post(`/chat/conversations/${conversationId}/read`, { message_id: messageId }),
}
