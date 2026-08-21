// stores/group.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { groups } from '../api/group'

export const useGroupsStore = defineStore('groups', () => {
  // Состояние
  const groupsList = ref([])
  const currentGroup = ref(null)
  const members = ref([])
  const isLoading = ref(false)
  const error = ref(null)
  const lastFetched = ref(null) // для кеширования

  // Инвайты/заявки, ждущие моего ответа
  const myInvites = ref([])
  const myRequests = ref([])
  const pendingCount = computed(() => myInvites.value.length + myRequests.value.length)

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

  // Создание группы (только имя — привычки добавляются отдельным вызовом)
  const createGroup = async (data) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await groups.create({ name: data.name })
      groupsList.value.push(response.data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка создания группы'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Добавление новой общей привычки в группу (только владелец)
  const addHabitToGroup = async (groupId, habitData) => {
    try {
      const response = await groups.addHabit(groupId, habitData)

      if (currentGroup.value?.id === groupId) {
        currentGroup.value.habits = [...(currentGroup.value.habits || []), response.data]
      }
      const group = groupsList.value.find(g => g.id === groupId)
      if (group) {
        group.habits = [...(group.habits || []), response.data]
      }

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка добавления привычки'
      throw err
    }
  }

  // Список привычек группы (обычно не нужен отдельно — приходят вместе с группой)
  const fetchGroupHabits = async (groupId) => {
    try {
      const response = await groups.getHabits(groupId)
      if (currentGroup.value?.id === groupId) {
        currentGroup.value.habits = response.data
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка загрузки привычек группы'
      throw err
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

  // Заявка на вступление по инвайт-коду - членство только после одобрения владельцем,
  // так что в groupsList её пушить рано (юзер группу пока не видит)
  const joinGroup = async (inviteCode) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await groups.join(inviteCode)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Не удалось отправить заявку'
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

  // Приглашение участника владельцем - членство только после его accept,
  // поэтому список участников тут не трогаем (новый участник в нём не появится)
  const addMember = async (groupId, userId) => {
    try {
      const response = await groups.addMember(groupId, userId)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Ошибка приглашения участника'
      throw err
    }
  }

  // ===== Инвайты / заявки =====

  const fetchMyInvites = async () => {
    try {
      const response = await groups.getMyInvites()
      myInvites.value = response.data
      return myInvites.value
    } catch (err) {
      console.error('Ошибка загрузки инвайтов:', err)
      throw err
    }
  }

  const fetchMyRequests = async () => {
    try {
      const response = await groups.getMyRequests()
      myRequests.value = response.data
      return myRequests.value
    } catch (err) {
      console.error('Ошибка загрузки заявок:', err)
      throw err
    }
  }

  const acceptInvite = async (groupId) => {
    const response = await groups.acceptInvite(groupId)
    myInvites.value = myInvites.value.filter((i) => i.group_id !== groupId)
    groupsList.value.push(response.data)
    return response.data
  }

  const declineInvite = async (groupId) => {
    await groups.declineInvite(groupId)
    myInvites.value = myInvites.value.filter((i) => i.group_id !== groupId)
  }

  const approveRequest = async (groupId, userId) => {
    const response = await groups.approveRequest(groupId, userId)
    myRequests.value = myRequests.value.filter(
      (r) => !(r.group_id === groupId && r.user_id === userId)
    )
    return response.data
  }

  const rejectRequest = async (groupId, userId) => {
    await groups.rejectRequest(groupId, userId)
    myRequests.value = myRequests.value.filter(
      (r) => !(r.group_id === groupId && r.user_id === userId)
    )
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

  // Очистка стора (например при логауте)
  const $reset = () => {
    groupsList.value = []
    currentGroup.value = null
    members.value = []
    isLoading.value = false
    error.value = null
    lastFetched.value = null
    myInvites.value = []
    myRequests.value = []
  }

  return {
    // Состояние
    groupsList,
    currentGroup,
    members,
    isLoading,
    error,
    lastFetched,
    myInvites,
    myRequests,
    pendingCount,

    // Методы
    fetchGroups,
    fetchGroupById,
    createGroup,
    addHabitToGroup,
    fetchGroupHabits,
    updateGroup,
    deleteGroup,
    regenerateInvite,
    joinGroup,
    fetchMembers,
    addMember,
    removeMember,
    leaveGroup,
    fetchMyInvites,
    fetchMyRequests,
    acceptInvite,
    declineInvite,
    approveRequest,
    rejectRequest,
    $reset
  }
})
