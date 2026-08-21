// api/habits.js
import api from './index'

export const habits = {
  // Получить все личные привычки (групповые — через api/group.js)
  getAll: (onlyActive = true) =>
    api.get('/habits', { params: { only_active: onlyActive } }),

  // Получить привычку по ID (личную или групповую — участнику доступны обе)
  getById: (habitId) =>
    api.get(`/habits/${habitId}`),

  // Получить привычку с последними отметками
  getWithChecks: (habitId) =>
    api.get(`/habits/${habitId}/details`),

  // Создать личную привычку (для групповой — groups.addHabit)
  create: (data) =>
    api.post('/habits', data),

  // Обновить (название/описание/приватность/allowed_misses) — владелец привычки
  update: (habitId, data) =>
    api.patch(`/habits/${habitId}`, data),

  // Архивировать
  archive: (habitId) =>
    api.post(`/habits/${habitId}/archive`),

  // Восстановить
  restore: (habitId) =>
    api.post(`/habits/${habitId}/restore`),

  // Удалить навсегда
  delete: (habitId) =>
    api.delete(`/habits/${habitId}`),

  // Отметить выполнение за сегодня (по своей таймзоне, бэкфилл не поддержан)
  check: (habitId) =>
    api.post(`/habits/${habitId}/check`),

  // Последние отметки
  getChecks: (habitId, limit = 30) =>
    api.get(`/habits/${habitId}/checks`, { params: { limit } }),

  // Кто из участников уже отметился в своём текущем периоде
  getCheckinStatus: (habitId) =>
    api.get(`/habits/${habitId}/checks/status`)
}
