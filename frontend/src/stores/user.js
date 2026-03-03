import { defineStore } from 'pinia'
import { ref } from 'vue'
import { auth } from '../api/auth'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const isAuthenticated = ref(false)

  const checkAuth = async () => {
    console.log('🔍 Проверка авторизации...')
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        console.log('❌ Нет токена')
        isAuthenticated.value = false
        return
      }
      
      const response = await auth.getMe()
      user.value = response.data
      isAuthenticated.value = true
      console.log('✅ Авторизован:', response.data.email)
    } catch (error) {
      console.error('❌ Ошибка авторизации:', error)
      localStorage.removeItem('access_token')
      isAuthenticated.value = false
      user.value = null
    }
  }

  const login = async (email, password) => {
    try {
      const response = await auth.login(email, password)
      if (response.access_token) {
        localStorage.setItem('access_token', response.access_token)
        await checkAuth() // перепроверяем и получаем юзера
        return true
      }
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }

  const logout = async () => {
    try {
      await auth.logout()
    } finally {
      user.value = null
      isAuthenticated.value = false
      localStorage.removeItem('access_token')
    }
  }

  return {
    user,
    isAuthenticated,
    checkAuth,
    login,
    logout
  }
})