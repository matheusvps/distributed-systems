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
  <div class="rounded-xl border border-slate-200 bg-slate-50/80 p-3">
    <label class="label">Usuário (consumerId)</label>
    <div class="flex gap-2">
      <input
        v-model="draft"
        class="input"
        placeholder="cliente_a"
        @keyup.enter="apply"
      />
      <button class="btn-primary btn-sm shrink-0" @click="apply">Trocar</button>
    </div>
    <div class="mt-2 flex flex-wrap gap-1.5">
      <button
        v-for="p in presets"
        :key="p"
        class="badge px-2 py-0.5 ring-1 ring-inset transition"
        :class="user.consumerId === p
          ? 'bg-brand-600 text-white ring-brand-600'
          : 'bg-white text-slate-500 ring-slate-200 hover:bg-slate-100'"
        @click="draft = p; apply()"
      >
        {{ p }}
      </button>
    </div>
  </div>
</template>
