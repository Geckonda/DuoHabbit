import api from './index'

export const auth = {
  async login(email, password) {
    // fastapi-users ожидает form-data с полем username
    const formData = new FormData()
    formData.append('username', email)  // да, email в поле username
    formData.append('password', password)
    
    const response = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    return response.data // { access_token: string, token_type: string }
  },
  
  async register(userData) {
    // userData должен соответствовать UserCreate из бекенда
    const response = await api.post('/users', {
      email: userData.email,
      username: userData.username,
      password: userData.password,
      is_platform_admin: userData.is_platform_admin || false
    })
    
    return response.data // обычно возвращает UserRead
  },
  
  async logout() {
    return api.post('/auth/logout')
  },
  
  async getMe() {
    return api.get('/users/me') // возвращает UserRead
  }
}