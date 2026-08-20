<!-- views/GroupDetailView.vue -->
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGroupsStore } from '../stores/group'
import { useUserStore } from '../stores/user'
import { users } from '../api/user'
import AppHeader from '../components/AppHeader.vue'
import ActionMenu from '../components/ActionMenu.vue'
import ConfirmModal from '../components/ConfirmModal.vue'
import StatGrid from '../components/StatGrid.vue'
import PillButton from '../components/PillButton.vue'
import GlassCard from '../components/GlassCard.vue'

const route = useRoute()
const router = useRouter()
const groupsStore = useGroupsStore()
const userStore = useUserStore()

const groupId = Number(route.params.id)

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

const settingsForm = ref({
  name: '',
  habit_title: '',
  habit_description: '',
  allowed_misses: 0
})

const group = computed(() => groupsStore.currentGroup)
const members = computed(() => groupsStore.members)
const checkinStatus = computed(() => groupsStore.checkinStatus)

const isOwner = computed(() =>
  group.value && userStore.user && group.value.owner_id === userStore.user.id
)

const hasCheckedInToday = computed(() =>
  checkinStatus.value?.checked_in_user_ids?.includes(userStore.user?.id)
)

const stats = computed(() => [
  { value: group.value?.habit?.current_streak || 0, label: '🔥 Стрик' },
  { value: `${group.value?.habit?.misses_remaining ?? 0}/${group.value?.habit?.allowed_misses ?? 0}`, label: '🛡️ Прощений' },
  { value: group.value?.member_count || members.value.length, label: '👥 Участников' }
])

const filteredUsers = computed(() => {
  const memberIds = new Set(members.value.map(m => m.user_id))
  const query = userSearchQuery.value.trim().toLowerCase()
  return allUsers.value
    .filter(u => !memberIds.has(u.id))
    .filter(u => !query || u.username.toLowerCase().includes(query))
})

const load = async () => {
  isLoading.value = true
  error.value = ''

  try {
    await Promise.all([
      groupsStore.fetchGroupById(groupId),
      groupsStore.fetchMembers(groupId),
      groupsStore.fetchCheckinStatus(groupId)
    ])
  } catch (err) {
    error.value = 'Не удалось загрузить группу'
    console.error(err)
  } finally {
    isLoading.value = false
  }
}

const isCheckedIn = (userId) => checkinStatus.value?.checked_in_user_ids?.includes(userId)

const handleCheckIn = async () => {
  try {
    await groupsStore.checkIn(groupId)
    await groupsStore.fetchCheckinStatus(groupId)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка при отметке'
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

const openSettings = () => {
  settingsForm.value = {
    name: group.value.name,
    habit_title: group.value.habit?.title || '',
    habit_description: group.value.habit?.description || '',
    allowed_misses: group.value.habit?.allowed_misses ?? 0
  }
  showSettingsModal.value = true
}

const handleSaveSettings = async () => {
  try {
    await groupsStore.updateGroup(groupId, { name: settingsForm.value.name })
    await groupsStore.updateGroupHabit(groupId, {
      title: settingsForm.value.habit_title,
      description: settingsForm.value.habit_description,
      allowed_misses: settingsForm.value.allowed_misses
    })
    showSettingsModal.value = false
    await load()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка сохранения настроек'
  }
}

const handleRemoveMember = async (member) => {
  try {
    await groupsStore.removeMember(groupId, member.user_id)
    await groupsStore.fetchCheckinStatus(groupId)
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
    await groupsStore.addMember(groupId, user.id)
    await groupsStore.fetchCheckinStatus(groupId)
    showAddMemberModal.value = false
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка добавления участника'
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
              <button @click="handleCopyInvite" class="menu-item">
                <span class="menu-icon">🔗</span>
                Скопировать ссылку-приглашение
              </button>
              <button @click="handleRegenerateInvite" class="menu-item">
                <span class="menu-icon">🔄</span>
                Обновить код приглашения
              </button>
              <button @click="openAddMember" class="menu-item">
                <span class="menu-icon">➕</span>
                Добавить участника
              </button>
              <button @click="openSettings" class="menu-item">
                <span class="menu-icon">⚙️</span>
                Настройки
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
        <div class="group-header">
          <p v-if="group.habit" class="habit-title">{{ group.habit.title }}</p>
          <p v-if="group.habit?.description" class="habit-description">{{ group.habit.description }}</p>
        </div>

        <p v-if="copyHint" class="copy-hint">{{ copyHint }}</p>

        <StatGrid :stats="stats" />

        <p v-if="error" class="inline-error">{{ error }}</p>

        <GlassCard title="Участники" class="members-card">
          <div class="members-list">
            <div v-for="member in members" :key="member.id" class="member-item">
              <div class="member-info">
                <span class="member-name">{{ member.username }}</span>
                <span v-if="member.role === 'owner'" class="owner-badge">владелец</span>
              </div>
              <div class="member-actions">
                <span class="check-indicator">{{ isCheckedIn(member.user_id) ? '✅' : '⏳' }}</span>
                <button
                  v-if="isOwner && member.user_id !== group.owner_id"
                  @click="handleRemoveMember(member)"
                  class="remove-member-btn"
                  title="Удалить участника"
                >✕</button>
              </div>
            </div>
          </div>
        </GlassCard>

        <PillButton
          class="check-btn-wrap"
          :variant="hasCheckedInToday ? 'secondary' : 'primary'"
          :disabled="hasCheckedInToday"
          @click="handleCheckIn"
        >
          {{ hasCheckedInToday ? '✅ Уже отмечено сегодня' : '🔥 Отметить выполнение' }}
        </PillButton>
      </div>
    </div>

    <ConfirmModal
      v-model="showDeleteModal"
      icon="🗑️"
      title="Расформировать группу?"
      text="Это действие нельзя отменить. Группа, привычка и вся история отметок будут удалены навсегда для всех участников."
      confirm-label="Расформировать"
      danger
      @confirm="handleDelete"
    />

    <ConfirmModal
      v-model="showLeaveModal"
      icon="🚪"
      title="Покинуть группу?"
      text="Вы больше не будете участвовать в общем стрике. Вернуться можно будет только по новому приглашению."
      confirm-label="Покинуть"
      danger
      @confirm="handleLeave"
    />

    <div v-if="showSettingsModal" class="modal-overlay" @click="showSettingsModal = false">
      <div class="modal-content settings-modal" @click.stop>
        <h3 class="modal-title">Настройки группы</h3>
        <div class="settings-form">
          <label class="settings-label">Название группы</label>
          <input v-model="settingsForm.name" type="text" class="settings-input" maxlength="100">

          <label class="settings-label">Название привычки</label>
          <input v-model="settingsForm.habit_title" type="text" class="settings-input" maxlength="100">

          <label class="settings-label">Описание</label>
          <textarea v-model="settingsForm.habit_description" class="settings-input" rows="2" maxlength="300"></textarea>

          <label class="settings-label">Прощений на пропуск</label>
          <input v-model.number="settingsForm.allowed_misses" type="number" min="0" max="3" class="settings-input">
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

.group-header {
  margin-bottom: var(--space-5);
}

.habit-title {
  font-size: 20px;
  color: var(--text-primary);
  font-weight: 700;
}

.habit-description {
  font-size: 14px;
  color: var(--text-tertiary);
  margin-top: var(--space-1);
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

.member-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.check-indicator {
  font-size: 16px;
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

.check-btn-wrap {
  margin-top: var(--space-6);
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
