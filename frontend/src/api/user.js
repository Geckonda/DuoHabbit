// api/user.js
import api from './index'

export const users = {
  // Список пользователей с пагинацией (используется чатом и поиском при добавлении в группу)
  getAll: (offset = 0, limit = 100) =>
    api.get('/users/', { params: { offset, limit } }),

  // Пользователь по ID
  getById: (userId) =>
    api.get(`/users/${userId}`),

  // Обновить свой профиль (только username/timezone — сознательно узкий эндпоинт)
  updateMe: (data) =>
    api.patch('/users/me', data)
}
