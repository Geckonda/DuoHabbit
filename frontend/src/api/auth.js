import api from './index'

export const auth = {
  async login(email, password) {
    const formData = new FormData()
    formData.append('username', email)
    formData.append('password', password)
    
    const response = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token)
    }
    return response.data
  },
  
  async logout() {
    try {
      await api.post('/auth/logout')
    } finally {
      localStorage.removeItem('access_token')
    }
  },
  
  async getMe() {
    return api.get('/users/me')
  }
}