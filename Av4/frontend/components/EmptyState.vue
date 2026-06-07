<script setup lang="ts">
defineProps<{ icon?: string; title: string; subtitle?: string }>()
</script>

<template>
  <div class="flex flex-col items-center justify-center rounded-2xl border border-dashed border-bone-300 bg-bone-50/50 px-6 py-20 text-center animate-fade-in">
    <div class="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-bone-200 text-pine-700">
      <Icon :name="icon || 'inbox'" :size="26" />
    </div>
    <h3 class="font-display text-lg font-bold text-ink-900">{{ title }}</h3>
    <p v-if="subtitle" class="mt-1.5 max-w-sm text-sm text-ink-500">{{ subtitle }}</p>
    <slot />
  </div>
</template>
