// stores/habits.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { habits } from '../api/habit'

export const useHabitsStore = defineStore('habits', () => {
  // Состояние
  const habitsList = ref([])
  const currentHabit = ref(null)
  const isLoading = ref(false)
  const error = ref(null)
  const lastFetched = ref(null) // для кеширования

  // Геттеры (computed свойства)
  const activeHabits = computed(() => 
    habitsList.value.filter(h => h.is_active)
  )
  
  const archivedHabits = computed(() => 
    habitsList.value.filter(h => !h.is_active)
  )

  // Загрузка всех привычек пользователя
  const fetchHabits = async (onlyActive = true, force = false) => {
    // Кеширование на 5 минут
    const CACHE_TIME = 5 * 60 * 1000 // 5 минут
    const now = Date.now()
    
    if (!force && 
        lastFetched.value && 
        (now - lastFetched.value) < CACHE_TIME &&
        habitsList.value.length > 0) {
      console.log('🔄 Использую кешированные привычки')
      return habitsList.value
    }

    isLoading.value = true
    error.value = null
    
    try {
      const response = await habits.getAll(onlyActive)
      habitsList.value = response.data
      lastFetched.value = now
      return habitsList.value
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка загрузки привычек'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Получение конкретной привычки
  const fetchHabitById = async (habitId, withChecks = false) => {
    isLoading.value = true
    error.value = null
    
    try {
      const endpoint = withChecks ? 'getWithChecks' : 'getById'
      const response = await habits[endpoint](habitId)
      
      // Обновляем в списке если есть
      const index = habitsList.value.findIndex(h => h.id === habitId)
      if (index !== -1) {
        habitsList.value[index] = response.data
      }
      
      currentHabit.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка загрузки привычки'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Создание привычки
  const createHabit = async (habitData) => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await habits.create(habitData)
      habitsList.value.push(response.data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка создания привычки'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Обновление привычки
  const updateHabit = async (habitId, updateData) => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await habits.update(habitId, updateData)
      
      // Обновляем в списке
      const index = habitsList.value.findIndex(h => h.id === habitId)
      if (index !== -1) {
        habitsList.value[index] = response.data
      }
      
      // Обновляем текущую если это она
      if (currentHabit.value?.id === habitId) {
        currentHabit.value = response.data
      }
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка обновления привычки'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Архивация привычки (soft delete)
  const archiveHabit = async (habitId) => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await habits.archive(habitId)
      
      // Обновляем статус в списке
      const index = habitsList.value.findIndex(h => h.id === habitId)
      if (index !== -1) {
        habitsList.value[index] = response.data
      }
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка архивации'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Восстановление из архива
  const restoreHabit = async (habitId) => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await habits.restore(habitId)
      
      const index = habitsList.value.findIndex(h => h.id === habitId)
      if (index !== -1) {
        habitsList.value[index] = response.data
      }
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка восстановления'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Полное удаление привычки
  const deleteHabit = async (habitId) => {
    isLoading.value = true
    error.value = null
    
    try {
      await habits.delete(habitId)
      
      // Удаляем из списка
      habitsList.value = habitsList.value.filter(h => h.id !== habitId)
      
      // Очищаем текущую если это она
      if (currentHabit.value?.id === habitId) {
        currentHabit.value = null
      }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка удаления'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Отметка выполнения привычки
  const checkHabit = async (habitId, checkDate = new Date().toISOString().split('T')[0]) => {
    try {
      const response = await habits.check(habitId, { check_date: checkDate })
      
      // Обновляем streak в привычке
      const habit = habitsList.value.find(h => h.id === habitId)
      if (habit) {
        habit.current_streak = response.data.current_streak
      }
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка отметки'
      throw err
    }
  }

  // Получение статистики привычки
  const getHabitStats = async (habitId, days = 30) => {
    try {
      const response = await habits.getStats(habitId, days)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка загрузки статистики'
      throw err
    }
  }

  // Очистка стора (например при логауте)
  const $reset = () => {
    habitsList.value = []
    currentHabit.value = null
    isLoading.value = false
    error.value = null
    lastFetched.value = null
  }

  return {
    // Состояние
    habitsList,
    currentHabit,
    isLoading,
    error,
    lastFetched,
    
    // Геттеры
    activeHabits,
    archivedHabits,
    
    // Методы
    fetchHabits,
    fetchHabitById,
    createHabit,
    updateHabit,
    archiveHabit,
    restoreHabit,
    deleteHabit,
    checkHabit,
    getHabitStats,
    $reset
  }
})