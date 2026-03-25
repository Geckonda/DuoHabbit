<!-- views/HabitCreateView.vue -->
<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useHabitsStore } from '../stores/habit'

const router = useRouter()
const habitsStore = useHabitsStore()

// Типы привычек из схемы
const habitTypes = [
  { value: 'daily', label: 'Ежедневно', icon: '📅' },
  { value: 'weekdays', label: 'По будням', icon: '💼' },
  { value: 'weekly', label: 'Еженедельно', icon: '📆' },
  { value: 'monthly', label: 'Ежемесячно', icon: '📊' }
]

// Форма
const formData = ref({
  title: '',
  description: '',
  habit_type: 'daily',
  is_private: true
})

const isLoading = ref(false)
const error = ref('')

// Создание привычки
const handleSubmit = async () => {
  // Валидация
  if (!formData.value.title.trim()) {
    error.value = 'Название обязательно'
    return
  }
  
  isLoading.value = true
  error.value = ''
  
  try {
    await habitsStore.createHabit(formData.value)
    router.push('/') // назад на главную
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка при создании привычки'
    console.error(err)
  } finally {
    isLoading.value = false
  }
}

// Отмена
const handleCancel = () => {
  router.push('/')
}
</script>

<template>
  <div class="create-habit-screen">
    <div class="create-container">
      <!-- Хедер -->
      <div class="header">
        <button @click="handleCancel" class="close-btn" title="Закрыть">
          <span class="close-icon">✕</span>
        </button>
        <h1 class="page-title">Новая привычка</h1>
        <div class="placeholder"></div>
      </div>

      <!-- Форма -->
      <form @submit.prevent="handleSubmit" class="habit-form">
        <!-- Название -->
        <div class="input-group">
          <label class="input-label">
            <span class="label-icon">📝</span>
            Название
          </label>
          <input 
            v-model="formData.title"
            type="text"
            placeholder="Например: Утренняя пробежка"
            maxlength="100"
            required
            :disabled="isLoading"
            class="glass-input"
          >
          <span class="char-counter">{{ formData.title.length }}/100</span>
        </div>

        <!-- Описание -->
        <div class="input-group">
          <label class="input-label">
            <span class="label-icon">📋</span>
            Описание
            <span class="optional">(необязательно)</span>
          </label>
          <textarea 
            v-model="formData.description"
            placeholder="Опиши свою привычку подробнее..."
            rows="3"
            maxlength="300"
            :disabled="isLoading"
            class="glass-textarea"
          ></textarea>
          <span class="char-counter">{{ formData.description?.length || 0 }}/300</span>
        </div>

        <!-- Тип привычки -->
        <div class="input-group">
          <label class="input-label">
            <span class="label-icon">🔄</span>
            Периодичность
          </label>
          <div class="type-grid">
            <button
              v-for="type in habitTypes"
              :key="type.value"
              type="button"
              class="type-option"
              :class="{ active: formData.habit_type === type.value }"
              @click="formData.habit_type = type.value"
              :disabled="isLoading"
            >
              <span class="type-icon">{{ type.icon }}</span>
              <span class="type-label">{{ type.label }}</span>
            </button>
          </div>
        </div>

        <!-- Приватность -->
        <div class="privacy-group">
          <label class="privacy-option">
            <input 
              type="radio" 
              v-model="formData.is_private" 
              :value="true"
              :disabled="isLoading"
            >
            <span class="privacy-content">
              <span class="privacy-icon">🔒</span>
              <span class="privacy-text">
                <strong>Приватная</strong>
                <span class="privacy-hint">Только ты видишь</span>
              </span>
            </span>
          </label>

          <label class="privacy-option">
            <input 
              type="radio" 
              v-model="formData.is_private" 
              :value="false"
              :disabled="isLoading"
            >
            <span class="privacy-content">
              <span class="privacy-icon">🌍</span>
              <span class="privacy-text">
                <strong>Публичная</strong>
                <span class="privacy-hint">Друзья увидят (скоро)</span>
              </span>
            </span>
          </label>
        </div>

        <!-- Ошибка -->
        <p v-if="error" class="error-message">
          <span class="error-icon">⚠️</span>
          {{ error }}
        </p>

        <!-- Кнопки -->
        <div class="form-actions">
          <button 
            type="button" 
            class="cancel-btn"
            @click="handleCancel"
            :disabled="isLoading"
          >
            Отмена
          </button>
          <button 
            type="submit" 
            class="submit-btn"
            :disabled="isLoading"
          >
            <span v-if="!isLoading">Создать привычку</span>
            <span v-else class="button-loader"></span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.create-habit-screen {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  overflow-y: auto;
}

.create-container {
  width: 100%;
  max-width: 500px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 32px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
  animation: slideUp 0.5s ease;
}

/* Хедер */
.header {
  padding: 20px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.close-btn {
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

.close-btn:active {
  transform: scale(0.95);
  background: rgba(255, 255, 255, 0.3);
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.placeholder {
  width: 40px;
}

/* Форма */
.habit-form {
  padding: 24px;
}

.input-group {
  margin-bottom: 24px;
  position: relative;
}

.input-label {
  display: flex;
  align-items: center;
  gap: 6px;
  color: white;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  opacity: 0.9;
}

.label-icon {
  font-size: 16px;
}

.optional {
  font-size: 12px;
  font-weight: 400;
  opacity: 0.6;
  margin-left: 4px;
}

.glass-input,
.glass-textarea {
  width: 100%;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1.5px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  font-size: 16px;
  color: white;
  transition: all 0.3s;
}

.glass-textarea {
  resize: vertical;
  min-height: 80px;
}

.glass-input:focus,
.glass-textarea:focus {
  outline: none;
  border-color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.15);
}

.glass-input::placeholder,
.glass-textarea::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.char-counter {
  position: absolute;
  bottom: -18px;
  right: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

/* Типы привычек */
.type-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.type-option {
  padding: 14px;
  background: rgba(255, 255, 255, 0.1);
  border: 1.5px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  color: white;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.type-option.active {
  background: rgba(255, 255, 255, 0.25);
  border-color: white;
  transform: scale(1.02);
}

.type-option:active {
  transform: scale(0.98);
}

.type-icon {
  font-size: 20px;
}

.type-label {
  font-size: 14px;
  font-weight: 500;
}

/* Приватность */
.privacy-group {
  margin-bottom: 24px;
  display: flex;
  gap: 12px;
}

.privacy-option {
  flex: 1;
  cursor: pointer;
}

.privacy-option input[type="radio"] {
  display: none;
}

.privacy-content {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.1);
  border: 1.5px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  transition: all 0.3s;
}

.privacy-option input[type="radio"]:checked + .privacy-content {
  background: rgba(255, 255, 255, 0.25);
  border-color: white;
}

.privacy-icon {
  font-size: 20px;
}

.privacy-text {
  display: flex;
  flex-direction: column;
  color: white;
}

.privacy-text strong {
  font-size: 14px;
}

.privacy-hint {
  font-size: 11px;
  opacity: 0.6;
}

/* Ошибка */
.error-message {
  background: rgba(255, 59, 48, 0.2);
  border: 1px solid rgba(255, 59, 48, 0.3);
  border-radius: 16px;
  padding: 12px 16px;
  margin-bottom: 20px;
  color: white;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Кнопки */
.form-actions {
  display: flex;
  gap: 12px;
}

.cancel-btn,
.submit-btn {
  flex: 1;
  padding: 16px;
  border-radius: 24px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  border: none;
}

.cancel-btn {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.submit-btn {
  background: white;
  color: #764ba2;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
}

.cancel-btn:active,
.submit-btn:active {
  transform: scale(0.98);
}

.cancel-btn:disabled,
.submit-btn:disabled {
  opacity: 0.7;
  transform: none;
}

.button-loader {
  display: inline-block;
  width: 24px;
  height: 24px;
  border: 3px solid rgba(139, 92, 246, 0.3);
  border-radius: 50%;
  border-top-color: #764ba2;
  animation: spin 1s linear infinite;
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
  .type-grid {
    grid-template-columns: 1fr;
  }
  
  .privacy-group {
    flex-direction: column;
  }
}

</style>