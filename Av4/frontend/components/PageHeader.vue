<script setup lang="ts">
defineProps<{ title: string; subtitle?: string; eyebrow?: string }>()
</script>

<template>
  <div class="mb-8 flex flex-wrap items-end justify-between gap-4 animate-rise-in">
    <div class="min-w-0">
      <p v-if="eyebrow" class="eyebrow mb-2">
        <span class="h-px w-6 bg-pine-400" />
        {{ eyebrow }}
      </p>
      <h1 class="font-display text-3xl font-extrabold tracking-tightest text-ink-900 sm:text-4xl">
        {{ title }}
      </h1>
      <p v-if="subtitle" class="mt-2 max-w-xl text-sm leading-relaxed text-ink-500">{{ subtitle }}</p>
    </div>
    <div class="flex items-center gap-2">
      <slot name="actions" />
    </div>
  </div>
</template>
