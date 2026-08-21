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

  // Подать заявку на вступление по инвайт-коду - членство только после одобрения владельцем
  join: (inviteCode) =>
    api.post('/groups/join', { invite_code: inviteCode }),

  // Мои входящие инвайты (owner пригласил, жду ответа)
  getMyInvites: () =>
    api.get('/groups/invites'),

  // Заявки на вступление в группы, которыми я владею
  getMyRequests: () =>
    api.get('/groups/requests'),

  acceptInvite: (groupId) =>
    api.post(`/groups/${groupId}/invites/accept`),

  declineInvite: (groupId) =>
    api.post(`/groups/${groupId}/invites/decline`),

  approveRequest: (groupId, userId) =>
    api.post(`/groups/${groupId}/requests/${userId}/approve`),

  rejectRequest: (groupId, userId) =>
    api.post(`/groups/${groupId}/requests/${userId}/reject`),

  // Список участников (с юзернеймами)
  getMembers: (groupId) =>
    api.get(`/groups/${groupId}/members`),

  // Пригласить юзера напрямую (только владелец) - членство только после его accept
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
