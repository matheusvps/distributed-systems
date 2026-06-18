<script setup lang="ts">
const props = withDefaults(
  defineProps<{ name: string; size?: number | string; strokeWidth?: number }>(),
  { size: 20, strokeWidth: 1.75 }
)

const paths: Record<string, string> = {
  tag: 'M3.5 11.5 11 4h6.5a2 2 0 0 1 2 2V12L12 19.5a1.5 1.5 0 0 1-2.1 0L3.5 13.6a1.5 1.5 0 0 1 0-2.1Z M15.5 8.5h.01',
  flame: 'M12 3c.5 3 3 4 3 7a3 3 0 0 1-6 0c0-1 .4-1.7 1-2.3M12 21a6 6 0 0 0 6-6c0-4-2.5-6-4-9-1 4-4 4.5-5.5 7A6 6 0 0 0 12 21Z',
  plus: 'M12 5v14M5 12h14',
  bookmark: 'M6 4h12a1 1 0 0 1 1 1v15l-7-4-7 4V5a1 1 0 0 1 1-1Z',
  bell: 'M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6M10 21a2 2 0 0 0 4 0',
  refresh: 'M4 9a8 8 0 0 1 13.7-3.5L20 8M20 4v4h-4M20 15a8 8 0 0 1-13.7 3.5L4 16M4 20v-4h4',
  store: 'M4 9.5 5.2 5h13.6L20 9.5M4 9.5h16M4 9.5v9a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-9M4 9.5a2.2 2.2 0 0 0 4 0 2.2 2.2 0 0 0 4 0 2.2 2.2 0 0 0 4 0 2.2 2.2 0 0 0 4 0',
  check: 'M5 12.5 10 17 19 7',
  close: 'M6 6l12 12M18 6 6 18',
  info: 'M12 11v6M12 7.5h.01M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z',
  alert: 'M12 9v4M12 17h.01M10.3 4l-7 12.5A1.5 1.5 0 0 0 4.6 19h14.8a1.5 1.5 0 0 0 1.3-2.5L13.7 4a2 2 0 0 0-3.4 0Z',
  inbox: 'M4 13h4l1.5 3h5L16 13h4M4 13l2.5-8h11L20 13M4 13v5a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-5',
  up: 'M6 14h3v6h6V11l3-1-4-7c-1.2 0-2 .6-2.5 2L9 9H6a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2Z',
  down: 'M18 10h-3V4H9v9l-3 1 4 7c1.2 0 2-.6 2.5-2L15 15h3a2 2 0 0 0 2-2v-1a2 2 0 0 0-2-2Z',
  menu: 'M4 7h16M4 12h16M4 17h16',
  spark: 'M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18',
  trending: 'M4 16l5-5 3 3 7-7M15 7h5v5',
  user: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM4.5 20a7.5 7.5 0 0 1 15 0',
  logout: 'M14 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-2M10 12h11M21 12l-3-3M21 12l-3 3',
  arrowRight: 'M5 12h14M13 6l6 6-6 6',
  clock: 'M12 7v5l3 2M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z'
}

const isFilledDot = (n: string) => n === 'check' || n === 'close' || n === 'menu'
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    :stroke-width="strokeWidth"
    stroke="currentColor"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    class="shrink-0"
  >
    <path :d="paths[name] || paths.info" />
  </svg>
</template>
