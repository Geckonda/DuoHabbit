<!-- views/HomeView.vue -->
<script setup>
import { onMounted, computed } from 'vue'
import { useHabitsStore } from '../stores/habit'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'

const habitsStore = useHabitsStore()
const router = useRouter()

const habits = computed(() => habitsStore.activeHabits)

const loadHabits = async () => {
  try {
    await habitsStore.fetchHabits(true)
  } catch (err) {
    console.error('Ошибка загрузки:', err)
  }
}

const handleAddHabit = () => {
  router.push('/habits/new')
}

onMounted(() => {
  loadHabits()
})
</script>

<template>
  <div class="screen">
    <AppHeader title="Мои привычки" :show-back="false">
      <template #right>
        <button @click="handleAddHabit" class="add">+</button>
      </template>
    </AppHeader>

    <div class="screen-body">
      <div v-if="habitsStore.isLoading" class="loading">Загрузка...</div>

      <div v-else-if="habitsStore.error" class="error">
        <p>{{ habitsStore.error }}</p>
        <button @click="loadHabits">Повторить</button>
      </div>

      <div v-else-if="habits.length === 0" class="empty">
        <p>У вас пока нет привычек</p>
        <button @click="handleAddHabit">Создать привычку</button>
      </div>

      <div v-else class="list">
        <div
          v-for="habit in habits"
          :key="habit.id"
          class="item"
          @click="router.push(`/habits/${habit.id}`)"
        >
          <div>
            <div class="title">{{ habit.title }}</div>
            <div class="meta">
              <span v-if="habit.current_streak">🔥 {{ habit.current_streak }}</span>
              <span v-if="habit.description" class="description">{{ habit.description }}</span>
            </div>
          </div>
          <span class="chevron">›</span>
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
  max-width: 600px;
  width: 100%;
  margin: 0 auto;
  padding: var(--space-4);
  padding-bottom: calc(var(--tab-bar-height) + env(safe-area-inset-bottom) + var(--space-4));
}

.add {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-pill);
  background: var(--surface-card);
  border: none;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  font-size: 22px;
  color: var(--color-ios-blue);
}

.loading {
  text-align: center;
  padding: 40px 0;
  color: var(--text-tertiary);
}

.error {
  text-align: center;
  padding: 40px 0;
  color: var(--color-danger);
}

.error button {
  margin-top: var(--space-4);
  padding: var(--space-2) var(--space-5);
  border-radius: var(--radius-pill);
  background: var(--surface-card);
  border: none;
  color: var(--color-ios-blue);
  cursor: pointer;
  box-shadow: var(--shadow-sm);
}

.empty {
  text-align: center;
  padding: 60px 0;
}

.empty p {
  color: var(--text-tertiary);
  margin-bottom: var(--space-5);
}

.empty button {
  padding: var(--space-3) var(--space-6);
  border-radius: var(--radius-pill);
  background: var(--color-ios-blue);
  border: none;
  color: #fff;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: var(--shadow-md);
}

.list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.item {
  background: var(--surface-card);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
}

.title {
  font-size: 17px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.meta {
  display: flex;
  gap: var(--space-3);
  font-size: 14px;
  color: var(--text-tertiary);
}

.chevron {
  color: var(--color-gray-light);
  font-size: 20px;
}
</style>
