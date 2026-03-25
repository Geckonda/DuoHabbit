import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { requiresGuest: true }
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/RegisterView.vue'),
    meta: { requiresGuest: true }
  },
  {
    path: '/habits/new',
    name: 'habit-create',
    component: () => import('../views/HabitCreateView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/habits/:id',
    name: 'habit-detail',
    component: () => import('../views/HabitDetailView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/habits/:id/edit',
    name: 'habit-edit',
    component: () => import('../views/HabitCreateView.vue'), // переиспользуем форму
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Флаг, что проверка авторизации еще не завершена
let authChecked = false

router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  
  // ✅ ЖДЕМ пока проверится авторизация, если еще не проверили
  if (!authChecked) {
    console.log('⏳ Ожидаем проверку авторизации...')
    await userStore.checkAuth()
    authChecked = true
    console.log('✅ Проверка завершена, auth:', userStore.isAuthenticated)
  }
  
  const isAuthenticated = userStore.isAuthenticated
  console.log('📍 Навигация:', to.path, 'auth:', isAuthenticated)

  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
  } else if (to.meta.requiresGuest && isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router