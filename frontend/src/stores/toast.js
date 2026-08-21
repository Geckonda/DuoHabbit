// stores/toast.js
// Внутриприложенческие уведомления - когда приложение открыто, но юзер не там,
// куда пришло событие. Внешний Web Push (stores/notifications.js) - для случая,
// когда приложения нет на экране вообще.
import { defineStore } from 'pinia'
import { ref } from 'vue'

const AUTO_DISMISS_MS = 4000

export const useToastStore = defineStore('toast', () => {
  const current = ref(null) // { title, body, url } | null
  let dismissTimer = null

  const dismiss = () => {
    clearTimeout(dismissTimer)
    current.value = null
  }

  // Один тост на экране - новый заменяет предыдущий, этого достаточно для чата
  const show = ({ title, body, url }) => {
    clearTimeout(dismissTimer)
    current.value = { title, body, url }
    dismissTimer = setTimeout(dismiss, AUTO_DISMISS_MS)
  }

  return { current, show, dismiss }
})
