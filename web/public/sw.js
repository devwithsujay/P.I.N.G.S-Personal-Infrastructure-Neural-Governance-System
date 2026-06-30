const CACHE_NAME = 'pings-v2'
const SHELL_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/pings-icon.svg',
  '/src/index.css',
  '/src/main.jsx',
  '/src/App.jsx',
  '/src/api.js',
  '/src/components/SidebarBrand.jsx',
  '/src/components/Sidebar.jsx',
  '/src/components/MobileNav.jsx',
  '/src/components/BootSequence.jsx',
  '/src/pages/Chat.jsx',
  '/src/pages/ResearchPage.jsx',
  '/src/pages/Tasks.jsx',
  '/src/pages/Calendar.jsx',
  '/src/pages/HomeLab.jsx',
  '/src/pages/Skills.jsx',
  '/src/pages/History.jsx',
  '/src/pages/MissionControl.jsx',
  '/src/pages/Settings.jsx'
]

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_ASSETS))
  )
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  )
  self.clients.claim()
})

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url)

  if (url.pathname.startsWith('/api/')) {
    event.respondWith(fetch(event.request))
    return
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      const fetched = fetch(event.request).then((response) => {
        if (response.ok) {
          const clone = response.clone()
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone))
        }
        return response
      }).catch(() => cached)

      return cached || fetched
    })
  )
})
