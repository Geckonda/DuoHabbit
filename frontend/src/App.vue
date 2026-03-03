<script setup>
import { ref, onMounted } from 'vue'
import { RouterView, useRouter } from 'vue-router'
import { useUserStore } from './stores/user'
import LoaderScreen from './components/LoaderScreen.vue'

const router = useRouter()
const userStore = useUserStore()
const showSplash = ref(true)

onMounted(async () => {
  console.log('🔥 Сплеш включен')
  
  const startTime = Date.now()
  const minLoadTime = 2000 // 2 секунды минимум
  
  // Проверяем авторизацию
  await userStore.checkAuth()
  
  // Считаем время
  const elapsedTime = Date.now() - startTime
  
  // Держим сплеш минимум 2 секунды
  if (elapsedTime < minLoadTime) {
    await new Promise(resolve => setTimeout(resolve, minLoadTime - elapsedTime))
  }
  
  // Выключаем сплеш
  showSplash.value = false
  console.log('✅ Сплеш выключен')
  
  // Редирект если не авторизован
  if (!userStore.isAuthenticated) {
    router.push('/login')
  }
})
</script>

<template>
  <LoaderScreen 
    v-if="showSplash" 
    :loading-progress="true"
    loading-text="Загрузка..."
  />
  <RouterView v-else />
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  width: 100%;
  overflow: hidden; /* ГЛУШИМ СКРОЛЛ НАХУЙ */
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  height: 100vh; /* вместо min-height */
  width: 100vw;
  overflow: hidden; /* и тут */
  background: #f5f5f5;
}

.container {
  padding: 16px;
  max-width: 100%;
}

@media (min-width: 768px) {
  .container {
    max-width: 600px;
    margin: 0 auto;
    padding: 24px;
  }
}
</style>