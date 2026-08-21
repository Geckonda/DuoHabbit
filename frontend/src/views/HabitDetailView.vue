<!-- views/HabitDetailView.vue -->
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useHabitsStore } from '../stores/habit'
import { useGroupsStore } from '../stores/group'
import { useUserStore } from '../stores/user'
import AppHeader from '../components/AppHeader.vue'
import ActionMenu from '../components/ActionMenu.vue'
import ConfirmModal from '../components/ConfirmModal.vue'
import StatGrid from '../components/StatGrid.vue'
import GlassCard from '../components/GlassCard.vue'
import PillButton from '../components/PillButton.vue'

const route = useRoute()
const router = useRouter()
const habitsStore = useHabitsStore()
const groupsStore = useGroupsStore()
const userStore = useUserStore()

const habitId = Number(route.params.id)
const habit = ref(null)
const groupMembers = ref([])
const checkinStatus = ref(null)
const isLoading = ref(true)
const error = ref('')
const showMenu = ref(false)
const showDeleteModal = ref(false)

const typeIcons = { daily: '📅', weekdays: '💼', weekly: '📆', monthly: '📊' }
const typeLabels = { daily: 'Ежедневно', weekdays: 'По будням', weekly: 'Еженедельно', monthly: 'Ежемесячно' }

const isGroupHabit = computed(() => !!habit.value?.group_id)
const isCreator = computed(() =>
  habit.value && userStore.user && habit.value.creator_id === userStore.user.id
)
const hasCheckedInToday = computed(() =>
  checkinStatus.value?.checked_in_user_ids?.includes(userStore.user?.id)
)

const stats = computed(() => {
  if (!habit.value) return []
  if (isGroupHabit.value) {
    return [
      { value: habit.value.current_streak || 0, label: '🔥 Стрик команды' },
      { value: habit.value.my_current_streak || 0, label: '🙋 Моя серия' },
      { value: `${habit.value.my_misses_remaining ?? 0}/${habit.value.allowed_misses ?? 0}`, label: '🛡️ Прощений' }
    ]
  }
  return [
    { value: habit.value.current_streak || 0, label: '🔥 Стрик' },
    { value: `${habit.value.my_misses_remaining ?? 0}/${habit.value.allowed_misses ?? 0}`, label: '🛡️ Прощений' },
    { value: habit.value.is_private ? 'Личная' : 'Общая', label: '👁️ Видимость' }
  ]
})

const memberStatus = computed(() =>
  groupMembers.value.map(m => ({
    ...m,
    checkedIn: checkinStatus.value?.checked_in_user_ids?.includes(m.user_id)
  }))
)

const loadHabit = async () => {
  isLoading.value = true
  error.value = ''

  try {
    habit.value = await habitsStore.fetchHabitById(habitId, true)
    checkinStatus.value = await habitsStore.fetchCheckinStatus(habitId)

    if (habit.value.group_id) {
      groupMembers.value = await groupsStore.fetchMembers(habit.value.group_id)
    }
  } catch (err) {
    error.value = 'Не удалось загрузить привычку'
    console.error(err)
  } finally {
    isLoading.value = false
  }
}

const handleEdit = () => {
  router.push(`/habits/${habitId}/edit`)
}

const handleArchive = async () => {
  try {
    await habitsStore.archiveHabit(habitId)
    await loadHabit()
  } catch (err) {
    error.value = 'Ошибка при архивации'
  }
}

const handleRestore = async () => {
  try {
    await habitsStore.restoreHabit(habitId)
    await loadHabit()
  } catch (err) {
    error.value = 'Ошибка при восстановлении'
  }
}

const handleDelete = async () => {
  try {
    await habitsStore.deleteHabit(habitId)
    router.push(isGroupHabit.value ? `/groups/${habit.value.group_id}` : '/')
  } catch (err) {
    error.value = 'Ошибка при удалении'
    showDeleteModal.value = false
  }
}

const handleCheckIn = async () => {
  try {
    await habitsStore.checkHabit(habitId)
    await loadHabit()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка при отметке'
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return 'не указано'
  return new Date(dateStr).toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

onMounted(() => {
  loadHabit()
})
</script>

<template>
  <div class="screen">
    <AppHeader :title="habit?.title || 'Привычка'" fallback="/">
      <template #right>
        <div v-if="isCreator" class="menu-wrapper">
          <button class="menu-btn" @click="showMenu = !showMenu">•••</button>
          <ActionMenu v-model="showMenu">
            <button @click="handleEdit" class="menu-item">
              <span class="menu-icon">✏️</span>
              Редактировать
            </button>
            <button v-if="habit?.is_active" @click="handleArchive" class="menu-item">
              <span class="menu-icon">📦</span>
              Архивировать
            </button>
            <button v-else @click="handleRestore" class="menu-item">
              <span class="menu-icon">🔄</span>
              Восстановить
            </button>
            <button @click="showDeleteModal = true" class="menu-item delete">
              <span class="menu-icon">🗑️</span>
              Удалить навсегда
            </button>
          </ActionMenu>
        </div>
      </template>
    </AppHeader>

    <div class="screen-body">
      <div v-if="isLoading" class="loading-state">Загрузка...</div>

      <div v-else-if="error && !habit" class="error-state">
        <p>{{ error }}</p>
        <button @click="loadHabit" class="retry-btn">Попробовать снова</button>
      </div>

      <div v-else-if="habit" class="habit-detail">
        <div class="habit-header">
          <div class="habit-icon-large">{{ typeIcons[habit.habit_type] || '📝' }}</div>
          <div class="habit-title-section">
            <h2 class="habit-title">{{ habit.title }}</h2>
            <div class="habit-badges">
              <span class="badge" :class="{ archived: !habit.is_active }">
                {{ habit.is_active ? 'Активна' : 'В архиве' }}
              </span>
              <span class="badge">{{ typeLabels[habit.habit_type] || habit.habit_type }}</span>
              <router-link
                v-if="isGroupHabit"
                :to="`/groups/${habit.group_id}`"
                class="badge group-badge"
              >👥 Групповая</router-link>
            </div>
          </div>
        </div>

        <StatGrid :stats="stats" />

        <p v-if="error" class="inline-error">{{ error }}</p>

        <div class="detail-sections">
          <GlassCard v-if="habit.description" title="Описание">
            <p class="description-text">{{ habit.description }}</p>
          </GlassCard>

          <GlassCard v-if="isGroupHabit" title="Кто сегодня отметился">
            <div class="checks-list">
              <div v-for="m in memberStatus" :key="m.id" class="check-item">
                <span class="check-date">{{ m.username }}</span>
                <span class="check-badge" :class="{ pending: !m.checkedIn }">
                  {{ m.checkedIn ? 'Отметился' : 'Ждём' }}
                </span>
              </div>
            </div>
          </GlassCard>

          <GlassCard title="Детали">
            <div class="details-grid">
              <div class="detail-item">
                <span class="detail-label">Создана</span>
                <span class="detail-value">{{ formatDate(habit.created_at) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Обновлена</span>
                <span class="detail-value">{{ formatDate(habit.updated_at) }}</span>
              </div>
            </div>
          </GlassCard>

          <GlassCard v-if="habit.recent_checks?.length" title="Последние выполнения">
            <div class="checks-list">
              <div v-for="check in habit.recent_checks.slice(0, 5)" :key="check.id" class="check-item">
                <span class="check-date">{{ formatDate(check.check_date) }}</span>
                <span class="check-badge">Выполнено</span>
              </div>
            </div>
          </GlassCard>
        </div>

        <PillButton
          v-if="habit.is_active"
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
      title="Удалить привычку?"
      text="Это действие нельзя отменить. Привычка будет удалена навсегда вместе со всей историей выполнений."
      confirm-label="Удалить"
      danger
      @confirm="handleDelete"
    />
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

.habit-header {
  display: flex;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.habit-icon-large {
  width: 64px;
  height: 64px;
  background: var(--surface-card);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  flex-shrink: 0;
  box-shadow: var(--shadow-sm);
}

.habit-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: var(--space-2);
}

.habit-badges {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.badge {
  padding: 4px 10px;
  background: var(--surface-card);
  border-radius: var(--radius-pill);
  font-size: 12px;
  color: var(--text-secondary);
}

.badge.archived {
  background: rgba(255, 149, 0, 0.15);
  color: #B25E00;
}

.group-badge {
  text-decoration: none;
  background: rgba(139, 92, 246, 0.12);
  color: var(--color-accent);
  font-weight: 500;
}

.inline-error {
  color: var(--color-danger);
  font-size: 13px;
  margin: var(--space-4) 0;
}

.detail-sections {
  margin-top: var(--space-4);
}

.description-text {
  color: var(--text-secondary);
  line-height: 1.5;
  font-size: 15px;
}

.details-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: var(--space-2) 0;
  border-bottom: 1px solid var(--border-subtle);
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-label {
  color: var(--text-tertiary);
  font-size: 14px;
}

.detail-value {
  font-weight: 500;
  color: var(--text-primary);
  font-size: 14px;
}

.checks-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.check-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3);
  background: rgba(0, 0, 0, 0.03);
  border-radius: var(--radius-sm);
}

.check-date {
  font-size: 14px;
  color: var(--text-primary);
}

.check-badge {
  padding: 3px 10px;
  background: rgba(52, 199, 89, 0.15);
  border-radius: var(--radius-pill);
  font-size: 12px;
  color: #248A3D;
}

.check-badge.pending {
  background: rgba(0, 0, 0, 0.06);
  color: var(--text-tertiary);
}

.check-btn-wrap {
  margin-top: var(--space-6);
}
</style>
