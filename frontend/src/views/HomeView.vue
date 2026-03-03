<script setup>
import { useUserStore } from '../stores/user'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()

const handleLogout = async () => {
  await userStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="home">
    <div class="header">
      <h1>Главная</h1>
      <button @click="handleLogout" class="logout-btn">Выйти</button>
    </div>
    
    <div class="content">
      <p>Привет, {{ userStore.user?.email || 'пользователь' }}!</p>
      <p>Ты авторизован и видишь этот контент</p>
    </div>
  </div>
</template>

<style scoped>
.home {
  min-height: 100vh;
  background: #f5f5f5;
}

.header {
  background: white;
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.header h1 {
  font-size: 20px;
  color: #333;
}

.logout-btn {
  padding: 8px 16px;
  background: #ff4d4d;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.content {
  padding: 20px 16px;
  max-width: 600px;
  margin: 0 auto;
}

.content p {
  background: white;
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 12px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
</style>