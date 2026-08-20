// stores/group.js
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { groups } from '../api/group'

export const useGroupsStore = defineStore('groups', () => {
  // Состояние
  const groupsList = ref([])
  const currentGroup = ref(null)
  const members = ref([])
  const checkinStatus = ref(null)
  const isLoading = ref(false)
  const error = ref(null)
  const lastFetched = ref(null) // для кеширования

  // Загрузка моих групп
  const fetchGroups = async (onlyActive = true, force = false) => {
    // Кеширование на 5 минут
    const CACHE_TIME = 5 * 60 * 1000
    const now = Date.now()

    if (!force &&
        lastFetched.value &&
        (now - lastFetched.value) < CACHE_TIME &&
        groupsList.value.length > 0) {
      return groupsList.value
    }

    isLoading.value = true
    error.value = null

    try {
      const response = await groups.getAll(onlyActive)
      groupsList.value = response.data
      lastFetched.value = now
      return groupsList.value
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка загрузки групп'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Получение группы по ID
  const fetchGroupById = async (groupId) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await groups.getById(groupId)
      currentGroup.value = response.data

      const index = groupsList.value.findIndex(g => g.id === groupId)
      if (index !== -1) {
        groupsList.value[index] = response.data
      }

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка загрузки группы'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Создание группы
  const createGroup = async (data) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await groups.create(data)
      groupsList.value.push(response.data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка создания группы'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Переименование группы
  const updateGroup = async (groupId, data) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await groups.update(groupId, data)

      const index = groupsList.value.findIndex(g => g.id === groupId)
      if (index !== -1) {
        groupsList.value[index] = { ...groupsList.value[index], ...response.data }
      }
      if (currentGroup.value?.id === groupId) {
        currentGroup.value = { ...currentGroup.value, ...response.data }
      }

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка обновления группы'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Расформирование группы
  const deleteGroup = async (groupId) => {
    isLoading.value = true
    error.value = null

    try {
      await groups.delete(groupId)
      groupsList.value = groupsList.value.filter(g => g.id !== groupId)
      if (currentGroup.value?.id === groupId) {
        currentGroup.value = null
      }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка расформирования группы'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Перегенерация инвайт-кода
  const regenerateInvite = async (groupId) => {
    try {
      const response = await groups.regenerateInvite(groupId)
      if (currentGroup.value?.id === groupId) {
        currentGroup.value = { ...currentGroup.value, invite_code: response.data.invite_code }
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка обновления инвайт-кода'
      throw err
    }
  }

  // Вступление по инвайт-коду
  const joinGroup = async (inviteCode) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await groups.join(inviteCode)
      groupsList.value.push(response.data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Не удалось присоединиться к группе'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Список участников группы
  const fetchMembers = async (groupId) => {
    try {
      const response = await groups.getMembers(groupId)
      members.value = response.data
      return members.value
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка загрузки участников'
      throw err
    }
  }

  // Добавление участника владельцем
  const addMember = async (groupId, userId) => {
    try {
      const response = await groups.addMember(groupId, userId)
      await fetchMembers(groupId)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка добавления участника'
      throw err
    }
  }

  // Удаление участника владельцем
  const removeMember = async (groupId, userId) => {
    try {
      await groups.removeMember(groupId, userId)
      members.value = members.value.filter(m => m.user_id !== userId)
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка удаления участника'
      throw err
    }
  }

  // Выход из группы
  const leaveGroup = async (groupId) => {
    try {
      await groups.leave(groupId)
      groupsList.value = groupsList.value.filter(g => g.id !== groupId)
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка выхода из группы'
      throw err
    }
  }

  // Изменение общей привычки
  const updateGroupHabit = async (groupId, data) => {
    try {
      const response = await groups.updateHabit(groupId, data)
      if (currentGroup.value?.id === groupId) {
        currentGroup.value = { ...currentGroup.value, habit: response.data }
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка обновления привычки'
      throw err
    }
  }

  // Отметка выполнения за текущий период
  const checkIn = async (groupId) => {
    try {
      const response = await groups.checkIn(groupId)
      if (currentGroup.value?.id === groupId && currentGroup.value.habit) {
        currentGroup.value.habit.current_streak = response.data.current_streak
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка отметки'
      throw err
    }
  }

  // Кто уже отметился за текущий период
  const fetchCheckinStatus = async (groupId) => {
    try {
      const response = await groups.getCheckinStatus(groupId)
      checkinStatus.value = response.data
      return checkinStatus.value
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка загрузки статуса отметок'
      throw err
    }
  }

  // Очистка стора (например при логауте)
  const $reset = () => {
    groupsList.value = []
    currentGroup.value = null
    members.value = []
    checkinStatus.value = null
    isLoading.value = false
    error.value = null
    lastFetched.value = null
  }

  return {
    // Состояние
    groupsList,
    currentGroup,
    members,
    checkinStatus,
    isLoading,
    error,
    lastFetched,

    // Методы
    fetchGroups,
    fetchGroupById,
    createGroup,
    updateGroup,
    deleteGroup,
    regenerateInvite,
    joinGroup,
    fetchMembers,
    addMember,
    removeMember,
    leaveGroup,
    updateGroupHabit,
    checkIn,
    fetchCheckinStatus,
    $reset
  }
})
