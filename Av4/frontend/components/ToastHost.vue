<script setup lang="ts">
import { useToast } from '~/composables/useToast'

const { toasts, dismiss } = useToast()

const styles: Record<string, string> = {
  success: 'border-pine-200 bg-pine-50 text-pine-800',
  error: 'border-rose-200 bg-rose-50 text-rose-700',
  info: 'border-bone-300 bg-bone-50 text-ink-700'
}
const icons: Record<string, string> = {
  success: 'check',
  error: 'close',
  info: 'info'
}
</script>

<template>
  <div class="pointer-events-none fixed inset-x-0 top-4 z-[100] flex flex-col items-center gap-2 px-4">
    <TransitionGroup name="toast">
      <div
        v-for="t in toasts"
        :key="t.id"
        class="pointer-events-auto flex w-full max-w-md items-start gap-3 rounded-xl border px-4 py-3 text-sm shadow-cardhover backdrop-blur-sm"
        :class="styles[t.kind]"
      >
        <span class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-current/10">
          <Icon :name="icons[t.kind]" :size="13" :stroke-width="2.25" />
        </span>
        <p class="flex-1 font-medium leading-snug">{{ t.message }}</p>
        <button
          class="opacity-50 transition hover:opacity-100"
          aria-label="Fechar"
          @click="dismiss(t.id)"
        >
          <Icon name="close" :size="15" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s cubic-bezier(0.2, 0.7, 0.2, 1);
}
.toast-enter-from {
  opacity: 0;
  transform: translateY(-12px) scale(0.96);
}
.toast-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.98);
}
</style>
