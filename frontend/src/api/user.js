// api/user.js
import api from './index'

export const users = {
  // Список пользователей с пагинацией
  getAll: (offset = 0, limit = 20) =>
    api.get('/users/', { params: { offset, limit } }),

  // Пользователь по ID
  getById: (userId) =>
    api.get(`/users/${userId}`),
  // Список пользователей (для поиска при добавлении в группу)
  getAll: (limit = 100) =>
    api.get('/users/', { params: { limit } })
}
