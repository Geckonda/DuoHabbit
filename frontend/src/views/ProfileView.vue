<!-- views/ProfileView.vue -->
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useHabitsStore } from '../stores/habit'
import { useGroupsStore } from '../stores/group'
import AppHeader from '../components/AppHeader.vue'
import GlassCard from '../components/GlassCard.vue'
import PillButton from '../components/PillButton.vue'

const router = useRouter()
const userStore = useUserStore()
const habitsStore = useHabitsStore()
const groupsStore = useGroupsStore()

const formData = ref({ username: '', timezone: '' })
const isSaving = ref(false)
const error = ref('')
const savedHint = ref('')

const initials = computed(() => (userStore.user?.username || '?').slice(0, 1).toUpperCase())
const detectedTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone

const syncForm = () => {
  formData.value = {
    username: userStore.user?.username || '',
    timezone: userStore.user?.timezone || detectedTimezone
  }
}

const detectTimezone = () => {
  formData.value.timezone = detectedTimezone
}

const handleSave = async () => {
  if (!formData.value.username.trim()) {
    error.value = 'Имя пользователя не может быть пустым'
    return
  }

  isSaving.value = true
  error.value = ''
  savedHint.value = ''

  try {
    await userStore.updateProfile(formData.value)
    savedHint.value = 'Сохранено'
    setTimeout(() => { savedHint.value = '' }, 2000)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Не удалось сохранить профиль'
  } finally {
    isSaving.value = false
  }
}

const handleLogout = async () => {
  await userStore.logout()
  habitsStore.$reset()
  groupsStore.$reset()
  router.push('/login')
}

onMounted(syncForm)
</script>

<template>
  <div class="screen">
    <AppHeader title="Профиль" :show-back="false" />

    <div class="screen-body">
      <div class="profile-header">
        <div class="avatar">{{ initials }}</div>
        <div class="profile-name">{{ userStore.user?.username }}</div>
        <div class="profile-email">{{ userStore.user?.email }}</div>
      </div>

      <GlassCard title="Аккаунт" icon="⚙️">
        <div class="input-group">
          <label class="input-label">Имя пользователя</label>
          <input
            v-model="formData.username"
            type="text"
            maxlength="100"
            :disabled="isSaving"
            class="text-input"
          >
        </div>

        <div class="input-group">
          <label class="input-label">
            Часовой пояс
            <span class="optional">— по нему считается "сегодня" для стриков</span>
          </label>
          <div class="timezone-row">
            <input
              v-model="formData.timezone"
              type="text"
              placeholder="Europe/Moscow"
              :disabled="isSaving"
              class="text-input"
            >
            <button
              type="button"
              class="detect-btn"
              :disabled="isSaving"
              @click="detectTimezone"
              title="Определить по браузеру"
            >📍</button>
          </div>
          <span class="hint-text">Сейчас определяется браузером как {{ detectedTimezone }}</span>
        </div>

        <p v-if="error" class="error-message">{{ error }}</p>
        <p v-if="savedHint" class="saved-hint">✓ {{ savedHint }}</p>

        <PillButton :loading="isSaving" @click="handleSave">Сохранить</PillButton>
      </GlassCard>

      <PillButton variant="ghost" class="logout-btn" @click="handleLogout">
        Выйти из аккаунта
      </PillButton>
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

.profile-header {
  text-align: center;
  margin-bottom: var(--space-6);
}

.avatar {
  width: 72px;
  height: 72px;
  margin: 0 auto var(--space-3);
  border-radius: var(--radius-pill);
  background: linear-gradient(135deg, var(--color-accent) 0%, var(--color-accent-2) 100%);
  color: var(--text-on-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 700;
  box-shadow: var(--shadow-md);
}

.profile-name {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.profile-email {
  font-size: 14px;
  color: var(--text-tertiary);
  margin-top: 2px;
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
  font-size: 12px;
}

.text-input {
  width: 100%;
  padding: var(--space-4);
  background: var(--surface-overlay);
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

.text-input:disabled {
  opacity: 0.6;
}

.timezone-row {
  display: flex;
  gap: var(--space-2);
}

.timezone-row .text-input {
  flex: 1;
}

.detect-btn {
  width: 48px;
  flex-shrink: 0;
  border: none;
  border-radius: var(--radius-md);
  background: var(--surface-overlay);
  font-size: 18px;
  cursor: pointer;
}

.hint-text {
  display: block;
  margin-top: var(--space-2);
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

.saved-hint {
  color: #248A3D;
  background: rgba(52, 199, 89, 0.12);
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-3);
  font-size: 13px;
  margin-bottom: var(--space-4);
  text-align: center;
}

.logout-btn {
  margin-top: var(--space-5);
}
</style>
