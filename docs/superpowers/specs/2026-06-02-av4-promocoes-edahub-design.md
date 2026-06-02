# Av4 — Plataforma Distribuída de Promoções (EDA + GraphQL + SSE)

Data: 2026-06-02
Autores: Matheus Vinicius Passos de Santana, Lucas Yukio Fukuda Matsumoto

## Objetivo

Plataforma web onde lojas cadastram promoções, consumidores consultam/votam/seguem
categorias, promoções populares viram "hot deals", notificações chegam em tempo real
via SSE e lojas recebem e-mails. Toda comunicação entre microsserviços ocorre
**exclusivamente via RabbitMQ** — nenhuma chamada direta entre serviços.

Av4 é a evolução web do `Trab1` (CLI Node.js já existente neste repositório), reusando
o modelo de eventos assinados em RSA, mas reescrito em Java/Spring Boot com API GraphQL,
SSE, bancos por serviço e Docker Compose.

## Decisões técnicas (com justificativa para a defesa)

1. **Backend Java 21 + Spring Boot** — cumpre o requisito "frontend em linguagem
   diferente do backend" (frontend é React/TypeScript).
2. **GraphQL puro** (Spring for GraphQL + Apollo Client) — a pedido do autor. Diverge do
   "REST" sugerido no enunciado; divergência documentada. As ações do enunciado
   (cadastrar, listar, votar, seguir/cancelar categoria) viram queries/mutations.
3. **Subscriptions GraphQL transportadas via SSE** (`graphql-sse`) — mantém GraphQL puro
   E satisfaz o requisito explícito de notificações em tempo real via SSE.
4. **1 PostgreSQL com 4 bancos lógicos** (`gateway_db`, `promocao_db`, `ranking_db`,
   `notificacao_db`) — cumpre "não compartilhar banco" sem o peso de 4 containers.
5. **Resend real** — requer `RESEND_API_KEY`. Sem a chave, o envio de e-mail falha e é
   logado, mas o restante do fluxo (eventos, SSE) continua.
6. **Assinatura RSA-2048 + SHA-256**, canonical JSON determinístico, anti-replay via
   `eventId` único + `timestamp` (janela de 5 min).
7. **Sem código compartilhado entre serviços** — cada microsserviço é standalone
   (pequena duplicação utilitária de envelope/assinatura) para independência real.
8. **Limiar de hot deal = 5** (configurável via `HOT_DEAL_THRESHOLD`).
9. **Sem autenticação real** — `consumerId`/`lojaId` são identificadores simples
   fornecidos pelo frontend (escopo acadêmico).

## Arquitetura

- **Frontend** (React+TS): fala só com o Gateway via GraphQL HTTP + subscriptions SSE.
- **Gateway** (Spring Boot): expõe GraphQL, mantém conexões SSE, traduz ações em eventos
  RabbitMQ, consome notificações e filtra por interesse de cada usuário. Mantém estado de
  lojas (com par de chaves) e interesses por categoria em `gateway_db`.
- **MS Promoção**: consome `promocao.recebida`, valida assinatura + anti-replay, persiste,
  publica `promocao.publicada`.
- **MS Ranking**: consome `promocao.voto`, valida, atualiza score, ao atingir o limiar
  publica `promocao.destaque`.
- **MS Notificação**: consome `promocao.publicada` e `promocao.destaque`, valida, envia
  e-mail (Resend) à loja e publica `promocao.categoria` / `notificacao.hotdeal` para o
  Gateway (SSE).
- **RabbitMQ**: dois topic exchanges — `promocoes.events` (eventos de domínio) e
  `promocoes.notificacoes` (notificações destinadas ao Gateway).

## Eventos (envelope assinado)

```jsonc
{
  "eventId": "uuid-v4",
  "eventType": "promocao.recebida",
  "producer": "loja:<id> | gateway | promocao | ranking | notificacao",
  "timestamp": "ISO-8601 UTC",
  "version": 1,
  "payload": { ... },
  "signature": "base64(RSA-SHA256(canonicalJSON(envelope sem signature)))"
}
```

| Evento | Exchange | Produtor → Consumidor | Assinado por |
|---|---|---|---|
| `promocao.recebida`  | events        | Gateway → Promoção     | loja |
| `promocao.publicada` | events        | Promoção → Notificação | promocao |
| `promocao.voto`      | events        | Gateway → Ranking      | gateway |
| `promocao.destaque`  | events        | Ranking → Notificação  | ranking |
| `promocao.categoria` | notificacoes  | Notificação → Gateway  | notificacao |
| `notificacao.hotdeal`| notificacoes  | Notificação → Gateway  | notificacao |

Anti-replay: cada serviço grava `eventId` processado na tabela `Evento` e rejeita
duplicatas e timestamps fora da janela.

## Contrato GraphQL (Gateway)

Queries: `promocoes(categoria, apenasHot)`, `promocao(id)`, `categorias`,
`minhasCategorias(consumerId)`.
Mutations: `registrarLoja`, `cadastrarPromocao`, `votar`, `seguirCategoria`,
`deixarCategoria`.
Subscription: `notificacoes(consumerId)` (transporte SSE).

Tipos: `Promocao`, `Loja`, `Notificacao`, `VotoResult`, enum `TipoNotificacao`.

## Bancos de dados (1 Postgres, 4 DBs)

- **gateway_db**: `loja` (id, nome, email, public_key, private_key), `interesse`
  (consumer_id, categoria).
- **promocao_db**: `promocao` (id, titulo, descricao, categoria, preco, preco_original,
  loja_id, loja_email, status, criada_em), `loja_chave` (loja_id, public_key),
  `evento` (event_id, processado_em).
- **ranking_db**: `voto` (id, promocao_id, consumer_id, valor), `score` (promocao_id,
  total, hot), `evento`.
- **notificacao_db**: `notificacao` (id, tipo, titulo, mensagem, promocao_id, categoria,
  loja_email, criada_em), `evento`.

## Segurança / chaves

- RSA-2048. Pares dos serviços gerados por um container `keygen` no boot, gravados num
  volume `keys/`. Públicas distribuídas a quem verifica.
- Par da loja gerado no `registrarLoja` (Gateway), privada guardada em `gateway_db`,
  pública publicada para o MS Promoção (via evento `promocao.recebida` carregando a
  pública na primeira vez OU registro prévio — usaremos: pública embarcada no payload do
  primeiro `promocao.recebida` e persistida em `promocao_db.loja_chave`; assinatura
  verificada contra a pública registrada).

## Estrutura de pastas

```
Av4/
├── docker-compose.yml
├── .env.example
├── README.md
├── docs/{arquitetura,eventos,payloads,diagramas}.md
├── infra/{postgres/init.sql, rabbitmq/definitions.json, keygen/}
├── keys/                         (volume compartilhado)
├── frontend/                     (React+TS+Vite+Apollo+graphql-sse)
└── services/{gateway,promocao,ranking,notificacao}/   (Spring Boot standalone)
```

## Entregáveis

Código completo (frontend + 4 serviços), config RabbitMQ, init dos bancos, Docker
Compose, docs de arquitetura/eventos, instruções de execução, exemplos de payloads,
diagramas mermaid.

## Critérios de aceitação

- Subir tudo com `docker compose up` e abrir o frontend.
- Cadastrar promoção → e-mail à loja + notificação SSE a quem segue a categoria.
- Votar até o limiar → evento de destaque → e-mail "hot deal" + SSE.
- Seguir/cancelar categoria altera o que chega via SSE.
- Nenhuma chamada direta entre serviços (só RabbitMQ).
- Eventos com assinatura inválida são rejeitados.
