<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue'
import { usePromocoesStore } from '~/stores/promocoes'
import { useUserStore } from '~/stores/user'
import { useMinhasStore } from '~/stores/minhas'
import { useToast } from '~/composables/useToast'

const store = usePromocoesStore()
const user = useUserStore()
const minhas = useMinhasStore()
const toast = useToast()

const form = reactive({
  title: '',
  description: '',
  category: '',
  price: '' as string | number,
  originalPrice: '' as string | number
})

const submitting = ref(false)
const touched = ref(false)

const priceNum = computed(() => Number(form.price))
const origNum = computed(() => Number(form.originalPrice))

const errors = computed(() => {
  const e: Record<string, string> = {}
  if (!form.title.trim()) e.title = 'Informe o título'
  if (!form.description.trim()) e.description = 'Informe a descrição'
  if (!form.category.trim()) e.category = 'Selecione a categoria'
  if (form.price === '' || isNaN(priceNum.value) || priceNum.value < 0) e.price = 'Preço inválido'
  if (form.originalPrice === '' || isNaN(origNum.value) || origNum.value < 0)
    e.originalPrice = 'Preço original inválido'
  else if (!isNaN(priceNum.value) && priceNum.value > origNum.value)
    e.price = 'Preço deve ser menor que o original'
  return e
})
const isValid = computed(() => Object.keys(errors.value).length === 0)

onMounted(() => {
  if (!store.categories.length) store.fetchCategories()
})

async function submit() {
  touched.value = true
  if (!isValid.value) {
    toast.error('Corrija os campos destacados')
    return
  }
  submitting.value = true
  try {
    const payload = {
      title: form.title.trim(),
      description: form.description.trim(),
      category: form.category.trim(),
      price: priceNum.value,
      originalPrice: origNum.value,
      store: user.loja.name,
      storeEmail: user.loja.email
    }
    const res = await store.createPromotion(payload)
    if (res?.promotionId) {
      minhas.add({
        id: res.promotionId,
        title: payload.title,
        category: payload.category,
        price: payload.price,
        originalPrice: payload.originalPrice,
        store: payload.store,
        storeEmail: payload.storeEmail,
        submittedAt: new Date().toISOString()
      })
    }
    toast.success('Promoção enviada! Acompanhe o status em Minhas promoções.')
    Object.assign(form, { title: '', description: '', category: '', price: '', originalPrice: '' })
    touched.value = false
    await navigateTo('/loja')
  } catch (e: any) {
    toast.error(e?.data?.message || e?.message || 'Falha ao cadastrar promoção')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-2xl">
    <PageHeader
      eyebrow="Nova oferta"
      title="Cadastrar promoção"
      subtitle="Publique uma oferta da sua loja. Ela será validada antes de entrar no catálogo."
    />

    <div class="card mb-5 flex items-center gap-3 p-4">
      <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-pine-800 text-acid-300">
        <Icon name="store" :size="20" />
      </div>
      <div class="min-w-0 flex-1">
        <p class="text-xs font-medium uppercase tracking-wider text-ink-400">Publicando como</p>
        <p class="truncate font-semibold text-ink-900">
          {{ user.loja.name }}
          <span class="font-normal text-ink-400">· {{ user.loja.email }}</span>
        </p>
      </div>
    </div>

    <form class="card space-y-5 p-6" novalidate @submit.prevent="submit">
      <div>
        <label class="label">Título</label>
        <input v-model="form.title" class="input" placeholder="Ex.: Notebook Gamer 20% OFF" />
        <p v-if="touched && errors.title" class="mt-1 text-xs text-rose-600">{{ errors.title }}</p>
      </div>

      <div>
        <label class="label">Descrição</label>
        <textarea
          v-model="form.description"
          rows="3"
          class="input resize-none"
          placeholder="Detalhe a oferta"
        />
        <p v-if="touched && errors.description" class="mt-1 text-xs text-rose-600">
          {{ errors.description }}
        </p>
      </div>

      <div>
        <label class="label">Categoria</label>
        <input
          v-model="form.category"
          class="input"
          list="categorias"
          placeholder="eletronicos"
        />
        <datalist id="categorias">
          <option v-for="c in store.categories" :key="c" :value="c" />
        </datalist>
        <p v-if="touched && errors.category" class="mt-1 text-xs text-rose-600">
          {{ errors.category }}
        </p>
      </div>

      <div class="grid gap-4 sm:grid-cols-2">
        <div>
          <label class="label">Preço (R$)</label>
          <input
            v-model="form.price"
            type="number"
            step="0.01"
            min="0"
            class="input nums"
            placeholder="999.90"
          />
          <p v-if="touched && errors.price" class="mt-1 text-xs text-rose-600">
            {{ errors.price }}
          </p>
        </div>
        <div>
          <label class="label">Preço original (R$)</label>
          <input
            v-model="form.originalPrice"
            type="number"
            step="0.01"
            min="0"
            class="input nums"
            placeholder="1299.90"
          />
          <p v-if="touched && errors.originalPrice" class="mt-1 text-xs text-rose-600">
            {{ errors.originalPrice }}
          </p>
        </div>
      </div>

      <div class="flex flex-wrap items-center justify-end gap-3 border-t border-bone-200 pt-5">
        <span class="mr-auto text-xs text-ink-400">A oferta será validada antes de publicar.</span>
        <button type="submit" class="btn-accent" :disabled="submitting">
          <span v-if="submitting" class="h-4 w-4 animate-spin rounded-full border-2 border-pine-900/30 border-t-pine-900" />
          <Icon v-else name="plus" :size="16" :stroke-width="2.25" />
          {{ submitting ? 'Enviando…' : 'Publicar promoção' }}
        </button>
      </div>
    </form>
  </div>
</template>
