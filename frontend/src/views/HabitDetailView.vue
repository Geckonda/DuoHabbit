<!-- views/HabitDetailView.vue -->
<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useHabitsStore } from '../stores/habit'

const route = useRoute()
const router = useRouter()
const habitsStore = useHabitsStore()

const habitId = Number(route.params.id)
const habit = ref(null)
const isLoading = ref(true)
const error = ref('')
const showDeleteModal = ref(false)

// Загрузка привычки
const loadHabit = async () => {
  isLoading.value = true
  error.value = ''
  
  try {
    // Загружаем с чеками для детальной инфы
    habit.value = await habitsStore.fetchHabitById(habitId, true)
  } catch (err) {
    error.value = 'Не удалось загрузить привычку'
    console.error(err)
  } finally {
    isLoading.value = false
  }
}

// Редактирование
const handleEdit = () => {
  router.push(`/habits/${habitId}/edit`)
}

// Архивация
const handleArchive = async () => {
  try {
    await habitsStore.archiveHabit(habitId)
    router.push('/')
  } catch (err) {
    error.value = 'Ошибка при архивации'
  }
}

// Восстановление из архива
const handleRestore = async () => {
  try {
    await habitsStore.restoreHabit(habitId)
    await loadHabit() // перезагружаем
  } catch (err) {
    error.value = 'Ошибка при восстановлении'
  }
}

// Удаление
const handleDelete = async () => {
  try {
    await habitsStore.deleteHabit(habitId)
    router.push('/')
  } catch (err) {
    error.value = 'Ошибка при удалении'
    showDeleteModal.value = false
  }
}

// Форматирование типа привычки
const getHabitTypeLabel = (type) => {
  const types = {
    daily: { label: 'Ежедневно', icon: '📅' },
    weekdays: { label: 'По будням', icon: '💼' },
    weekly: { label: 'Еженедельно', icon: '📆' },
    monthly: { label: 'Ежемесячно', icon: '📊' }
  }
  return types[type] || { label: type, icon: '📝' }
}

// Форматирование даты
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
  <div class="habit-detail-screen">
    <div class="detail-container">
      <!-- Хедер -->
      <div class="header">
        <button @click="router.back()" class="back-btn" title="Назад">
          <span class="back-icon">←</span>
        </button>
        <h1 class="page-title">Детали привычки</h1>
        
        <!-- Меню (три точки) -->
        <div class="menu-wrapper">
          <button class="menu-btn" @click="showMenu = !showMenu">•••</button>
          
          <!-- Выпадающее меню -->
          <div v-if="showMenu" class="dropdown-menu" v-click-outside="() => showMenu = false">
            <button @click="handleEdit" class="menu-item">
              <span class="menu-icon">✏️</span>
              Редактировать
            </button>
            <button 
              v-if="habit?.is_active"
              @click="handleArchive" 
              class="menu-item"
            >
              <span class="menu-icon">📦</span>
              Архивировать
            </button>
            <button 
              v-else
              @click="handleRestore" 
              class="menu-item"
            >
              <span class="menu-icon">🔄</span>
              Восстановить
            </button>
            <button @click="showDeleteModal = true" class="menu-item delete">
              <span class="menu-icon">🗑️</span>
              Удалить навсегда
            </button>
          </div>
        </div>
      </div>

      <!-- Контент -->
      <div class="content">
        <!-- Загрузка -->
        <div v-if="isLoading" class="loading-state">
          <div class="glass-loader"></div>
        </div>

        <!-- Ошибка -->
        <div v-else-if="error" class="error-state">
          <span class="error-icon">⚠️</span>
          <p>{{ error }}</p>
          <button @click="loadHabit" class="retry-btn">Попробовать снова</button>
        </div>

        <!-- Данные привычки -->
        <div v-else-if="habit" class="habit-detail">
          <!-- Иконка и название -->
          <div class="habit-header">
            <div class="habit-icon-large">
              {{ habit.icon || '📝' }}
            </div>
            <div class="habit-title-section">
              <h2 class="habit-title">{{ habit.title }}</h2>
              <div class="habit-badges">
                <span class="badge" :class="{ archived: !habit.is_active }">
                  {{ habit.is_active ? 'Активна' : 'В архиве' }}
                </span>
                <span class="badge type">
                  {{ getHabitTypeLabel(habit.habit_type).icon }}
                  {{ getHabitTypeLabel(habit.habit_type).label }}
                </span>
                <span class="badge privacy">
                  {{ habit.is_private ? '🔒 Приватная' : '🌍 Публичная' }}
                </span>
              </div>
            </div>
          </div>

          <!-- Статистика -->
          <div class="stats-grid">
            <div class="stat-card">
              <span class="stat-value">{{ habit.current_streak || 0 }}</span>
              <span class="stat-label">🔥 Текущий streak</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">0</span>
              <span class="stat-label">🏆 Лучший streak</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ habit.checks?.length || 0 }}</span>
              <span class="stat-label">✅ Выполнено</span>
            </div>
          </div>

          <!-- Описание -->
          <div v-if="habit.description" class="info-section">
            <h3 class="section-title">
              <span class="section-icon">📋</span>
              Описание
            </h3>
            <p class="description-text">{{ habit.description }}</p>
          </div>

          <!-- Детали -->
          <div class="info-section">
            <h3 class="section-title">
              <span class="section-icon">ℹ️</span>
              Детали
            </h3>
            <div class="details-grid">
              <div class="detail-item">
                <span class="detail-label">Создана:</span>
                <span class="detail-value">{{ formatDate(habit.created_at) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Обновлена:</span>
                <span class="detail-value">{{ formatDate(habit.updated_at) }}</span>
              </div>
            </div>
          </div>

          <!-- Последние чекины (если есть) -->
          <div v-if="habit.checks?.length" class="info-section">
            <h3 class="section-title">
              <span class="section-icon">✅</span>
              Последние выполнения
            </h3>
            <div class="checks-list">
              <div 
                v-for="check in habit.checks.slice(0, 5)" 
                :key="check.id"
                class="check-item"
              >
                <span class="check-date">{{ formatDate(check.check_date) }}</span>
                <span class="check-badge">Выполнено</span>
              </div>
            </div>
          </div>

          <!-- Кнопка отметки выполнения (для активных) -->
          <button 
            v-if="habit.is_active"
            class="check-btn"
            @click="habitsStore.checkHabit(habitId)"
          >
            <span class="check-icon">✅</span>
            Отметить выполнение
          </button>
        </div>
      </div>
    </div>

    <!-- Модалка подтверждения удаления -->
    <div v-if="showDeleteModal" class="modal-overlay" @click="showDeleteModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-icon">🗑️</div>
        <h3 class="modal-title">Удалить привычку?</h3>
        <p class="modal-text">
          Это действие нельзя отменить. Привычка будет удалена навсегда вместе со всей историей выполнений.
        </p>
        <div class="modal-actions">
          <button @click="showDeleteModal = false" class="modal-cancel">
            Отмена
          </button>
          <button @click="handleDelete" class="modal-confirm delete">
            Удалить
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.habit-detail-screen {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  padding: 16px;
  display: flex;
  align-items: flex-start;
  justify-content: center;
}

.detail-container {
  width: 100%;
  max-width: 600px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 32px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  animation: slideUp 0.5s ease;
}

/* Хедер */
.header {
  padding: 20px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  position: relative;
}

.back-btn {
  width: 40px;
  height: 40px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  font-size: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
}

.back-btn:active {
  transform: scale(0.95);
  background: rgba(255, 255, 255, 0.3);
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Меню */
.menu-wrapper {
  position: relative;
}

.menu-btn {
  width: 40px;
  height: 40px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
}

.dropdown-menu {
  position: absolute;
  top: 50px;
  right: 0;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 8px;
  min-width: 200px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  z-index: 10;
}

.menu-item {
  width: 100%;
  padding: 12px 16px;
  background: none;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  color: #1a1a1a;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.menu-item:active {
  background: rgba(0, 0, 0, 0.05);
}

.menu-item.delete {
  color: #ff3b30;
}

.menu-icon {
  font-size: 18px;
}

/* Контент */
.content {
  padding: 24px;
}

.loading-state {
  text-align: center;
  padding: 60px 0;
}

.glass-loader {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

.error-state {
  text-align: center;
  padding: 40px 0;
  color: white;
}

.error-icon {
  font-size: 48px;
  margin-bottom: 16px;
  display: block;
}

.retry-btn {
  margin-top: 20px;
  padding: 12px 24px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 30px;
  color: white;
  font-size: 16px;
  cursor: pointer;
}

/* Детали привычки */
.habit-header {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
}

.habit-icon-large {
  width: 80px;
  height: 80px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.habit-title-section {
  flex: 1;
}

.habit-title {
  font-size: 28px;
  font-weight: 600;
  color: white;
  margin-bottom: 12px;
}

.habit-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.badge {
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  font-size: 13px;
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.badge.archived {
  background: rgba(255, 193, 7, 0.2);
}

/* Статистика */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 30px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  padding: 16px 12px;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: white;
  display: block;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}

/* Секции информации */
.info-section {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 20px;
  margin-bottom: 20px;
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: white;
  margin-bottom: 16px;
}

.section-icon {
  font-size: 18px;
}

.description-text {
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.6;
  font-size: 15px;
}

.details-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  color: white;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.detail-label {
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
}

.detail-value {
  font-weight: 500;
}

/* Чекины */
.checks-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.check-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.check-date {
  color: white;
  font-size: 14px;
}

.check-badge {
  padding: 4px 10px;
  background: rgba(52, 199, 89, 0.3);
  border-radius: 20px;
  font-size: 12px;
  color: white;
}

/* Кнопка отметки */
.check-btn {
  width: 100%;
  padding: 18px;
  background: white;
  border: none;
  border-radius: 30px;
  font-size: 18px;
  font-weight: 600;
  color: #764ba2;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
  margin-top: 20px;
}

.check-btn:active {
  transform: scale(0.98);
}

/* Модалка */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 32px;
  padding: 32px;
  max-width: 400px;
  text-align: center;
  animation: slideUp 0.3s ease;
}

.modal-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.modal-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #1a1a1a;
}

.modal-text {
  color: #666;
  margin-bottom: 24px;
  line-height: 1.5;
}

.modal-actions {
  display: flex;
  gap: 12px;
}

.modal-cancel,
.modal-confirm {
  flex: 1;
  padding: 14px;
  border-radius: 24px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  border: none;
}

.modal-cancel {
  background: #f0f0f0;
  color: #666;
}

.modal-confirm.delete {
  background: #ff3b30;
  color: white;
}

/* Анимации */
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Адаптивность */
@media (max-width: 480px) {
  .habit-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  .habit-badges {
    justify-content: center;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .modal-content {
    padding: 24px;
  }
}
</style>