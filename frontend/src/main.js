import { createApp } from 'vue'
import { createPinia } from 'pinia' // Импорт Pinia
import router from './router'
import App from './App.vue'
import './style.css'
import { useNotificationsStore } from './stores/notifications'

const app = createApp(App)
const pinia = createPinia() // Создание экземпляра Pinia

app.use(pinia) // !!! Установка Pinia — ПЕРВЫМ делом !!!
app.use(router) // Потом уже роутер

app.mount('#app') // Монтируем в самом конце

// Регистрация сервис-воркера для push-уведомлений (без запроса разрешения -
// его спрашиваем явно в профиле, когда юзер сам включит уведомления). Через
// стор, а не напрямую - там же лежит путь к sw.js, который используют
// syncStatus()/enable(), незачем дублировать регистрацию
const notificationsStore = useNotificationsStore()
if (notificationsStore.isSupported) {
  notificationsStore.registerServiceWorker().catch(() => {})
}