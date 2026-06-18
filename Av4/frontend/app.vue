<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useUserStore } from '~/stores/user'
import { useMinhasStore } from '~/stores/minhas'

const user = useUserStore()
const minhas = useMinhasStore()
const mounted = ref(false)

onMounted(() => {
  user.hydrate()
  minhas.hydrate()
  mounted.value = true
})
</script>

<template>
  <div>
    <template v-if="mounted">
      <WelcomeScreen v-if="!user.role" />
      <NuxtLayout v-else>
        <NuxtPage />
      </NuxtLayout>
    </template>

    <div v-else class="grid min-h-screen place-items-center bg-bone-100">
      <div class="flex items-center gap-3 text-ink-400">
        <span class="h-5 w-5 animate-spin rounded-full border-2 border-bone-300 border-t-pine-600" />
        <span class="font-display font-bold tracking-tight text-ink-700">Mercado</span>
      </div>
    </div>

    <ToastHost />
  </div>
</template>
