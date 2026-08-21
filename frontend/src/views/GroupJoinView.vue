<!-- views/GroupJoinView.vue -->
<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGroupsStore } from '../stores/group'
import AppHeader from '../components/AppHeader.vue'
import PillButton from '../components/PillButton.vue'

const route = useRoute()
const router = useRouter()
const groupsStore = useGroupsStore()

const inviteCode = ref('')
const isLoading = ref(false)
const error = ref('')
const isSent = ref(false)

onMounted(() => {
  if (route.query.code) {
    inviteCode.value = String(route.query.code)
  }
})

const handleSubmit = async () => {
  if (!inviteCode.value.trim()) {
    error.value = 'Введите код приглашения'
    return
  }

  isLoading.value = true
  error.value = ''

  try {
    // Членство только после того, как владелец одобрит заявку - группа пока не открывается
    await groupsStore.joinGroup(inviteCode.value.trim())
    isSent.value = true
  } catch (err) {
    error.value = err.response?.data?.detail || 'Не удалось отправить заявку. Проверьте код.'
    console.error(err)
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="screen">
    <AppHeader title="Присоединиться" fallback="/groups" />

    <div class="screen-body">
      <template v-if="isSent">
        <div class="join-icon">✅</div>
        <p class="join-hint">
          Заявка отправлена! Как только владелец группы её одобрит, группа появится у тебя в списке.
        </p>
        <PillButton @click="router.push('/groups')">Готово</PillButton>
      </template>

      <template v-else>
        <div class="join-icon">🔗</div>
        <p class="join-hint">Введите код приглашения от владельца группы</p>

        <form @submit.prevent="handleSubmit" class="join-form">
          <input
            v-model="inviteCode"
            type="text"
            placeholder="Например: a1b2c3d4"
            :disabled="isLoading"
            class="text-input code-input"
            autocapitalize="off"
            autocorrect="off"
          >

          <p v-if="error" class="error-message">{{ error }}</p>

          <PillButton type="submit" :loading="isLoading">Отправить заявку</PillButton>
        </form>
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
  padding: var(--space-6) var(--space-4);
  max-width: 420px;
  width: 100%;
  margin: 0 auto;
  text-align: center;
}

.join-icon {
  font-size: 48px;
  margin-bottom: var(--space-2);
}

.join-hint {
  color: var(--text-secondary);
  font-size: 15px;
  margin-bottom: var(--space-6);
  line-height: 1.4;
}

.join-form {
  text-align: left;
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
  margin-bottom: var(--space-5);
  transition: border-color 0.2s;
}

.text-input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.code-input {
  text-align: center;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 2px;
}

.error-message {
  background: rgba(255, 59, 48, 0.1);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
  margin-bottom: var(--space-4);
  color: var(--color-danger);
  font-size: 14px;
  text-align: left;
}
</style>
