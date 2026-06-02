import { ref, onBeforeUnmount } from 'vue'
import type { SseStatus } from '~/types'

interface UseSseOptions {
  onMessage: (raw: string, eventName: string) => void
  onReady?: () => void
  onStatus?: (status: SseStatus) => void
}

/**
 * EventSource lifecycle helper. Connect to the notifications stream for a
 * consumerId; cleanly closes the previous connection on reconnect/unmount.
 */
export function useSse(options: UseSseOptions) {
  const config = useRuntimeConfig()
  const baseURL = config.public.gatewayUrl as string
  const status = ref<SseStatus>('idle')
  let es: EventSource | null = null

  function setStatus(s: SseStatus) {
    status.value = s
    options.onStatus?.(s)
  }

  function close() {
    if (es) {
      es.close()
      es = null
      setStatus('closed')
    }
  }

  function connect(consumerId: string) {
    close()
    if (!consumerId) return
    if (typeof window === 'undefined' || typeof EventSource === 'undefined') return

    setStatus('connecting')
    const url = `${baseURL}/api/notificacoes/stream?consumerId=${encodeURIComponent(consumerId)}`
    es = new EventSource(url)

    es.onopen = () => setStatus('open')

    es.onerror = () => {
      // EventSource auto-reconnects; surface the transient error state.
      setStatus('error')
    }

    es.addEventListener('ready', () => {
      setStatus('open')
      options.onReady?.()
    })

    es.addEventListener('notificacao', (ev) => {
      options.onMessage((ev as MessageEvent).data, 'notificacao')
    })
  }

  onBeforeUnmount(close)

  return { status, connect, close }
}
