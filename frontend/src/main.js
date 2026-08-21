import { createApp } from 'vue'
import { createPinia } from 'pinia' // Импорт Pinia
import router from './router'
import App from './App.vue'
import './style.css'

const app = createApp(App)
const pinia = createPinia() // Создание экземпляра Pinia

app.use(pinia) // !!! Установка Pinia — ПЕРВЫМ делом !!!
app.use(router) // Потом уже роутер

app.mount('#app') // Монтируем в самом конце

// Регистрация сервис-воркера для push-уведомлений (без запроса разрешения -
// его спрашиваем явно в профиле, когда юзер сам включит уведомления)
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').catch(() => {})
}