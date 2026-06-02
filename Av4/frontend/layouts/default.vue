<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useUserStore } from '~/stores/user'
import { useApiService } from '~/services/api'

const user = useUserStore()
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
      class="fixed inset-y-0 left-0 z-40 w-72 transform border-r border-slate-200 bg-white transition-transform lg:static lg:translate-x-0"
      :class="mobileOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <div class="flex h-full flex-col p-4">
        <div class="mb-6 flex items-center gap-2 px-2">
          <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-lg text-white shadow-sm">
            🏷️
          </div>
          <div>
            <p class="text-sm font-bold leading-tight text-slate-900">Promoções</p>
            <p class="text-xs text-slate-400">Plataforma EDA</p>
          </div>
        </div>

        <NavBar @click="mobileOpen = false" />

        <div class="mt-auto space-y-3 pt-6">
          <ConsumerSelector />
          <div class="flex items-center gap-2 px-1 text-xs">
            <span
              class="h-2 w-2 rounded-full"
              :class="gatewayOnline === null
                ? 'bg-slate-300'
                : gatewayOnline
                  ? 'bg-emerald-500'
                  : 'bg-rose-500'"
            />
            <span class="text-slate-400">
              Gateway
              <template v-if="gatewayOnline === null">…</template>
              <template v-else>{{ gatewayOnline ? 'online' : 'offline' }}</template>
            </span>
          </div>
        </div>
      </div>
    </aside>

    <div
      v-if="mobileOpen"
      class="fixed inset-0 z-30 bg-slate-900/30 lg:hidden"
      @click="mobileOpen = false"
    />

    <!-- Main -->
    <div class="flex min-w-0 flex-1 flex-col">
      <header class="flex items-center gap-3 border-b border-slate-200 bg-white/80 px-4 py-3 backdrop-blur lg:hidden">
        <button class="btn-ghost btn-sm" @click="mobileOpen = !mobileOpen">☰</button>
        <span class="font-semibold text-slate-800">Promoções</span>
        <span class="ml-auto badge bg-slate-100 text-slate-500">{{ user.consumerId }}</span>
      </header>

      <main class="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">
        <slot />
      </main>

      <footer class="border-t border-slate-200 px-4 py-4 text-center text-xs text-slate-400">
        Av4 — Plataforma Distribuída de Promoções · Frontend Nuxt 3
      </footer>
    </div>
  </div>
</template>
