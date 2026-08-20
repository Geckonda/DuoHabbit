<!-- views/HomeView.vue -->
<script setup>
import { onMounted, computed } from 'vue'
import { useUserStore } from '../stores/user'
import { useHabitsStore } from '../stores/habit'
import { useGroupsStore } from '../stores/group'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'

const userStore = useUserStore()
const habitsStore = useHabitsStore()
const groupsStore = useGroupsStore()
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

const handleOpenChats = () => {
  router.push('/chats')
}

const handleLogout = async () => {
  await userStore.logout()
  habitsStore.$reset()
  groupsStore.$reset()
  router.push('/login')
}

onMounted(() => {
  loadHabits()

  // Диалоги нужны здесь только ради счетчика непрочитанных,
  // сокет держит его свежим без перезагрузки страницы
  chatStore.fetchConversations().catch(() => {})
  chatStore.connectSocket()
})
</script>

<template>
  <div class="screen">
    <AppHeader title="Мои привычки" :show-back="false">
      <template #right>
        <button @click="handleAddHabit" class="add">+</button>
        <button @click="handleLogout" class="logout">Выйти</button>
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
            <div v-if="habit.description" class="description">{{ habit.description }}</div>
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

.add,
.logout {
  border: none;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
}

.chats {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 20px;
  background: #fff;
  border: none;
  font-size: 18px;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.chats .badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  background: #FF3B30;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.add {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-pill);
  background: var(--surface-card);
  font-size: 22px;
  color: var(--color-ios-blue);
}

.logout {
  padding: 0 var(--space-4);
  height: 36px;
  border-radius: var(--radius-pill);
  background: var(--surface-card);
  font-size: 14px;
  color: var(--color-danger);
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

.description {
  font-size: 14px;
  color: var(--text-tertiary);
}

.chevron {
  color: var(--color-gray-light);
  font-size: 20px;
}
</style>
