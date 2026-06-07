<script setup lang="ts">
defineProps<{ categories: string[]; modelValue: string }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: string): void }>()
</script>

<template>
  <div class="flex flex-wrap items-center gap-2">
    <button
      class="badge px-3 py-1.5 ring-1 ring-inset transition-all capitalize"
      :class="modelValue === ''
        ? 'bg-pine-800 text-bone-50 ring-pine-800'
        : 'bg-bone-50 text-ink-700 ring-bone-300 hover:ring-pine-300'"
      @click="emit('update:modelValue', '')"
    >
      Todas
    </button>
    <button
      v-for="c in categories"
      :key="c"
      class="badge px-3 py-1.5 ring-1 ring-inset transition-all capitalize"
      :class="modelValue === c
        ? 'bg-pine-800 text-bone-50 ring-pine-800'
        : 'bg-bone-50 text-ink-700 ring-bone-300 hover:ring-pine-300'"
      @click="emit('update:modelValue', c)"
    >
      {{ c }}
    </button>
  </div>
</template>
