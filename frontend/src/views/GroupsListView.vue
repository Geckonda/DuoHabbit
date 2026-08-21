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
    // force=true: 5-минутный кэш иначе прячет свежее членство (тебя одобрили,
    // а список групп ещё "помнит" старое состояние) при каждом заходе на вкладку
    await groupsStore.fetchGroups(true, true)
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

const handleOpenInvites = () => {
  router.push('/groups/invites')
}

onMounted(() => {
  loadGroups()
  groupsStore.fetchMyInvites().catch(() => {})
  groupsStore.fetchMyRequests().catch(() => {})
})
</script>

<template>
  <div class="screen">
    <AppHeader title="Мои группы" :show-back="false">
      <template #right>
        <button @click="handleOpenInvites" class="invites" title="Приглашения">
          🔔
          <span v-if="groupsStore.pendingCount > 0" class="invites-badge">
            {{ groupsStore.pendingCount > 9 ? '9+' : groupsStore.pendingCount }}
          </span>
        </button>
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
              <span>👥 {{ group.member_count }}</span>
              <span v-if="group.habits?.length">📋 {{ group.habits.length }}</span>
              <span v-if="group.habits?.length">
                🔥 {{ Math.min(...group.habits.map(h => h.current_streak)) }}
              </span>
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

.invites,
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

.invites {
  position: relative;
  font-size: 16px;
}

.invites-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 15px;
  height: 15px;
  padding: 0 3px;
  border-radius: var(--radius-pill);
  background: var(--color-danger);
  color: var(--text-on-accent);
  font-size: 10px;
  font-weight: 700;
  line-height: 15px;
  text-align: center;
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
