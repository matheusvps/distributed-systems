<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useUserStore } from '~/stores/user'
import { useApiService } from '~/services/api'
import { useNotificacoesStore } from '~/stores/notificacoes'
import { useNotificationPanel } from '~/composables/useNotificationPanel'

const user = useUserStore()
const notif = useNotificacoesStore()
const { toggle: toggleNotif } = useNotificationPanel()
const unread = computed(() => notif.unread)
const mobileOpen = ref(false)
const gatewayOnline = ref<boolean | null>(null)

onMounted(async () => {
  user.hydrate()
  try {
    await useApiService().health()
    gatewayOnline.value = true
  } catch {
    gatewayOnline.value = false
  }
})
</script>

<template>
  <div class="min-h-screen lg:flex">
    <!-- Sidebar -->
    <aside
      class="fixed inset-y-0 left-0 z-40 w-72 transform border-r border-bone-200 bg-bone-50/80 backdrop-blur-md transition-transform duration-300 lg:static lg:translate-x-0"
      :class="mobileOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <div class="flex h-full flex-col p-5">
        <!-- Wordmark -->
        <NuxtLink to="/" class="mb-8 flex items-center gap-3 px-1" @click="mobileOpen = false">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-pine-800 text-acid-300 shadow-card">
            <Icon name="tag" :size="20" :stroke-width="2" />
          </div>
          <div>
            <p class="font-display text-lg font-extrabold leading-none tracking-tightest text-ink-900">
              Mercado
            </p>
            <p class="mt-1 text-[0.7rem] font-medium uppercase tracking-[0.16em] text-ink-400">
              Promoções ao vivo
            </p>
          </div>
        </NuxtLink>

        <NavBar @click="mobileOpen = false" />

        <div class="mt-auto space-y-3 pt-6">
          <ConsumerSelector />
          <div class="flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs">
            <span class="relative flex h-2 w-2">
              <span
                v-if="gatewayOnline"
                class="absolute inline-flex h-full w-full animate-ping rounded-full bg-pine-400 opacity-60"
              />
              <span
                class="relative inline-flex h-2 w-2 rounded-full"
                :class="gatewayOnline === null
                  ? 'bg-bone-400'
                  : gatewayOnline
                    ? 'bg-pine-500'
                    : 'bg-rose-500'"
              />
            </span>
            <span class="font-medium text-ink-500">Gateway</span>
            <span class="ml-auto nums text-ink-400">
              <template v-if="gatewayOnline === null">—</template>
              <template v-else>{{ gatewayOnline ? 'online' : 'offline' }}</template>
            </span>
          </div>
        </div>
      </div>
    </aside>

    <div
      v-if="mobileOpen"
      class="fixed inset-0 z-30 bg-pine-950/40 backdrop-blur-sm lg:hidden"
      @click="mobileOpen = false"
    />

    <!-- Main -->
    <div class="flex min-w-0 flex-1 flex-col">
      <header class="sticky top-0 z-20 flex items-center gap-3 border-b border-bone-200 bg-bone-100/80 px-4 py-3 backdrop-blur-md lg:hidden">
        <button class="btn-ghost btn-sm" aria-label="Abrir menu" @click="mobileOpen = !mobileOpen">
          <Icon name="menu" :size="18" />
        </button>
        <span class="font-display font-bold tracking-tight text-ink-900">Mercado</span>
        <button
          class="relative ml-auto flex h-9 w-9 items-center justify-center rounded-lg text-ink-700 transition hover:bg-bone-200"
          aria-label="Notificações"
          @click="toggleNotif"
        >
          <Icon name="bell" :size="18" />
          <span
            v-if="unread > 0"
            class="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-acid-400 px-1 text-[0.6rem] font-bold text-pine-900"
          >
            {{ unread > 9 ? '9+' : unread }}
          </span>
        </button>
      </header>

      <main class="mx-auto w-full max-w-6xl flex-1 px-4 py-10 sm:px-8">
        <slot />
      </main>

      <footer class="border-t border-bone-200 px-4 py-5 text-center text-xs text-ink-400">
        Mercado — Plataforma Distribuída de Promoções · Arquitetura Orientada a Eventos
      </footer>
    </div>

    <!-- Painel de notificações global (hospeda a conexão SSE) -->
    <NotificationMenu />
  </div>
</template>
