<!-- views/GroupDetailView.vue -->
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGroupsStore } from '../stores/group'
import { useHabitsStore } from '../stores/habit'
import { useUserStore } from '../stores/user'
import { users } from '../api/user'
import AppHeader from '../components/AppHeader.vue'
import ActionMenu from '../components/ActionMenu.vue'
import ConfirmModal from '../components/ConfirmModal.vue'
import PillButton from '../components/PillButton.vue'
import GlassCard from '../components/GlassCard.vue'

const route = useRoute()
const router = useRouter()
const groupsStore = useGroupsStore()
const habitsStore = useHabitsStore()
const userStore = useUserStore()

const groupId = Number(route.params.id)
const typeIcons = { daily: '📅', weekdays: '💼', weekly: '📆', monthly: '📊' }

const isLoading = ref(true)
const error = ref('')
const showMenu = ref(false)
const showDeleteModal = ref(false)
const showLeaveModal = ref(false)
const showSettingsModal = ref(false)
const showAddMemberModal = ref(false)
const userSearchQuery = ref('')
const allUsers = ref([])
const isLoadingUsers = ref(false)
const copyHint = ref('')
const checkingInId = ref(null)
const checkinStatusByHabit = ref({})

const settingsForm = ref({ name: '' })

const group = computed(() => groupsStore.currentGroup)
const members = computed(() => groupsStore.members)
const habits = computed(() => group.value?.habits || [])

const isOwner = computed(() =>
  group.value && userStore.user && group.value.owner_id === userStore.user.id
)

const filteredUsers = computed(() => {
  const memberIds = new Set(members.value.map(m => m.user_id))
  const query = userSearchQuery.value.trim().toLowerCase()
  return allUsers.value
    .filter(u => !memberIds.has(u.id))
    .filter(u => !query || u.username.toLowerCase().includes(query))
})

const hasCheckedIn = (habitId) =>
  checkinStatusByHabit.value[habitId]?.checked_in_user_ids?.includes(userStore.user?.id)

const doneCount = (habitId) => {
  const status = checkinStatusByHabit.value[habitId]
  return status ? `${status.checked_in_user_ids.length}/${status.total_active_members}` : ''
}

const loadCheckinStatuses = async () => {
  const entries = await Promise.all(
    habits.value.map(async (h) => [h.id, await habitsStore.fetchCheckinStatus(h.id)])
  )
  checkinStatusByHabit.value = Object.fromEntries(entries)
}

const load = async () => {
  isLoading.value = true
  error.value = ''

  try {
    await Promise.all([
      groupsStore.fetchGroupById(groupId),
      groupsStore.fetchMembers(groupId)
    ])
    await loadCheckinStatuses()
  } catch (err) {
    error.value = 'Не удалось загрузить группу'
    console.error(err)
  } finally {
    isLoading.value = false
  }
}

const inviteLink = computed(() => {
  if (!group.value) return ''
  return `${window.location.origin}/groups/join?code=${group.value.invite_code}`
})

const handleCopyInvite = async () => {
  try {
    await navigator.clipboard.writeText(inviteLink.value)
    copyHint.value = 'Ссылка скопирована!'
  } catch (err) {
    copyHint.value = group.value.invite_code
  }
  setTimeout(() => { copyHint.value = '' }, 2500)
}

const handleRegenerateInvite = async () => {
  try {
    await groupsStore.regenerateInvite(groupId)
    copyHint.value = 'Код обновлён'
    setTimeout(() => { copyHint.value = '' }, 2500)
  } catch (err) {
    error.value = 'Не удалось обновить код'
  }
}

const handleAddHabit = () => {
  router.push(`/groups/${groupId}/habits/new`)
}

const handleCheckIn = async (habitId) => {
  checkingInId.value = habitId
  try {
    const result = await habitsStore.checkHabit(habitId)

    // Карточка рендерится из group.habits (groupsStore), а не из habitsStore —
    // патчим стрики прямо тут, иначе останутся старые значения до перезагрузки страницы.
    const habitInGroup = habits.value.find(h => h.id === habitId)
    if (habitInGroup) {
      habitInGroup.current_streak = result.current_streak
      habitInGroup.my_current_streak = result.my_current_streak
    }

    checkinStatusByHabit.value[habitId] = await habitsStore.fetchCheckinStatus(habitId)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка при отметке'
  } finally {
    checkingInId.value = null
  }
}

const openSettings = () => {
  settingsForm.value = { name: group.value.name }
  showSettingsModal.value = true
}

const handleSaveSettings = async () => {
  try {
    await groupsStore.updateGroup(groupId, { name: settingsForm.value.name })
    showSettingsModal.value = false
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка сохранения настроек'
  }
}

const handleRemoveMember = async (member) => {
  try {
    await groupsStore.removeMember(groupId, member.user_id)
    await loadCheckinStatuses()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка удаления участника'
  }
}

const openAddMember = async () => {
  userSearchQuery.value = ''
  showAddMemberModal.value = true

  if (allUsers.value.length === 0) {
    isLoadingUsers.value = true
    try {
      const response = await users.getAll()
      allUsers.value = response.data
    } catch (err) {
      error.value = 'Не удалось загрузить список пользователей'
    } finally {
      isLoadingUsers.value = false
    }
  }
}

const handleAddMember = async (user) => {
  try {
    // Приглашение, не мгновенное членство - участники/привычки не меняются,
    // пока юзер сам не примет приглашение
    await groupsStore.addMember(groupId, user.id)
    // Не активный участник, поэтому из filteredUsers сам не пропадет - убираем
    // руками, иначе пикер тут же предложит пригласить его повторно
    allUsers.value = allUsers.value.filter((u) => u.id !== user.id)
    showAddMemberModal.value = false
    copyHint.value = `Приглашение отправлено: ${user.username}`
    setTimeout(() => { copyHint.value = '' }, 2500)
  } catch (err) {
    // Уже приглашен (кем-то еще, или до того как открыли этот список) - тоже
    // прячем из пикера вместо того чтобы просто показать ошибку
    if (err.response?.status === 409) {
      allUsers.value = allUsers.value.filter((u) => u.id !== user.id)
    }
    error.value = err.response?.data?.detail || 'Ошибка приглашения участника'
  }
}

const handleDelete = async () => {
  try {
    await groupsStore.deleteGroup(groupId)
    router.push('/groups')
  } catch (err) {
    error.value = 'Ошибка при расформировании'
    showDeleteModal.value = false
  }
}

const handleLeave = async () => {
  try {
    await groupsStore.leaveGroup(groupId)
    router.push('/groups')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка при выходе из группы'
    showLeaveModal.value = false
  }
}

onMounted(() => {
  load()
})
</script>

<template>
  <div class="screen">
    <AppHeader :title="group?.name || 'Группа'" fallback="/groups">
      <template #right>
        <div class="menu-wrapper">
          <button class="menu-btn" @click="showMenu = !showMenu">•••</button>
          <ActionMenu v-model="showMenu">
            <template v-if="isOwner">
              <button @click="handleAddHabit" class="menu-item">
                <span class="menu-icon">➕</span>
                Добавить привычку
              </button>
              <button @click="handleCopyInvite" class="menu-item">
                <span class="menu-icon">🔗</span>
                Скопировать ссылку-приглашение
              </button>
              <button @click="handleRegenerateInvite" class="menu-item">
                <span class="menu-icon">🔄</span>
                Обновить код приглашения
              </button>
              <button @click="openAddMember" class="menu-item">
                <span class="menu-icon">👤</span>
                Добавить участника
              </button>
              <button @click="openSettings" class="menu-item">
                <span class="menu-icon">⚙️</span>
                Переименовать
              </button>
              <button @click="showDeleteModal = true" class="menu-item delete">
                <span class="menu-icon">🗑️</span>
                Расформировать
              </button>
            </template>
            <template v-else>
              <button @click="showLeaveModal = true" class="menu-item delete">
                <span class="menu-icon">🚪</span>
                Покинуть группу
              </button>
            </template>
          </ActionMenu>
        </div>
      </template>
    </AppHeader>

    <div class="screen-body">
      <div v-if="isLoading" class="loading-state">Загрузка...</div>

      <div v-else-if="error && !group" class="error-state">
        <p>{{ error }}</p>
        <button @click="load" class="retry-btn">Попробовать снова</button>
      </div>

      <div v-else-if="group" class="group-info">
        <div class="group-summary">
          <span>👥 {{ group.member_count }} {{ group.member_count === 1 ? 'участник' : 'участников' }}</span>
          <span>📋 {{ habits.length }} {{ habits.length === 1 ? 'привычка' : 'привычек' }}</span>
        </div>

        <p v-if="copyHint" class="copy-hint">{{ copyHint }}</p>
        <p v-if="error" class="inline-error">{{ error }}</p>

        <div v-if="habits.length === 0" class="empty-habits">
          <p>У группы пока нет общих привычек</p>
          <PillButton v-if="isOwner" @click="handleAddHabit">Добавить привычку</PillButton>
          <p v-else class="empty-hint">Владелец ещё не добавил ни одной</p>
        </div>

        <div v-else class="habits-list">
          <div
            v-for="habit in habits"
            :key="habit.id"
            class="habit-card"
            @click="router.push(`/habits/${habit.id}`)"
          >
            <div class="habit-card-top">
              <span class="habit-card-icon">{{ typeIcons[habit.habit_type] || '📝' }}</span>
              <div class="habit-card-title-block">
                <span class="habit-card-title">{{ habit.title }}</span>
                <span v-if="doneCount(habit.id)" class="habit-card-meta">
                  {{ doneCount(habit.id) }} отметилось сегодня
                </span>
              </div>
              <span class="chevron">›</span>
            </div>
            <div class="habit-card-stats">
              <span>🔥 {{ habit.current_streak }}</span>
              <span>🙋 {{ habit.my_current_streak }}</span>
            </div>
            <PillButton
              class="habit-card-check"
              :variant="hasCheckedIn(habit.id) ? 'secondary' : 'primary'"
              :disabled="hasCheckedIn(habit.id)"
              :loading="checkingInId === habit.id"
              @click.stop="handleCheckIn(habit.id)"
            >
              {{ hasCheckedIn(habit.id) ? 'Уже отмечено' : 'Отметить выполнение' }}
            </PillButton>
          </div>
        </div>

        <GlassCard title="Участники" class="members-card">
          <div class="members-list">
            <div v-for="member in members" :key="member.id" class="member-item">
              <div class="member-info">
                <span class="member-name">{{ member.username }}</span>
                <span v-if="member.role === 'owner'" class="owner-badge">владелец</span>
              </div>
              <button
                v-if="isOwner && member.user_id !== group.owner_id"
                @click="handleRemoveMember(member)"
                class="remove-member-btn"
                title="Удалить участника"
              >✕</button>
            </div>
          </div>
        </GlassCard>
      </div>
    </div>

    <ConfirmModal
      v-model="showDeleteModal"
      icon="🗑️"
      title="Расформировать группу?"
      text="Это действие нельзя отменить. Группа, все её привычки и история отметок будут удалены навсегда для всех участников."
      confirm-label="Расформировать"
      danger
      @confirm="handleDelete"
    />

    <ConfirmModal
      v-model="showLeaveModal"
      icon="🚪"
      title="Покинуть группу?"
      text="Ваши стрики по общим привычкам группы заморозятся. Вернуться можно будет только по новому приглашению, стрик начнётся заново."
      confirm-label="Покинуть"
      danger
      @confirm="handleLeave"
    />

    <div v-if="showSettingsModal" class="modal-overlay" @click="showSettingsModal = false">
      <div class="modal-content settings-modal" @click.stop>
        <h3 class="modal-title">Переименовать группу</h3>
        <div class="settings-form">
          <label class="settings-label">Название группы</label>
          <input v-model="settingsForm.name" type="text" class="settings-input" maxlength="100">
        </div>
        <div class="modal-actions">
          <button @click="showSettingsModal = false" class="modal-cancel">Отмена</button>
          <button @click="handleSaveSettings" class="modal-confirm">Сохранить</button>
        </div>
      </div>
    </div>

    <div v-if="showAddMemberModal" class="modal-overlay" @click="showAddMemberModal = false">
      <div class="modal-content settings-modal" @click.stop>
        <h3 class="modal-title">Добавить участника</h3>
        <input
          v-model="userSearchQuery"
          type="text"
          placeholder="Поиск по имени пользователя"
          class="settings-input search-input"
        >
        <div class="user-search-list">
          <div v-if="isLoadingUsers" class="loading">Загрузка...</div>
          <div v-else-if="filteredUsers.length === 0" class="loading">Никого не нашлось</div>
          <button
            v-for="u in filteredUsers"
            :key="u.id"
            class="user-search-item"
            @click="handleAddMember(u)"
          >
            {{ u.username }}
          </button>
        </div>
        <div class="modal-actions">
          <button @click="showAddMemberModal = false" class="modal-cancel">Закрыть</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.screen {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.screen-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-4);
  max-width: 600px;
  width: 100%;
  margin: 0 auto;
}

.menu-wrapper {
  position: relative;
}

.menu-btn {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-pill);
  background: var(--surface-card);
  border: none;
  color: var(--text-primary);
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
}

.loading-state,
.error-state {
  text-align: center;
  padding: 60px 0;
  color: var(--text-tertiary);
}

.retry-btn {
  margin-top: var(--space-4);
  padding: var(--space-3) var(--space-6);
  background: var(--surface-card);
  border: none;
  border-radius: var(--radius-pill);
  color: var(--color-ios-blue);
  cursor: pointer;
  box-shadow: var(--shadow-sm);
}

.group-summary {
  display: flex;
  gap: var(--space-4);
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: var(--space-5);
}

.copy-hint {
  color: #248A3D;
  background: rgba(52, 199, 89, 0.12);
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-3);
  font-size: 13px;
  margin-bottom: var(--space-4);
  text-align: center;
}

.inline-error {
  color: var(--color-danger);
  font-size: 13px;
  margin: var(--space-4) 0;
}

.empty-habits {
  text-align: center;
  padding: var(--space-8) var(--space-4);
  background: var(--surface-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.empty-habits p {
  color: var(--text-tertiary);
  margin-bottom: var(--space-4);
}

.empty-hint {
  margin-bottom: 0 !important;
  font-size: 13px;
}

.habits-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.habit-card {
  background: var(--surface-card);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
}

.habit-card-top {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.habit-card-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.habit-card-title-block {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.habit-card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.habit-card-meta {
  font-size: 12px;
  color: var(--text-tertiary);
}

.chevron {
  color: var(--color-gray-light);
  font-size: 20px;
  flex-shrink: 0;
}

.habit-card-stats {
  display: flex;
  gap: var(--space-4);
  margin: var(--space-3) 0;
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

.habit-card-check {
  width: 100%;
}

.members-card {
  margin-top: var(--space-4);
}

.members-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.member-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3);
  background: rgba(0, 0, 0, 0.03);
  border-radius: var(--radius-sm);
}

.member-info {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.member-name {
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
}

.owner-badge {
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(0, 0, 0, 0.06);
  border-radius: var(--radius-pill);
  color: var(--text-tertiary);
}

.remove-member-btn {
  width: 22px;
  height: 22px;
  border-radius: var(--radius-pill);
  background: rgba(255, 59, 48, 0.12);
  border: none;
  color: var(--color-danger);
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-4);
  z-index: var(--z-modal);
}

.modal-content {
  background: var(--surface-overlay);
  border-radius: var(--radius-xl);
  padding: var(--space-8);
  max-width: 400px;
  width: 100%;
  text-align: center;
}

.modal-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: var(--space-4);
  color: var(--text-primary);
}

.modal-actions {
  display: flex;
  gap: var(--space-3);
  margin-top: var(--space-2);
}

.modal-cancel,
.modal-confirm {
  flex: 1;
  padding: var(--space-3);
  border-radius: var(--radius-lg);
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  border: none;
}

.modal-cancel {
  background: rgba(0, 0, 0, 0.06);
  color: var(--text-secondary);
}

.modal-confirm {
  background: var(--color-accent);
  color: var(--text-on-accent);
}

.settings-modal {
  text-align: left;
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.settings-label {
  font-size: 13px;
  color: var(--text-tertiary);
  margin-top: var(--space-2);
}

.settings-input {
  width: 100%;
  padding: var(--space-3);
  border: 1.5px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  font-size: 15px;
  color: var(--text-primary);
  font-family: inherit;
}

.settings-input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.search-input {
  margin-bottom: var(--space-3);
}

.user-search-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  max-height: 240px;
  overflow-y: auto;
  margin-bottom: var(--space-4);
}

.user-search-list .loading {
  text-align: center;
  color: var(--text-tertiary);
  padding: var(--space-5) 0;
  font-size: 14px;
}

.user-search-item {
  width: 100%;
  padding: var(--space-3);
  background: rgba(0, 0, 0, 0.03);
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--text-primary);
  text-align: left;
  cursor: pointer;
}

.user-search-item:active {
  background: rgba(0, 0, 0, 0.06);
}
</style>
