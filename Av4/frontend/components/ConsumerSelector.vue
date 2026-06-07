<script setup lang="ts">
import { ref, watch } from 'vue'
import { useUserStore } from '~/stores/user'
import { useToast } from '~/composables/useToast'

const user = useUserStore()
const toast = useToast()
const draft = ref(user.consumerId)
const presets = ['cliente_a', 'cliente_b', 'cliente_c']

watch(
  () => user.consumerId,
  (v) => {
    draft.value = v
  }
)

function apply() {
  const value = draft.value.trim()
  if (!value || value === user.consumerId) return
  user.setConsumerId(value)
  toast.info(`Usuário ativo: ${value}`)
}
</script>

<template>
  <div class="rounded-2xl border border-bone-200 bg-bone-100/60 p-3.5">
    <label class="label">Usuário ativo</label>
    <div class="flex gap-2">
      <input
        v-model="draft"
        class="input nums"
        placeholder="cliente_a"
        @keyup.enter="apply"
      />
      <button class="btn-primary btn-sm shrink-0" @click="apply">Trocar</button>
    </div>
    <div class="mt-2.5 flex flex-wrap gap-1.5">
      <button
        v-for="p in presets"
        :key="p"
        class="badge nums px-2.5 py-1 ring-1 ring-inset transition-all"
        :class="user.consumerId === p
          ? 'bg-pine-800 text-bone-50 ring-pine-800'
          : 'bg-bone-50 text-ink-500 ring-bone-300 hover:ring-pine-300'"
        @click="draft = p; apply()"
      >
        {{ p }}
      </button>
    </div>
  </div>
</template>
