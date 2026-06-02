<script setup lang="ts">
defineProps<{ category?: string }>()
</script>

<template>
  <span v-if="category" class="badge bg-slate-100 text-slate-600">
    {{ category }}
  </span>
</template>
