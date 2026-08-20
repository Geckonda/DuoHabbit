<!-- views/HabitDetailView.vue -->
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useHabitsStore } from '../stores/habit'
import AppHeader from '../components/AppHeader.vue'
import ActionMenu from '../components/ActionMenu.vue'
import ConfirmModal from '../components/ConfirmModal.vue'
import StatGrid from '../components/StatGrid.vue'
import GlassCard from '../components/GlassCard.vue'

const route = useRoute()
const router = useRouter()
const habitsStore = useHabitsStore()

const habitId = Number(route.params.id)
const habit = ref(null)
const isLoading = ref(true)
const error = ref('')
const showMenu = ref(false)
const showDeleteModal = ref(false)

const typeIcons = { daily: '📅', weekdays: '💼', weekly: '📆', monthly: '📊' }
const typeLabels = { daily: 'Ежедневно', weekdays: 'По будням', weekly: 'Еженедельно', monthly: 'Ежемесячно' }

const stats = computed(() => [
  { value: habit.value?.current_streak || 0, label: '🔥 Стрик' },
  { value: habit.value?.total_checks || habit.value?.recent_checks?.length || 0, label: '✅ Выполнено' },
  { value: habit.value?.is_private ? 'Личная' : 'Общая', label: '👁️ Видимость' }
])

const loadHabit = async () => {
  isLoading.value = true
  error.value = ''

  try {
    habit.value = await habitsStore.fetchHabitById(habitId, true)
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
    router.push('/')
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
        <div class="menu-wrapper">
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
            </div>
          </div>
        </div>

        <StatGrid :stats="stats" />

        <p v-if="error" class="inline-error">{{ error }}</p>

        <div class="detail-sections">
          <GlassCard v-if="habit.description" title="Описание">
            <p class="description-text">{{ habit.description }}</p>
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

        <button v-if="habit.is_active" class="check-btn" @click="handleCheckIn">
          <span class="check-icon">✅</span>
          Отметить выполнение
        </button>
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

.check-btn {
  width: 100%;
  padding: var(--space-4);
  background: var(--color-accent);
  border: none;
  border-radius: var(--radius-lg);
  font-size: 17px;
  font-weight: 600;
  color: var(--text-on-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  cursor: pointer;
  box-shadow: var(--shadow-md);
  margin-top: var(--space-6);
}

.check-btn:active {
  transform: scale(0.98);
}
</style>
