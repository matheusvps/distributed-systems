import { useUserStore } from '~/stores/user'

const CLIENTE_PAGES = ['/', '/hot-deals', '/interesses']
const LOJA_PAGES = ['/loja', '/cadastro']

export default defineNuxtRouteMiddleware((to) => {
  if (import.meta.server) return

  const user = useUserStore()
  if (!user.role) user.hydrate()
  if (!user.role) return

  if (user.role === 'loja' && CLIENTE_PAGES.includes(to.path)) return navigateTo('/loja')
  if (user.role === 'cliente' && LOJA_PAGES.includes(to.path)) return navigateTo('/')
})
