<!-- views/GroupCreateView.vue -->
<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useGroupsStore } from '../stores/group'
import { useHabitsStore } from '../stores/habit'
import AppHeader from '../components/AppHeader.vue'
import PillButton from '../components/PillButton.vue'
import HabitPicker from '../components/HabitPicker.vue'

const router = useRouter()
const groupsStore = useGroupsStore()
const habitsStore = useHabitsStore()

const missOptions = [
  { value: 0, label: 'Без прощений', icon: '🎯' },
  { value: 1, label: '1 прощение', icon: '🙏' },
  { value: 2, label: '2 прощения', icon: '🤝' },
  { value: 3, label: '3 прощения', icon: '💚' }
]

const formData = ref({
  name: '',
  habit_title: '',
  habit_description: '',
  habit_type: 'daily',
  allowed_misses: 0
})

const pickedHabitId = ref(null)
const isLoading = ref(false)
const error = ref('')

// Если название разошлось с выбранной привычкой, снимаем подсветку чипа —
// иначе он врёт о том, что реально уйдёт на сервер.
watch(() => formData.value.habit_title, (newTitle) => {
  if (pickedHabitId.value === null) return
  const picked = habitsStore.activeHabits.find(h => h.id === pickedHabitId.value)
  if (!picked || picked.title !== newTitle) pickedHabitId.value = null
})

const handlePick = ({ title, description }) => {
  formData.value.habit_title = title
  formData.value.habit_description = description
}

const handleSubmit = async () => {
  if (!formData.value.name.trim()) {
    error.value = 'Название группы обязательно'
    return
  }
  if (!formData.value.habit_title.trim()) {
    error.value = 'Название привычки обязательно'
    return
  }

  isLoading.value = true
  error.value = ''

  try {
    // Группа и её первая привычка — два отдельных запроса на новом бэке:
    // группа сама по себе просто ростер, привычка привязывается к ней отдельно.
    const group = await groupsStore.createGroup({ name: formData.value.name })
    await groupsStore.addHabitToGroup(group.id, {
      title: formData.value.habit_title,
      description: formData.value.habit_description,
      habit_type: formData.value.habit_type,
      allowed_misses: formData.value.allowed_misses
    })
    router.push(`/groups/${group.id}`)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка при создании группы'
    console.error(err)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  habitsStore.fetchHabits(true).catch(() => {})
})
</script>

<template>
  <div class="screen">
    <AppHeader title="Новая группа" fallback="/groups" />

    <div class="screen-body">
      <form @submit.prevent="handleSubmit" class="group-form">
        <div class="input-group">
          <label class="input-label">Название группы</label>
          <input
            v-model="formData.name"
            type="text"
            placeholder="Например: Утренние пробежки"
            maxlength="100"
            required
            :disabled="isLoading"
            class="text-input"
          >
        </div>

        <div v-if="habitsStore.activeHabits.length" class="input-group">
          <label class="input-label">Взять из своих привычек</label>
          <HabitPicker
            :habits="habitsStore.activeHabits"
            v-model="pickedHabitId"
            @pick="handlePick"
          />
        </div>

        <div class="input-group">
          <label class="input-label">Что трекаем</label>
          <input
            v-model="formData.habit_title"
            type="text"
            placeholder="Например: Бег 3 км"
            maxlength="100"
            required
            :disabled="isLoading"
            class="text-input"
          >
        </div>

        <div class="input-group">
          <label class="input-label">Описание <span class="optional">(необязательно)</span></label>
          <textarea
            v-model="formData.habit_description"
            placeholder="Условия, детали, договорённости..."
            rows="3"
            maxlength="300"
            :disabled="isLoading"
            class="text-input"
          ></textarea>
        </div>

        <div class="input-group">
          <label class="input-label">Прощения на пропуск</label>
          <div class="type-grid">
            <button
              v-for="option in missOptions"
              :key="option.value"
              type="button"
              class="type-option"
              :class="{ active: formData.allowed_misses === option.value }"
              @click="formData.allowed_misses = option.value"
              :disabled="isLoading"
            >
              <span class="type-icon">{{ option.icon }}</span>
              <span class="type-label">{{ option.label }}</span>
            </button>
          </div>
          <span class="hint-text">Если кто-то пропустит день, вместо сброса стрика потратится прощение</span>
        </div>

        <p v-if="error" class="error-message">{{ error }}</p>

        <PillButton type="submit" :loading="isLoading">Создать группу</PillButton>
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

.hint-text {
  display: block;
  margin-top: var(--space-3);
  font-size: 12px;
  color: var(--text-tertiary);
  line-height: 1.4;
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
