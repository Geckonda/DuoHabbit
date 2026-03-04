// Эти типы должны соответствовать твоим pydantic-схемам на беке

export interface UserRead {
  id: number
  email: string
  username: string
  is_active: boolean
  is_superuser: boolean
  is_verified: boolean
  is_platform_admin: boolean
}

export interface UserCreate {
  email: string
  username: string
  password: string
  is_platform_admin?: boolean  // опционально, для админов
}

export interface UserLogin {
  username: string  // внимание! fastapi-users ждет username, не email
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}