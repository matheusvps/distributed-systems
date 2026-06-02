# Promoções — Frontend (Nuxt 3)

Frontend da plataforma distribuída de promoções (Av4). Fala apenas com o **Gateway**
via REST + SSE.

## Stack
Nuxt 3 · Vue 3 (`<script setup>`) · Pinia · Tailwind CSS · TypeScript · `EventSource` nativo.

## Configuração
Base URL do Gateway via `runtimeConfig.public.gatewayUrl` (padrão `http://localhost:8080`).
Override com a env var:

```bash
NUXT_PUBLIC_GATEWAY_URL=http://localhost:8080
```

## Rodar

```bash
npm install
npm run dev      # http://localhost:3000
npm run build && npm run preview
```

## Páginas
- `/` — lista de promoções, filtro por categoria, votação 👍/👎.
- `/hot-deals` — apenas ofertas em destaque.
- `/cadastro` — formulário de criação de promoção (loja).
- `/interesses` — seguir / deixar de seguir categorias.
- `/notificacoes` — feed em tempo real via SSE com indicador de conexão.

O `consumerId` ativo fica na sidebar (persistido em `localStorage`) e é usado por
votos, interesses e pelo stream SSE.
