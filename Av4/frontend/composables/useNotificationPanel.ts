import { ref } from 'vue'

// Module-level singleton: the trigger button (NavBar / mobile header) and the
// drawer (NotificationMenu) share the same open state across the app.
const open = ref(false)

export function useNotificationPanel() {
  function toggle() {
    open.value = !open.value
  }
  function close() {
    open.value = false
  }
  return { open, toggle, close }
}
