// api/group.js
import api from './index'

export const groups = {
  // Получить мои группы (каждая уже с habits[] и member_count)
  getAll: (onlyActive = true) =>
    api.get('/groups', { params: { only_active: onlyActive } }),

  // Получить группу по ID (с привычками и числом участников)
  getById: (groupId) =>
    api.get(`/groups/${groupId}`),

  // Создать группу (только имя — привычки добавляются отдельно)
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

  // Вступить по инвайт-коду (сразу подключает ко всем текущим привычкам группы)
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

  // Список привычек группы
  getHabits: (groupId) =>
    api.get(`/groups/${groupId}/habits`),

  // Добавить новую общую привычку (только владелец) — подключает всех текущих участников
  addHabit: (groupId, data) =>
    api.post(`/groups/${groupId}/habits`, data)
}
