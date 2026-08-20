<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from './stores/user'
import LoaderScreen from './components/LoaderScreen.vue'
import AppShell from './components/AppShell.vue'

const userStore = useUserStore()
const showSplash = ref(true)

onMounted(async () => {
  console.log('🔥 Сплеш включен')
  
  const startTime = Date.now()
  const minLoadTime = 2000
  
  // Считаем время
  const elapsedTime = Date.now() - startTime
  
  // Держим сплеш минимум 2 секунды
  if (elapsedTime < minLoadTime) {
    await new Promise(resolve => setTimeout(resolve, minLoadTime - elapsedTime))
  }
  
  // Выключаем сплеш
  showSplash.value = false
  console.log('✅ Сплеш выключен')
})
</script>

<template>
  <!-- 👇 ГРАДИЕНТ ВЫНЕСЕН НА УРОВЕНЬ APP -->
  <div class="global-gradient-bg">
    <div class="gradient-orb orb1"></div>
    <div class="gradient-orb orb2"></div>
    <div class="gradient-orb orb3"></div>
  </div>

  <LoaderScreen 
    v-if="showSplash" 
    :loading-progress="true"
    loading-text="Загрузка..."
  />
  
  <AppShell v-else />
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
}

body {
  font-family: var(--font-family);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  height: 100vh;
  width: 100vw;
  position: relative; /* 👈 важно для z-index */
}

/* 👇 ГРАДИЕНТНЫЙ ФОН (СКОПИРОВАН ИЗ Login.vue) */
.global-gradient-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(145deg, #8B5CF6 0%, #EC4899 50%, #3B82F6 100%);
  z-index: -2;
  overflow: hidden;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
  animation: float 20s infinite ease-in-out;
  pointer-events: none;
}

.orb1 {
  width: 80%;
  height: 80%;
  max-width: 800px;
  max-height: 800px;
  background: #8B5CF6;
  top: -20%;
  right: -20%;
  animation-delay: 0s;
}

.orb2 {
  width: 90%;
  height: 90%;
  max-width: 900px;
  max-height: 900px;
  background: #EC4899;
  bottom: -30%;
  left: -30%;
  animation-delay: -5s;
}

.orb3 {
  width: 70%;
  height: 70%;
  max-width: 700px;
  max-height: 700px;
  background: #3B82F6;
  top: 40%;
  left: 40%;
  transform: translate(-40%, -40%);
  animation-delay: -10s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(5%, -5%) scale(1.1); }
  66% { transform: translate(-5%, 5%) scale(0.9); }
}

/* Анимация переходов */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
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