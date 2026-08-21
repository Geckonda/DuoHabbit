// composables/useSafeBack.js
import { useRouter } from 'vue-router'

// router.back() does nothing (or leaves the app) if we arrived via a deep link,
// refresh, or external referrer — there's no in-app history entry to pop.
// window.history.state.back is set by createWebHistory() whenever a real
// previous entry exists, so we can fall back to a known-good path otherwise.
export function useSafeBack() {
  const router = useRouter()

  return (fallbackPath = '/') => {
    if (window.history.state?.back) {
      router.back()
    } else {
      router.push(fallbackPath)
    }
  }
}
