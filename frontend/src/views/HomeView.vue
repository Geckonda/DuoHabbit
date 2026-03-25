<script setup>
import { onMounted, computed } from 'vue'
import { useUserStore } from '../stores/user'
import { useHabitsStore } from '../stores/habit'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
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

const handleLogout = async () => {
  await userStore.logout()
  habitsStore.$reset()
  router.push('/login')
}

onMounted(() => {
  loadHabits()
})
</script>

<template>
  <div class="home">
    <div class="header">
      <h1>Мои привычки</h1>
      <div class="actions">
        <button @click="handleAddHabit" class="add">+</button>
        <button @click="handleLogout" class="logout">Выйти</button>
      </div>
    </div>

    <div class="content">
      <div v-if="habitsStore.isLoading" class="loading">
        Загрузка...
      </div>

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
            <div v-if="habit.description" class="description">
              {{ habit.description }}
            </div>
          </div>
          <button class="menu" @click.stop>•••</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home {
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
}

.header {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #000;
}

.actions {
  display: flex;
  gap: 8px;
}

.add {
  width: 40px;
  height: 40px;
  border-radius: 20px;
  background: #fff;
  border: none;
  font-size: 24px;
  color: #007AFF;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.logout {
  padding: 8px 16px;
  border-radius: 20px;
  background: #fff;
  border: none;
  font-size: 15px;
  color: #FF3B30;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.content {
  max-width: 600px;
  margin: 0 auto;
  padding: 16px;
}

.loading {
  text-align: center;
  padding: 40px 0;
  color: #8E8E93;
}

.error {
  text-align: center;
  padding: 40px 0;
  color: #FF3B30;
}

.error button {
  margin-top: 16px;
  padding: 8px 20px;
  border-radius: 20px;
  background: #fff;
  border: none;
  color: #007AFF;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.empty {
  text-align: center;
  padding: 60px 0;
}

.empty p {
  color: #8E8E93;
  margin-bottom: 20px;
}

.empty button {
  padding: 12px 24px;
  border-radius: 24px;
  background: #007AFF;
  border: none;
  color: #fff;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,122,255,0.3);
}

.list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.item {
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.title {
  font-size: 17px;
  font-weight: 500;
  color: #000;
  margin-bottom: 4px;
}

.description {
  font-size: 14px;
  color: #8E8E93;
}

.menu {
  background: none;
  border: none;
  color: #8E8E93;
  font-size: 18px;
  padding: 8px;
  cursor: pointer;
}
</style>