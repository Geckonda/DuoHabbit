<template>
  <div class="loader-screen">
    <div class="logo-container">
      <div class="logo-wrapper">
        <img :src="logo" alt="Logo" class="logo">
      </div>
    </div>
  </div>
</template>

<script setup>
import logo from '../assets/logo.png'
</script>

<style scoped>
.loader-screen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.logo-container {
  text-align: center;
  animation: fadeIn 0.5s ease-in;
}

.logo-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.logo {
  max-width: 200px;
  height: auto;
  border-radius: 24px; /* скруглил */
  animation: pulse 2s infinite;
  filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1));
}

@keyframes fadeIn {
  from { 
    opacity: 0; 
    transform: scale(0.9); 
  }
  to { 
    opacity: 1; 
    transform: scale(1); 
  }
}

@keyframes pulse {
  0% { 
    transform: scale(1);
  }
  50% { 
    transform: scale(1.05);
    filter: drop-shadow(0 6px 8px rgba(0, 0, 0, 0.15));
  }
  100% { 
    transform: scale(1);
  }
}

@media (min-width: 768px) {
  .logo {
    max-width: 300px;
    border-radius: 32px; /* побольше скругление на десктопе */
  }
}

@media (max-width: 360px) {
  .logo {
    max-width: 150px;
    border-radius: 16px; /* поменьше на мобилках */
  }
}
</style>