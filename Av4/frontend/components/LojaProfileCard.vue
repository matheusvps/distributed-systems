<script setup lang="ts">
import { ref, watch } from 'vue'
import { useUserStore } from '~/stores/user'
import { useToast } from '~/composables/useToast'

const user = useUserStore()
const toast = useToast()

const editing = ref(false)
const name = ref(user.loja.name)
const email = ref(user.loja.email)

watch(
  () => [user.loja.name, user.loja.email],
  () => {
    name.value = user.loja.name
    email.value = user.loja.email
  }
)

const emailValid = (v: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim())

function save() {
  if (!name.value.trim()) {
    toast.error('Informe o nome da loja')
    return
  }
  if (!emailValid(email.value)) {
    toast.error('E-mail inválido')
    return
  }
  user.setLoja(name.value, email.value)
  editing.value = false
  toast.success('Perfil da loja atualizado')
}
</script>

<template>
  <div class="rounded-2xl border border-bone-200 bg-bone-100/60 p-3.5">
    <div class="flex items-center justify-between">
      <label class="label mb-0">Perfil da loja</label>
      <button
        v-if="!editing"
        class="text-xs font-semibold text-pine-600 hover:text-pine-800"
        @click="editing = true"
      >
        Editar
      </button>
    </div>

    <div v-if="!editing" class="mt-2 flex items-center gap-2.5">
      <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-pine-800 text-acid-300">
        <Icon name="store" :size="18" />
      </div>
      <div class="min-w-0">
        <p class="truncate text-sm font-bold text-ink-900">{{ user.loja.name || '—' }}</p>
        <p class="truncate text-xs text-ink-400">{{ user.loja.email || 'sem e-mail' }}</p>
      </div>
    </div>

    <div v-else class="mt-2 space-y-2">
      <input v-model="name" class="input" placeholder="Nome da loja" />
      <input v-model="email" type="email" class="input" placeholder="contato@loja.com" />
      <div class="flex gap-2">
        <button class="btn-primary btn-sm flex-1" @click="save">Salvar</button>
        <button class="btn-ghost btn-sm" @click="editing = false">Cancelar</button>
      </div>
    </div>
  </div>
</template>
