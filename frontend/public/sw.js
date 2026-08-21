// Service worker только для Web Push - без офлайн-кеша и precache.
// Копируется в dist как есть (Vite копирует public/* без изменений).

self.addEventListener('install', () => {
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim())
})

self.addEventListener('push', (event) => {
  if (!event.data) return

  const payload = event.data.json()
  const { title, body, url, tag } = payload

  event.waitUntil(
    self.registration.showNotification(title || 'DuoHabit', {
      body,
      tag,
      icon: '/web-app-manifest-192x192.png',
      data: { url: url || '/' },
    })
  )
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const url = event.notification.data?.url || '/'

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
      const existing = clients.find((client) => new URL(client.url).pathname === url)
      if (existing) return existing.focus()
      return self.clients.openWindow(url)
    })
  )
})
