// api/habits.js
import api from './index'

export const habits = {
  // Получить все привычки
  getAll: (onlyActive = true) => 
    api.get('/habits', { params: { only_active: onlyActive } }),
  
  // Получить привычку по ID
  getById: (habitId) => 
    api.get(`/habits/${habitId}`),
  
  // Получить привычку с чеками
  getWithChecks: (habitId) => 
    api.get(`/habits/${habitId}/details`),
  
  // Создать привычку
  create: (data) => 
    api.post('/habits', data),
  
  // Обновить привычку
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
  
  // Отметить выполнение
  check: (habitId, data) => 
    api.post(`/habits/${habitId}/check`, data),
  
  // Получить статистику
  getStats: (habitId, days = 30) => 
    api.get(`/habits/${habitId}/stats`, { params: { days } }),
  
  // Удалить отметку
  deleteCheck: (habitId, checkId) => 
    api.delete(`/habits/${habitId}/checks/${checkId}`)
}