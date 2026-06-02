# Av4 — Plataforma Distribuída de Promoções (EDA · Java + Nuxt)

Data: 2026-06-02 (revisado 2x)
Autores: Matheus Vinicius Passos de Santana, Lucas Yukio Fukuda Matsumoto

> **Histórico de revisão.** v1: Java/Spring + GraphQL + React. v2: Node + REST + Streamlit
> (reaproveitando o Trab1). **v3 (atual e implementada): backend 100% Java/Spring Boot +
> frontend 100% Nuxt 3/Vue 3, REST + SSE.** Migração do Trab1 (Node) preservando eventos,
> exchanges/filas, regras e assinatura RSA.

## Objetivo

Plataforma web: lojas cadastram promoções (assinadas), consumidores consultam/votam/seguem
categorias, promoções populares viram "hot deals", notificações em tempo real via SSE e
lojas recebem e-mail. Comunicação entre microsserviços **exclusivamente via RabbitMQ**.

## Stack

- **Backend**: Java 21, Spring Boot 3.3 (Web, AMQP, Data JPA, Validation), Maven multi-módulo,
  Lombok, Jackson. SSE via Spring MVC `SseEmitter`. RSA `SHA256withRSA`.
- **Frontend**: Nuxt 3, Vue 3 (Composition API), Pinia, Tailwind, `EventSource` nativo.
- **Infra**: RabbitMQ (2 topic exchanges), PostgreSQL (1 banco lógico por serviço; H2 local),
  Docker Compose, serviço `keygen` (OpenSSL) gerando o volume `keys/`.

## Decisões técnicas

1. **Maven multi-módulo** com `shared-lib` (envelope, RSA, constantes de mensageria, config
   Jackson/AMQP, `DomainEventPublisher`) reusada pelos 4 serviços.
2. **Gateway como ponto de entrada confiável**: assina `promocao.recebida` e `promocao.voto`
   em nome de loja/usuário; os MS verificam. Evita gerir par de chaves por loja no frontend.
3. **Chaves RSA em volume compartilhado** (`keys/`): cada serviço tem sua privada e lê
   qualquer pública para verificar (`KeyLoader` resolve `<source>.public.pem`).
4. **JSON canônico determinístico** (`CanonicalJson`): chaves ordenadas + números
   normalizados (`BigDecimal.stripTrailingZeros`), robusto ao round-trip POJO→wire→Map.
5. **Persistência por serviço** via JPA (entities/repositories/DTOs); H2 (file) local,
   PostgreSQL no compose (`gateway_db/promocao_db/ranking_db/notificacao_db`).
6. **SSE real** no Gateway (`/api/notificacoes/stream`, `EventSource`), filtrado por
   interesse de categoria + endpoint de polling de apoio.
7. **E-mail Resend (real)** via `HttpClient`; sem `RESEND_API_KEY` cai para mock (loga).
8. **Robustez de mensageria**: listener com `defaultRequeueRejected=false` (sem storm de
   poison messages) e mapper com `FAIL_ON_UNKNOWN_PROPERTIES=false`.
9. **Limiar de hot deal = 5** (`HOT_DEAL_THRESHOLD`); destaque idempotente (flag `hotPublished`).

## Eventos

Envelope: `{ eventId, type, timestamp, source, signature, payload }`. Exchanges
`promocoes.events` e `promocoes.notificacoes`. Eventos e payloads detalhados em
`Av4/docs/payloads.md`.

| Evento | Exchange | Produtor → Consumidor | source |
|---|---|---|---|
| `promocao.recebida`  | events       | Gateway → Promoção     | gateway |
| `promocao.publicada` | events       | Promoção → Gateway/Notificação | promocao |
| `promocao.voto`      | events       | Gateway → Ranking      | gateway |
| `promocao.destaque`  | events       | Ranking → Notificação/Gateway | ranking |
| `promocao.categoria.<cat>` | notificacoes | Notificação → Gateway | notificacao |

## Contrato REST (Gateway, 8080)

`GET /api/health`, `GET /api/categorias`, `POST /api/promocoes`,
`GET /api/promocoes?category=&hot=`, `POST /api/promocoes/{id}/voto`,
`POST /api/interesses`, `DELETE /api/interesses`, `GET /api/interesses?consumerId=`,
`GET /api/notificacoes/stream?consumerId=` (SSE), `GET /api/notificacoes?consumerId=&since=`.

## Estrutura

```
Av4/
├── keys/  ·  scripts/generate-keys.sh  ·  docs/payloads.md  ·  .env.example  ·  README.md
├── backend/  (pom.xml, Dockerfile, docker-compose.yml, infra/postgres/init.sql,
│              shared-lib/, gateway-service/, promocao-service/, ranking-service/, notificacao-service/)
└── frontend/ (Nuxt 3: app.vue, pages/, components/, composables/, stores/, services/)
```

## Critérios de aceitação (verificados)

- `docker compose up --build` sobe rabbit + postgres + keygen + 4 serviços + frontend.
- Cadastrar promoção → e-mail "aprovada" + notificação SSE a quem segue a categoria.
- Votar até o limiar → `promocao.destaque` → e-mail "hot deal" + SSE + catálogo `hot=true`.
- Seguir/cancelar categoria altera o que chega via SSE.
- Nenhuma chamada direta entre serviços (só RabbitMQ).
- Evento com assinatura inválida é rejeitado e logado.
