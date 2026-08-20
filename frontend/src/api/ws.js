// api/ws.js
// Клиент канала доставки чата. Отправка идет через REST, сюда приходят события.

const RECONNECT_BASE_DELAY = 1000
const RECONNECT_MAX_DELAY = 15000

// Код, которым бэкенд закрывает соединение с плохим токеном
const POLICY_VIOLATION = 1008

function buildSocketUrl(token) {
  const apiUrl = import.meta.env.VITE_API_URL || window.location.origin

  // VITE_API_URL может быть как абсолютным (http://localhost:8000),
  // так и относительным (/api) - во втором случае берем текущий origin
  const base = apiUrl.startsWith('http')
    ? apiUrl
    : `${window.location.origin}${apiUrl}`

  const wsBase = base.replace(/^http/, 'ws').replace(/\/$/, '')

  return `${wsBase}/chat/ws?token=${encodeURIComponent(token)}`
}

export function createChatSocket({ onEvent, onStatusChange } = {}) {
  let socket = null
  let reconnectAttempts = 0
  let reconnectTimer = null
  let closedByUs = false

  const setStatus = (status) => {
    if (onStatusChange) onStatusChange(status)
  }

  const scheduleReconnect = () => {
    // Растущая пауза: fastapi dev рвет сокеты на каждой перезагрузке кода,
    // и долбиться раз в секунду в лежащий бэкенд смысла нет
    const delay = Math.min(
      RECONNECT_BASE_DELAY * 2 ** reconnectAttempts,
      RECONNECT_MAX_DELAY
    )
    reconnectAttempts += 1
    reconnectTimer = setTimeout(connect, delay)
  }

  function connect() {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setStatus('unauthorized')
      return
    }

    closedByUs = false
    socket = new WebSocket(buildSocketUrl(token))

    socket.onopen = () => {
      reconnectAttempts = 0
      setStatus('connected')
    }

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        if (onEvent) onEvent(payload)
      } catch (error) {
        console.error('Не удалось разобрать событие чата:', error)
      }
    }

    socket.onclose = (event) => {
      socket = null

      if (closedByUs) {
        setStatus('closed')
        return
      }

      // Токен протух или невалиден - переподключение не поможет
      if (event.code === POLICY_VIOLATION) {
        setStatus('unauthorized')
        return
      }

      setStatus('reconnecting')
      scheduleReconnect()
    }
  }

  function close() {
    closedByUs = true
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (socket) {
      socket.close()
      socket = null
    }
    setStatus('closed')
  }

  return { connect, close }
}
