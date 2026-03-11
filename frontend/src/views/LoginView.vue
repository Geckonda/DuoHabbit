<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import logo from '../assets/logo.png'

const router = useRouter()
const userStore = useUserStore()
const email = ref('')
const password = ref('')
const error = ref('')
const isLoading = ref(false)

const handleSubmit = async () => {
  if (!email.value || !password.value) {
    error.value = 'Заполните все поля'
    return
  }
  
  isLoading.value = true
  error.value = ''
  
  try {
    await userStore.login(email.value, password.value)
    router.push('/')
  } catch (err) {
    error.value = 'Неверный email или пароль'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="login-screen">
    
    <div class="login-container">
      <!-- Лого с глянцевым эффектом -->
      <div class="logo-wrapper">
        <div class="logo-glass">
          <img :src="logo" alt="Logo" class="logo">
        </div>
        <h1 class="app-name">DuoHabit</h1>
        <p class="app-subtitle">Добро пожаловать</p>
      </div>

      <!-- Форма с глянцевым стеклом -->
      <form @submit.prevent="handleSubmit" class="login-form">
        <div class="input-group">
          <div class="input-icon">📧</div>
          <input 
            v-model="email" 
            type="email" 
            placeholder="Email"
            required
            :disabled="isLoading"
          >
        </div>
        
        <div class="input-group">
          <div class="input-icon">🔒</div>
          <input 
            v-model="password" 
            type="password" 
            placeholder="Пароль"
            required
            :disabled="isLoading"
          >
        </div>

        <div class="forgot-password">
          <a href="#" class="forgot-link">Забыли пароль?</a>
        </div>

        <p v-if="error" class="error-message">
          <span class="error-icon">⚠️</span>
          {{ error }}
        </p>

        <button 
          type="submit" 
          class="login-button"
          :disabled="isLoading"
        >
          <span v-if="!isLoading">Войти</span>
          <span v-else class="button-loader"></span>
        </button>

        <div class="signup-prompt">
        <span class="prompt-text">Нет аккаунта?</span>
          <router-link to="/register" class="signup-link">Зарегистрироваться</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  overflow: hidden; /* убить скролл на корню */
  height: 100%;
  width: 100%;
  position: fixed; /* для мобилок особенно */
}

.login-screen {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  position: relative;
  overflow: hidden;
  box-sizing: border-box;
  margin: 0;
  width: 100%;
}

/* Основной контейнер - жидкое стекло */
.login-container {
  width: 100%;
  max-width: 400px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 32px;
  padding: 32px 24px;
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.1),
    inset 0 1px 1px rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.4);
  animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative;
  z-index: 1;
}

/* Лого с глянцем */
.logo-wrapper {
  text-align: center;
  margin-bottom: 32px;
}

.logo-glass {
  width: 100px;
  height: 100px;
  margin: 0 auto 16px;
  background: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 
    0 8px 20px rgba(0, 0, 0, 0.1),
    inset 0 2px 2px rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.4);
}

.logo {
  width: 80px;
  height: 80px;
  border-radius: 24px;
  object-fit: cover;
}

.app-name {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 4px;
  background: linear-gradient(135deg, #1a1a1a 0%, #4a4a4a 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.5px;
}

.app-subtitle {
  font-size: 15px;
  color: rgba(0, 0, 0, 0.5);
  font-weight: 400;
  margin: 0;
}

/* Группа инпутов */
.input-group {
  position: relative;
  margin-bottom: 16px;
}

.input-icon {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 20px;
  opacity: 0.6;
  z-index: 1;
}

.input-group input {
  width: 100%;
  padding: 18px 18px 18px 52px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1.5px solid rgba(255, 255, 255, 0.8);
  border-radius: 20px;
  font-size: 16px;
  font-weight: 500;
  color: #1a1a1a;
  transition: all 0.3s ease;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.02);
}

.input-group input:focus {
  outline: none;
  border-color: white;
  background: white;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
  transform: scale(1.02);
}

.input-group input::placeholder {
  color: rgba(0, 0, 0, 0.4);
  font-weight: 400;
}

.input-group input:disabled {
  opacity: 0.6;
  background: rgba(255, 255, 255, 0.5);
}

/* Забыли пароль */
.forgot-password {
  text-align: right;
  margin: -8px 0 20px;
}

.forgot-link {
  color: rgba(0, 0, 0, 0.6);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: color 0.3s;
  padding: 8px 0;
  display: inline-block;
}

.forgot-link:active {
  color: #000;
}

/* Ошибка */
.error-message {
  background: rgba(255, 59, 48, 0.1);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 59, 48, 0.3);
  border-radius: 16px;
  padding: 12px 16px;
  margin-bottom: 20px;
  color: #ff3b30;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  animation: shake 0.5s ease-in-out;
}

.error-icon {
  font-size: 18px;
}

/* Кнопка входа */
.login-button {
  width: 100%;
  padding: 18px;
  background: linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%);
  border: none;
  border-radius: 24px;
  font-size: 18px;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 10px 20px rgba(139, 92, 246, 0.3);
  margin-bottom: 20px;
  position: relative;
  overflow: hidden;
}

.login-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s;
}

.login-button:active::before {
  left: 100%;
}

.login-button:active {
  transform: scale(0.98);
  box-shadow: 0 5px 15px rgba(139, 92, 246, 0.4);
}

.login-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.button-loader {
  display: inline-block;
  width: 24px;
  height: 24px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s linear infinite;
}

/* Регистрация */
.signup-prompt {
  text-align: center;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.4);
}

.prompt-text {
  color: rgba(0, 0, 0, 0.5);
  font-size: 15px;
  margin-right: 8px;
}

.signup-link {
  color: #8B5CF6;
  text-decoration: none;
  font-weight: 600;
  font-size: 15px;
  transition: all 0.3s;
  padding: 8px 0;
  display: inline-block;
}

.signup-link:active {
  opacity: 0.7;
  transform: translateX(2px);
}

/* Анимации */
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

/* Mobile first адаптация */
@media (max-width: 380px) {
  .login-container {
    padding: 24px 16px;
  }
  
  .logo-glass {
    width: 80px;
    height: 80px;
  }
  
  .logo {
    width: 64px;
    height: 64px;
  }
  
  .app-name {
    font-size: 28px;
  }
  
  .input-group input {
    padding: 16px 16px 16px 48px;
  }
}

/* Убиваем автозаполнение нахуй */
.input-group input:-webkit-autofill,
.input-group input:-webkit-autofill:hover,
.input-group input:-webkit-autofill:focus,
.input-group input:-webkit-autofill:active {
  -webkit-box-shadow: 0 0 0 30px rgba(255, 255, 255, 0.9) inset !important;
  box-shadow: 0 0 0 30px rgba(255, 255, 255, 0.9) inset !important;
  -webkit-text-fill-color: #1a1a1a !important;
  background-clip: text !important;
  background: transparent !important;
  border-color: rgba(255, 255, 255, 0.8) !important;
}

/* Для Firefox */
.input-group input:autofill {
  background: rgba(255, 255, 255, 0.9) !important;
  color: #1a1a1a !important;
}

</style>