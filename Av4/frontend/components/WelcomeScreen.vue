<script setup lang="ts">
import { ref } from 'vue'
import { useUserStore } from '~/stores/user'
import { useToast } from '~/composables/useToast'

const user = useUserStore()
const toast = useToast()

const consumerId = ref(user.consumerId || 'cliente_a')
const presets = ['cliente_a', 'cliente_b', 'cliente_c']

const lojaName = ref(user.loja.name)
const lojaEmail = ref(user.loja.email)

const emailValid = (v: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim())

async function entrarCliente() {
  const id = consumerId.value.trim()
  if (!id) {
    toast.error('Informe um identificador de cliente')
    return
  }
  user.enterAsCliente(id)
  await navigateTo('/')
}

async function entrarLoja() {
  if (!lojaName.value.trim()) {
    toast.error('Informe o nome da loja')
    return
  }
  if (!emailValid(lojaEmail.value)) {
    toast.error('Informe um e-mail de loja válido')
    return
  }
  user.enterAsLoja(lojaName.value, lojaEmail.value)
  await navigateTo('/loja')
}
</script>

<template>
  <div class="relative min-h-screen overflow-hidden">
    <!-- Marca decorativa em watermark -->
    <p
      class="pointer-events-none absolute -bottom-20 -right-10 select-none font-display text-[18rem] font-extrabold leading-none tracking-tightest text-pine-900/[0.03]"
    >
      Mercado
    </p>

    <div class="mx-auto flex min-h-screen max-w-5xl flex-col justify-center px-6 py-12">
      <header class="mb-10 animate-rise-in">
        <div class="mb-5 inline-flex items-center gap-3">
          <div class="flex h-11 w-11 items-center justify-center rounded-xl bg-pine-800 text-acid-300 shadow-card">
            <Icon name="tag" :size="22" :stroke-width="2" />
          </div>
          <span class="font-display text-xl font-extrabold tracking-tightest text-ink-900">Mercado</span>
        </div>
        <p class="eyebrow mb-3">
          <span class="h-px w-6 bg-pine-400" /> Plataforma de promoções
        </p>
        <h1 class="font-display text-4xl font-extrabold tracking-tightest text-ink-900 sm:text-5xl">
          Como você quer entrar?
        </h1>
        <p class="mt-3 max-w-lg text-ink-500">
          Escolha seu perfil. Você pode trocar a qualquer momento — suas identidades ficam salvas neste dispositivo.
        </p>
      </header>

      <div class="grid gap-5 md:grid-cols-2">
        <!-- Cliente -->
        <section
          class="card flex flex-col p-6 animate-rise-in"
          style="animation-delay: 80ms"
        >
          <div class="mb-4 flex items-center gap-3">
            <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-pine-50 text-pine-700 ring-1 ring-pine-100">
              <Icon name="user" :size="24" />
            </div>
            <div>
              <h2 class="font-display text-xl font-bold text-ink-900">Sou Cliente</h2>
              <p class="text-sm text-ink-500">Explorar ofertas, votar e seguir categorias</p>
            </div>
          </div>

          <label class="label">Identificador de cliente</label>
          <input
            v-model="consumerId"
            class="input nums"
            placeholder="cliente_a"
            @keyup.enter="entrarCliente"
          />
          <div class="mt-2.5 flex flex-wrap gap-1.5">
            <button
              v-for="p in presets"
              :key="p"
              class="badge nums px-2.5 py-1 ring-1 ring-inset transition-all"
              :class="consumerId === p
                ? 'bg-pine-800 text-bone-50 ring-pine-800'
                : 'bg-bone-50 text-ink-500 ring-bone-300 hover:ring-pine-300'"
              @click="consumerId = p"
            >
              {{ p }}
            </button>
          </div>

          <button class="btn-primary mt-auto w-full pt-2" @click="entrarCliente">
            <Icon name="arrowRight" :size="16" /> Entrar como cliente
          </button>
        </section>

        <!-- Loja -->
        <section
          class="card relative flex flex-col overflow-hidden p-6 ring-1 ring-acid-200 animate-rise-in"
          style="animation-delay: 160ms"
        >
          <div class="absolute right-0 top-0 h-24 w-24 rounded-bl-[3rem] bg-acid-100/60" />
          <div class="relative mb-4 flex items-center gap-3">
            <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-pine-800 text-acid-300">
              <Icon name="store" :size="24" />
            </div>
            <div>
              <h2 class="font-display text-xl font-bold text-ink-900">Sou Loja</h2>
              <p class="text-sm text-ink-500">Cadastrar e acompanhar suas promoções</p>
            </div>
          </div>

          <div class="relative space-y-3">
            <div>
              <label class="label">Nome da loja</label>
              <input v-model="lojaName" class="input" placeholder="Minha Loja" @keyup.enter="entrarLoja" />
            </div>
            <div>
              <label class="label">E-mail da loja</label>
              <input
                v-model="lojaEmail"
                type="email"
                class="input"
                placeholder="contato@loja.com"
                @keyup.enter="entrarLoja"
              />
            </div>
          </div>

          <button class="btn-accent mt-5 w-full" @click="entrarLoja">
            <Icon name="arrowRight" :size="16" /> Entrar como loja
          </button>
        </section>
      </div>
    </div>
  </div>
</template>
