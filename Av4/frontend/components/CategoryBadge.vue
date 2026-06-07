<script setup lang="ts">
defineProps<{ category?: string }>()
</script>

<template>
  <span
    v-if="category"
    class="badge bg-bone-200 text-ink-700 ring-1 ring-inset ring-bone-300 capitalize"
  >
    {{ category }}
  </span>
</template>
