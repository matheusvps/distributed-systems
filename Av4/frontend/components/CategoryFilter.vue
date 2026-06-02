<script setup lang="ts">
defineProps<{ categories: string[]; modelValue: string }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: string): void }>()
</script>

<template>
  <div class="flex flex-wrap items-center gap-2">
    <button
      class="badge px-3 py-1 ring-1 ring-inset transition"
      :class="modelValue === ''
        ? 'bg-brand-600 text-white ring-brand-600'
        : 'bg-white text-slate-600 ring-slate-200 hover:bg-slate-50'"
      @click="emit('update:modelValue', '')"
    >
      Todas
    </button>
    <button
      v-for="c in categories"
      :key="c"
      class="badge px-3 py-1 ring-1 ring-inset transition"
      :class="modelValue === c
        ? 'bg-brand-600 text-white ring-brand-600'
        : 'bg-white text-slate-600 ring-slate-200 hover:bg-slate-50'"
      @click="emit('update:modelValue', c)"
    >
      {{ c }}
    </button>
  </div>
</template>
