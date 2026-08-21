<!-- views/GroupInvitesView.vue -->
<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGroupsStore } from '../stores/group'
import AppHeader from '../components/AppHeader.vue'
import GlassCard from '../components/GlassCard.vue'
import PillButton from '../components/PillButton.vue'

const router = useRouter()
const groupsStore = useGroupsStore()

const isLoading = ref(true)
const error = ref('')
const respondingId = ref(null) // id инвайта/заявки, с которым сейчас работаем

const load = async () => {
  isLoading.value = true
  error.value = ''
  try {
    await Promise.all([groupsStore.fetchMyInvites(), groupsStore.fetchMyRequests()])
  } catch (err) {
    error.value = 'Не удалось загрузить приглашения'
  } finally {
    isLoading.value = false
  }
}

// Общая форма всех четырех действий: занять respondingId, дернуть store-экшен,
// при успехе опционально уйти в группу, при ошибке показать конкретный текст
const respond = async (item, { action, errorMessage, navigate = false }) => {
  respondingId.value = item.id
  try {
    await action()
    if (navigate) router.push(`/groups/${item.group_id}`)
  } catch (err) {
    error.value = err.response?.data?.detail || errorMessage
  } finally {
    respondingId.value = null
  }
}

const handleAccept = (invite) => respond(invite, {
  action: () => groupsStore.acceptInvite(invite.group_id),
  errorMessage: 'Не удалось принять приглашение',
  navigate: true,
})

const handleDecline = (invite) => respond(invite, {
  action: () => groupsStore.declineInvite(invite.group_id),
  errorMessage: 'Не удалось отклонить приглашение',
})

const handleApprove = (request) => respond(request, {
  action: () => groupsStore.approveRequest(request.group_id, request.user_id),
  errorMessage: 'Не удалось одобрить заявку',
  navigate: true,
})

const handleReject = (request) => respond(request, {
  action: () => groupsStore.rejectRequest(request.group_id, request.user_id),
  errorMessage: 'Не удалось отклонить заявку',
})

onMounted(load)
</script>

<template>
  <div class="screen">
    <AppHeader title="Приглашения" fallback="/groups" />

    <div class="screen-body">
      <p v-if="error" class="error-message">{{ error }}</p>

      <div v-if="isLoading" class="loading">Загрузка...</div>

      <template v-else>
        <GlassCard title="Приглашения в группы" icon="✉️">
          <p v-if="groupsStore.myInvites.length === 0" class="empty-hint">
            Пока никто не приглашал тебя в группу
          </p>
          <div v-else class="pending-list">
            <div v-for="invite in groupsStore.myInvites" :key="invite.id" class="pending-item">
              <div class="pending-name">{{ invite.group_name }}</div>
              <div class="pending-actions">
                <PillButton
                  variant="secondary"
                  :disabled="respondingId === invite.id"
                  @click="handleDecline(invite)"
                >Отклонить</PillButton>
                <PillButton
                  :loading="respondingId === invite.id"
                  @click="handleAccept(invite)"
                >Принять</PillButton>
              </div>
            </div>
          </div>
        </GlassCard>

        <GlassCard v-if="groupsStore.myRequests.length > 0" title="Заявки на вступление" icon="🙋">
          <div class="pending-list">
            <div v-for="request in groupsStore.myRequests" :key="request.id" class="pending-item">
              <div class="pending-name">
                {{ request.username }}
                <span class="pending-sub">→ {{ request.group_name }}</span>
              </div>
              <div class="pending-actions">
                <PillButton
                  variant="secondary"
                  :disabled="respondingId === request.id"
                  @click="handleReject(request)"
                >Отклонить</PillButton>
                <PillButton
                  :loading="respondingId === request.id"
                  @click="handleApprove(request)"
                >Одобрить</PillButton>
              </div>
            </div>
          </div>
        </GlassCard>
      </template>
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
  padding-bottom: calc(var(--tab-bar-height) + env(safe-area-inset-bottom) + var(--space-4));
}

.loading {
  text-align: center;
  color: var(--text-tertiary);
  padding: var(--space-6) 0;
}

.empty-hint {
  color: var(--text-tertiary);
  font-size: 14px;
}

.pending-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.pending-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.pending-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.pending-sub {
  font-weight: 400;
  color: var(--text-tertiary);
  font-size: 13px;
}

.pending-actions {
  display: flex;
  gap: var(--space-2);
  flex-shrink: 0;
}

.pending-actions .pill-btn {
  width: auto;
  padding: var(--space-2) var(--space-4);
  font-size: 14px;
}

.error-message {
  background: rgba(255, 59, 48, 0.1);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
  margin-bottom: var(--space-4);
  color: var(--color-danger);
  font-size: 14px;
}
</style>
