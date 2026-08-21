// stores/notifications.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { notifications } from '../api/notifications'

// Баннер с предложением включить уведомления показываем один раз за все время
// (при первом открытом чате), а не при каждом заходе - флаг переживает логаут/логин,
// он про браузер, а не про юзера
const PROMPTED_KEY = 'duohabit_push_prompted'

// Boilerplate-конвертер: applicationServerKey ждет Uint8Array, а сервер отдает
// VAPID-ключ строкой (urlsafe-base64)
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const rawData = atob(base64)
  return Uint8Array.from([...rawData].map((char) => char.charCodeAt(0)))
}

export const useNotificationsStore = defineStore('notifications', () => {
  const isSupported = 'serviceWorker' in navigator && 'PushManager' in window
  const permission = ref(isSupported ? Notification.permission : 'unsupported')
  const isSubscribed = ref(false)
  const error = ref(null)
  const hasPrompted = ref(localStorage.getItem(PROMPTED_KEY) === '1')

  // Показывать баннер только пока юзер еще не решил (permission все еще 'default') -
  // если он уже сам включил в профиле или заблокировал в браузере, баннер лишний
  const shouldPrompt = computed(
    () => isSupported && permission.value === 'default' && !isSubscribed.value && !hasPrompted.value
  )

  const markPrompted = () => {
    hasPrompted.value = true
    localStorage.setItem(PROMPTED_KEY, '1')
  }

  const registerServiceWorker = () => navigator.serviceWorker.register('/sw.js')

  // Проверить, есть ли уже активная подписка (например с прошлого визита)
  const syncStatus = async () => {
    if (!isSupported) return

    try {
      const registration = await registerServiceWorker()
      const subscription = await registration.pushManager.getSubscription()
      isSubscribed.value = subscription !== null
      permission.value = Notification.permission
    } catch (err) {
      // Не критично - просто останется "не подписан", тумблер предложит включить снова
      console.error('Не удалось проверить статус push-подписки:', err)
    }
  }

  const enable = async () => {
    if (!isSupported) {
      error.value = 'Браузер не поддерживает push-уведомления'
      return
    }

    error.value = null

    try {
      // Проверяем ДО requestPermission: если сервер не настроен, спрашивать
      // разрешение у юзера незачем - а провалившись после granted, банер
      // сам больше никогда не покажется (permission уже не 'default')
      const { data } = await notifications.getVapidPublicKey()
      if (!data.public_key) {
        error.value = 'Push пока не настроен на сервере'
        return
      }

      const result = await Notification.requestPermission()
      permission.value = result
      if (result !== 'granted') return

      const registration = await registerServiceWorker()

      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(data.public_key),
      })

      await notifications.subscribe(subscription.toJSON())
      isSubscribed.value = true
    } catch (err) {
      error.value = 'Не удалось включить уведомления'
      console.error('Push subscribe failed:', err)
    }
  }

  const disable = async () => {
    try {
      const registration = await navigator.serviceWorker.ready
      const subscription = await registration.pushManager.getSubscription()

      if (subscription) {
        await notifications.unsubscribe(subscription.endpoint)
        await subscription.unsubscribe()
      }
    } catch (err) {
      console.error('Push unsubscribe failed:', err)
    } finally {
      isSubscribed.value = false
    }
  }

  // Подписка на устройство не привязана к сессии - при логауте её не рвем,
  // следующий enable() на этом же браузере просто переприсвоит ее новому юзеру
  const $reset = () => {
    error.value = null
  }

  return {
    isSupported,
    permission,
    isSubscribed,
    error,
    shouldPrompt,
    markPrompted,
    registerServiceWorker,
    syncStatus,
    enable,
    disable,
    $reset,
  }
})
