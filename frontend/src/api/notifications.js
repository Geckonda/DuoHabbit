// api/notifications.js
import api from './index'

export const notifications = {
  // Публичный VAPID-ключ сервера, нужен браузеру для pushManager.subscribe
  getVapidPublicKey: () => api.get('/push/vapid-public-key'),

  // subscription - результат PushSubscription.toJSON() из Push API браузера
  subscribe: (subscription) => api.post('/push/subscribe', subscription),

  unsubscribe: (endpoint) => api.post('/push/unsubscribe', { endpoint }),
}
