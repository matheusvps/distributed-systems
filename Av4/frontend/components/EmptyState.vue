<script setup lang="ts">
defineProps<{ icon?: string; title: string; subtitle?: string }>()
</script>

<template>
  <div class="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-white/60 px-6 py-16 text-center">
    <div class="mb-3 text-4xl">{{ icon || '📭' }}</div>
    <h3 class="text-base font-semibold text-slate-700">{{ title }}</h3>
    <p v-if="subtitle" class="mt-1 max-w-sm text-sm text-slate-400">{{ subtitle }}</p>
    <slot />
  </div>
</template>
