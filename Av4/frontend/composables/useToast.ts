import { reactive } from 'vue'

export type ToastKind = 'success' | 'error' | 'info'

export interface Toast {
  id: number
  kind: ToastKind
  message: string
}

const state = reactive<{ toasts: Toast[] }>({ toasts: [] })
let counter = 0

export function useToast() {
  function push(message: string, kind: ToastKind = 'info', timeout = 3500) {
    const id = ++counter
    state.toasts.push({ id, message, kind })
    if (timeout > 0) {
      setTimeout(() => dismiss(id), timeout)
    }
    return id
  }

  function dismiss(id: number) {
    const i = state.toasts.findIndex((t) => t.id === id)
    if (i !== -1) state.toasts.splice(i, 1)
  }

  return {
    toasts: state.toasts,
    push,
    success: (m: string) => push(m, 'success'),
    error: (m: string) => push(m, 'error'),
    info: (m: string) => push(m, 'info'),
    dismiss
  }
}
