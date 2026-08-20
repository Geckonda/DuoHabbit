<!-- views/GroupsListView.vue -->
<script setup>
import { onMounted, computed } from 'vue'
import { useGroupsStore } from '../stores/group'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'

const groupsStore = useGroupsStore()
const router = useRouter()

const groupsList = computed(() => groupsStore.groupsList)

const loadGroups = async () => {
  try {
    await groupsStore.fetchGroups(true)
  } catch (err) {
    console.error('Ошибка загрузки групп:', err)
  }
}

const handleCreateGroup = () => {
  router.push('/groups/new')
}

const handleJoinGroup = () => {
  router.push('/groups/join')
}

onMounted(() => {
  loadGroups()
})
</script>

<template>
  <div class="screen">
    <AppHeader title="Мои группы" :show-back="false">
      <template #right>
        <button @click="handleJoinGroup" class="join" title="Присоединиться по коду">🔗</button>
        <button @click="handleCreateGroup" class="add">+</button>
      </template>
    </AppHeader>

    <div class="screen-body">
      <div v-if="groupsStore.isLoading" class="loading">Загрузка...</div>

      <div v-else-if="groupsStore.error" class="error">
        <p>{{ groupsStore.error }}</p>
        <button @click="loadGroups">Повторить</button>
      </div>

      <div v-else-if="groupsList.length === 0" class="empty">
        <p>У вас пока нет групп</p>
        <button @click="handleCreateGroup">Создать группу</button>
      </div>

      <div v-else class="list">
        <div
          v-for="group in groupsList"
          :key="group.id"
          class="item"
          @click="router.push(`/groups/${group.id}`)"
        >
          <div>
            <div class="title">{{ group.name }}</div>
            <div class="meta">
              <span v-if="group.habit">🔥 {{ group.habit.current_streak || 0 }}</span>
              <span v-if="group.member_count">👥 {{ group.member_count }}</span>
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

.join,
.add {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-pill);
  background: var(--surface-card);
  border: none;
  color: var(--color-ios-blue);
  cursor: pointer;
  box-shadow: var(--shadow-sm);
}

.join {
  font-size: 16px;
}

.add {
  font-size: 22px;
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
