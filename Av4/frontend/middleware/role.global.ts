import { useUserStore } from '~/stores/user'

const CLIENTE_PAGES = ['/', '/hot-deals', '/interesses']
const LOJA_PAGES = ['/loja', '/cadastro']

/**
 * Mantém cada papel nas suas próprias páginas. Quando não há papel definido,
 * a tela de entrada (WelcomeScreen, em app.vue) assume o controle.
 */
export default defineNuxtRouteMiddleware((to) => {
  if (import.meta.server) return

  const user = useUserStore()
  // Garante o papel persistido mesmo se o middleware rodar antes do mount.
  if (!user.role) user.hydrate()
  if (!user.role) return

  if (user.role === 'loja' && CLIENTE_PAGES.includes(to.path)) return navigateTo('/loja')
  if (user.role === 'cliente' && LOJA_PAGES.includes(to.path)) return navigateTo('/')
})
