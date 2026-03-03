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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Гвард с учетом лоадера
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  
  // Ждем пока проверится авторизация
  if (userStore.isLoading) {
    await new Promise(resolve => {
      const unwatch = userStore.$watch('isLoading', (val) => {
        if (!val) {
          unwatch()
          resolve()
        }
      })
    })
  }

  if (to.meta.requiresAuth && !userStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.requiresGuest && userStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router