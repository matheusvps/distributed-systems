export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },
  modules: ['@nuxtjs/tailwindcss', '@pinia/nuxt'],
  css: ['~/assets/css/main.css'],
  runtimeConfig: {
    public: {
      gatewayUrl: process.env.NUXT_PUBLIC_GATEWAY_URL || 'http://localhost:8080'
    }
  },
  app: {
    head: {
      title: 'Mercado · Plataforma de Promoções',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'theme-color', content: '#153f2b' },
        { name: 'description', content: 'Plataforma distribuída de promoções em tempo real.' }
      ]
    }
  }
})
