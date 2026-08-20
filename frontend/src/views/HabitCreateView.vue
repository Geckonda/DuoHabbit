<!-- views/HabitCreateView.vue -->
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useHabitsStore } from '../stores/habit'
import AppHeader from '../components/AppHeader.vue'
import PillButton from '../components/PillButton.vue'

const route = useRoute()
const router = useRouter()
const habitsStore = useHabitsStore()

const isEditMode = computed(() => !!route.params.id)
const habitId = computed(() => Number(route.params.id))

const habitTypes = [
  { value: 'daily', label: 'Ежедневно', icon: '📅' },
  { value: 'weekdays', label: 'По будням', icon: '💼' },
  { value: 'weekly', label: 'Еженедельно', icon: '📆' },
  { value: 'monthly', label: 'Ежемесячно', icon: '📊' }
]

const formData = ref({
  title: '',
  description: '',
  habit_type: 'daily',
  is_private: true
})

const isLoading = ref(false)
const isFetching = ref(false)
const error = ref('')

const pageTitle = computed(() => isEditMode.value ? 'Редактировать привычку' : 'Новая привычка')
const submitLabel = computed(() => isEditMode.value ? 'Сохранить' : 'Создать привычку')
const backFallback = computed(() => isEditMode.value ? `/habits/${habitId.value}` : '/')

const loadForEdit = async () => {
  isFetching.value = true
  try {
    const habit = await habitsStore.fetchHabitById(habitId.value)
    formData.value = {
      title: habit.title,
      description: habit.description || '',
      habit_type: habit.habit_type,
      is_private: habit.is_private
    }
  } catch (err) {
    error.value = 'Не удалось загрузить привычку'
    console.error(err)
  } finally {
    isFetching.value = false
  }
}

const handleSubmit = async () => {
  if (!formData.value.title.trim()) {
    error.value = 'Название обязательно'
    return
  }

  isLoading.value = true
  error.value = ''

  try {
    if (isEditMode.value) {
      await habitsStore.updateHabit(habitId.value, formData.value)
      router.push(`/habits/${habitId.value}`)
    } else {
      await habitsStore.createHabit(formData.value)
      router.push('/')
    }
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка при сохранении привычки'
    console.error(err)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  if (isEditMode.value) loadForEdit()
})
</script>

<template>
  <div class="screen">
    <AppHeader :title="pageTitle" :fallback="backFallback" />

    <div class="screen-body">
      <div v-if="isFetching" class="loading-state">Загрузка...</div>

      <form v-else @submit.prevent="handleSubmit" class="habit-form">
        <div class="input-group">
          <label class="input-label">Название</label>
          <input
            v-model="formData.title"
            type="text"
            placeholder="Например: Утренняя пробежка"
            maxlength="100"
            required
            :disabled="isLoading"
            class="text-input"
          >
        </div>

        <div class="input-group">
          <label class="input-label">
            Описание <span class="optional">(необязательно)</span>
          </label>
          <textarea
            v-model="formData.description"
            placeholder="Опиши свою привычку подробнее..."
            rows="3"
            maxlength="300"
            :disabled="isLoading"
            class="text-input"
          ></textarea>
        </div>

        <div class="input-group">
          <label class="input-label">Периодичность</label>
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

        <div class="privacy-group">
          <label class="privacy-option">
            <input type="radio" v-model="formData.is_private" :value="true" :disabled="isLoading">
            <span class="privacy-content">
              <span class="privacy-icon">🔒</span>
              <span class="privacy-text">
                <strong>Приватная</strong>
                <span class="privacy-hint">Только ты видишь</span>
              </span>
            </span>
          </label>

          <label class="privacy-option">
            <input type="radio" v-model="formData.is_private" :value="false" :disabled="isLoading">
            <span class="privacy-content">
              <span class="privacy-icon">🌍</span>
              <span class="privacy-text">
                <strong>Публичная</strong>
                <span class="privacy-hint">Друзья увидят (скоро)</span>
              </span>
            </span>
          </label>
        </div>

        <p v-if="error" class="error-message">{{ error }}</p>

        <PillButton type="submit" :loading="isLoading">{{ submitLabel }}</PillButton>
      </form>
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
  max-width: 500px;
  width: 100%;
  margin: 0 auto;
}

.loading-state {
  text-align: center;
  padding: 60px 0;
  color: var(--text-tertiary);
}

.input-group {
  margin-bottom: var(--space-5);
}

.input-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: var(--space-2);
}

.optional {
  font-weight: 400;
  opacity: 0.7;
}

.text-input {
  width: 100%;
  padding: var(--space-4);
  background: var(--surface-card);
  border: 1.5px solid transparent;
  border-radius: var(--radius-md);
  font-size: 16px;
  color: var(--text-primary);
  font-family: inherit;
  transition: border-color 0.2s;
}

.text-input:focus {
  outline: none;
  border-color: var(--color-accent);
}

textarea.text-input {
  resize: vertical;
  min-height: 80px;
}

.type-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-2);
}

.type-option {
  padding: var(--space-3);
  background: var(--surface-card);
  border: 1.5px solid transparent;
  border-radius: var(--radius-md);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  cursor: pointer;
}

.type-option.active {
  border-color: var(--color-accent);
  background: rgba(139, 92, 246, 0.1);
}

.type-icon {
  font-size: 18px;
}

.type-label {
  font-size: 14px;
  font-weight: 500;
}

.privacy-group {
  margin-bottom: var(--space-5);
  display: flex;
  gap: var(--space-3);
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
  gap: var(--space-2);
  padding: var(--space-3);
  background: var(--surface-card);
  border: 1.5px solid transparent;
  border-radius: var(--radius-md);
}

.privacy-option input[type="radio"]:checked + .privacy-content {
  border-color: var(--color-accent);
  background: rgba(139, 92, 246, 0.1);
}

.privacy-icon {
  font-size: 18px;
}

.privacy-text {
  display: flex;
  flex-direction: column;
  color: var(--text-primary);
}

.privacy-text strong {
  font-size: 14px;
}

.privacy-hint {
  font-size: 11px;
  color: var(--text-tertiary);
}

.error-message {
  background: rgba(255, 59, 48, 0.1);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
  margin-bottom: var(--space-4);
  color: var(--color-danger);
  font-size: 14px;
}

@media (max-width: 380px) {
  .type-grid {
    grid-template-columns: 1fr;
  }
}
</style>
