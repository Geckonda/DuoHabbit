<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import logo from '../assets/logo.png'

const router = useRouter()
const userStore = useUserStore()

const formData = ref({
  email: '',
  username: '',
  password: '',
  confirmPassword: ''
})

const error = ref('')
const isLoading = ref(false)

const handleSubmit = async () => {
  // Валидация
  if (!formData.value.email || !formData.value.username || !formData.value.password || !formData.value.confirmPassword) {
    error.value = 'Заполните все поля'
    return
  }
  
  if (formData.value.password !== formData.value.confirmPassword) {
    error.value = 'Пароли не совпадают'
    return
  }
  
  if (formData.value.password.length < 6) {
    error.value = 'Пароль должен быть не менее 6 символов'
    return
  }
  
  isLoading.value = true
  error.value = ''
  
  try {
    // Отправляем только нужные поля (без confirmPassword)
    await userStore.register({
      email: formData.value.email,
      username: formData.value.username,
      password: formData.value.password
    })
    router.push('/')
  } catch (err) {
    if (err.response?.status === 400) {
      error.value = 'Email уже используется или некорректные данные'
    } else {
      error.value = 'Ошибка регистрации'
    }
    console.error(err)
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="register-screen">
    
    <div class="register-container">
      <!-- Лого -->
      <div class="logo-wrapper">
        <div class="logo-glass">
          <img :src="logo" alt="Logo" class="logo">
        </div>
        <h1 class="app-name">DuoHabit</h1>
        <p class="app-subtitle">Создайте аккаунт</p>
      </div>

      <!-- Форма регистрации -->
      <form @submit.prevent="handleSubmit" class="register-form">
        <div class="input-group">
          <div class="input-icon">📧</div>
          <input 
            v-model="formData.email" 
            type="email" 
            placeholder="Email"
            required
            :disabled="isLoading"
          >
        </div>
        
        <div class="input-group">
          <div class="input-icon">👤</div>
          <input 
            v-model="formData.username" 
            type="text" 
            placeholder="Имя пользователя"
            required
            :disabled="isLoading"
          >
        </div>
        
        <div class="input-group">
          <div class="input-icon">🔒</div>
          <input 
            v-model="formData.password" 
            type="password" 
            placeholder="Пароль"
            required
            :disabled="isLoading"
          >
        </div>
        
        <div class="input-group">
          <div class="input-icon">✓</div>
          <input 
            v-model="formData.confirmPassword" 
            type="password" 
            placeholder="Подтвердите пароль"
            required
            :disabled="isLoading"
          >
        </div>

        <!-- Условия использования -->
        <div class="terms">
          <input type="checkbox" id="terms" required>
          <label for="terms">
            Я принимаю <a href="#" class="terms-link">условия использования</a> и 
            <a href="#" class="terms-link">политику конфиденциальности</a>
          </label>
        </div>

        <p v-if="error" class="error-message">
          <span class="error-icon">⚠️</span>
          {{ error }}
        </p>

        <button 
          type="submit" 
          class="register-button"
          :disabled="isLoading"
        >
          <span v-if="!isLoading">Создать аккаунт</span>
          <span v-else class="button-loader"></span>
        </button>

        <div class="login-prompt">
          <span class="prompt-text">Уже есть аккаунт?</span>
          <router-link to="/login" class="login-link">Войти</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
/* Копируем ВСЕ стили из login, но меняем class-префиксы */
.register-screen {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  position: relative;
  overflow: hidden;
}

.register-container {
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

.logo-wrapper {
  text-align: center;
  margin-bottom: 24px;
}

.logo-glass {
  width: 90px;
  height: 90px;
  margin: 0 auto 12px;
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
  width: 70px;
  height: 70px;
  border-radius: 24px;
  object-fit: cover;
}

.app-name {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 4px;
  background: linear-gradient(135deg, #1a1a1a 0%, #4a4a4a 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.5px;
}

.app-subtitle {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.5);
  font-weight: 400;
  margin: 0;
}

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
  padding: 16px 16px 16px 52px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1.5px solid rgba(255, 255, 255, 0.8);
  border-radius: 20px;
  font-size: 15px;
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

/* Условия использования */
.terms {
  margin: 8px 0 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.6);
}

.terms input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: #8B5CF6;
}

.terms-link {
  color: #8B5CF6;
  text-decoration: none;
  font-weight: 500;
}

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

.register-button {
  width: 100%;
  padding: 16px;
  background: linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%);
  border: none;
  border-radius: 24px;
  font-size: 16px;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 10px 20px rgba(139, 92, 246, 0.3);
  margin-bottom: 16px;
  position: relative;
  overflow: hidden;
}

.register-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s;
}

.register-button:active::before {
  left: 100%;
}

.register-button:active {
  transform: scale(0.98);
  box-shadow: 0 5px 15px rgba(139, 92, 246, 0.4);
}

.register-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.login-prompt {
  text-align: center;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.4);
}

.prompt-text {
  color: rgba(0, 0, 0, 0.5);
  font-size: 14px;
  margin-right: 8px;
}

.login-link {
  color: #8B5CF6;
  text-decoration: none;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s;
  padding: 8px 0;
  display: inline-block;
}

/* Те же анимации */
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