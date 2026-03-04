import { defineStore } from 'pinia'
import { ref } from 'vue'
import { auth } from '../api/auth'

export const useUserStore = defineStore('user', () => {
  const user = ref(null) // будет UserRead или null
  const isAuthenticated = ref(false)
  const isLoading = ref(true)

  const checkAuth = async () => {
    isLoading.value = true
    const token = localStorage.getItem('access_token')
    
    if (!token) {
      isAuthenticated.value = false
      user.value = null
      isLoading.value = false
      return
    }
    
    try {
      const response = await auth.getMe()
      user.value = response.data
      isAuthenticated.value = true
    } catch (error) {
      console.error('Auth check failed:', error)
      localStorage.removeItem('access_token')
      isAuthenticated.value = false
      user.value = null
    } finally {
      isLoading.value = false
    }
  }

  const login = async (email, password) => {
    try {
      const data = await auth.login(email, password)
      
      if (data.access_token) {
        localStorage.setItem('access_token', data.access_token)
        await checkAuth() // перезагружаем юзера
        return true
      }
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }

  const register = async (userData) => {
    try {
      // userData должен содержать: email, username, password
      const data = await auth.register(userData)
      
      // После регистрации обычно автоматически логинят
      if (data.access_token) {
        localStorage.setItem('access_token', data.access_token)
        await checkAuth()
        return true
      } else {
        // Или если регистрация без авто-логина
        await login(userData.email, userData.password)
      }
    } catch (error) {
      console.error('Registration failed:', error)
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
    isLoading,
    checkAuth,
    login,
    register,
    logout
  }
})