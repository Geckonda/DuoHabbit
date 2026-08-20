// api/group.js
import api from './index'

export const groups = {
  // Получить мои группы
  getAll: (onlyActive = true) =>
    api.get('/groups', { params: { only_active: onlyActive } }),

  // Получить группу по ID (с привычкой и числом участников)
  getById: (groupId) =>
    api.get(`/groups/${groupId}`),

  // Создать группу вместе с общей привычкой
  create: (data) =>
    api.post('/groups', data),

  // Переименовать группу
  update: (groupId, data) =>
    api.patch(`/groups/${groupId}`, data),

  // Расформировать группу
  delete: (groupId) =>
    api.delete(`/groups/${groupId}`),

  // Перегенерировать инвайт-код
  regenerateInvite: (groupId) =>
    api.post(`/groups/${groupId}/invite/regenerate`),

  // Вступить по инвайт-коду
  join: (inviteCode) =>
    api.post('/groups/join', { invite_code: inviteCode }),

  // Список участников (с юзернеймами)
  getMembers: (groupId) =>
    api.get(`/groups/${groupId}/members`),

  // Добавить участника напрямую (только владелец)
  addMember: (groupId, userId) =>
    api.post(`/groups/${groupId}/members`, { user_id: userId }),

  // Удалить участника (только владелец)
  removeMember: (groupId, userId) =>
    api.delete(`/groups/${groupId}/members/${userId}`),

  // Выйти из группы (не владелец)
  leave: (groupId) =>
    api.post(`/groups/${groupId}/leave`),

  // Изменить название/описание/allowed_misses общей привычки
  updateHabit: (groupId, data) =>
    api.patch(`/groups/${groupId}/habit`, data),

  // Отметить выполнение за текущий период
  checkIn: (groupId) =>
    api.post(`/groups/${groupId}/check`),

  // Кто уже отметился за текущий период
  getCheckinStatus: (groupId) =>
    api.get(`/groups/${groupId}/checks/status`),

  // Мои последние чеки
  getMyChecks: (groupId, limit = 30) =>
    api.get(`/groups/${groupId}/checks/mine`, { params: { limit } })
}
