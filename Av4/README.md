# Av4 — Plataforma Distribuída de Promoções (Java + Nuxt)

Migração do projeto **Trab1** (microsserviços em Node.js) para uma stack profissional:
**backend 100% Java (Spring Boot)** e **frontend 100% JavaScript (Nuxt 3 / Vue 3)**.
Preserva os mesmos fluxos, eventos, exchanges/filas, regras de negócio e o modelo de
assinatura digital RSA — agora reescritos em Java, orientados a eventos via RabbitMQ.

Alunos: Matheus Vinicius Passos de Santana · Lucas Yukio Fukuda Matsumoto

> Linguagens diferentes: **frontend Vue 3 / Nuxt 3 (TS)** ≠ **backend Java 21 / Spring Boot**.

## Arquitetura

```
                          REST + SSE (EventSource)
   ┌──────────────┐  ◄───────────────────────────►  ┌──────────────────────────────┐
   │  Nuxt 3/Vue  │                                   │      MS Gateway / API (8080)  │
   │  (frontend)  │                                   │ Spring Web · SSE · catálogo   │
   └──────────────┘                                   └───────────────┬──────────────┘
                                                        publica/consome (RabbitMQ)
                                                                       │
       ┌───────────────────────── RabbitMQ topic exchanges ───────────┴───────────────┐
       │   promocoes.events  (domínio)        promocoes.notificacoes  (p/ o Gateway)   │
       └─────┬───────────────┬───────────────────────────────────────┬────────────────┘
             │               │                                        │
    promocao.recebida   promocao.voto                       promocao.categoria.<cat>
             ▼               ▼                                        ▲
   ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────────────────────────┐
   │ MS Promoção  │  │  MS Ranking  │  │              MS Notificação                  │
   │   (8082)     │  │   (8083)     │  │   (8084)  e-mail (Resend) + notifica Gateway  │
   └──────┬───────┘  └──────┬───────┘  └────────────────────▲────────────────────────┘
          │ promocao.publicada     promocao.destaque         │
          └──────────────────────────────────────────────────┘
```

- **Comunicação entre microsserviços exclusivamente via RabbitMQ** — nenhuma chamada HTTP interna.
- **O frontend só fala com o Gateway** (REST + SSE), nunca com os demais serviços.
- **Todo evento é assinado (RSA SHA256withRSA)** e **verificado** no consumo; assinatura inválida é rejeitada.
- **EDA**: produtores/consumidores desacoplados por *topic exchanges*.

### Módulos (Maven multi-módulo)

| Módulo | Porta | Consome | Publica | Banco |
|---|---|---|---|---|
| **shared-lib** | — | — | — | modelo de evento, RSA (KeyLoader/SignatureService/EventSigner/EventVerifier), config RabbitMQ |
| **gateway-service** | 8080 | `promocao.publicada`, `promocao.destaque`, `promocao.categoria.#` | `promocao.recebida`, `promocao.voto` | gateway_db |
| **promocao-service** | 8082 | `promocao.recebida` | `promocao.publicada` | promocao_db |
| **ranking-service** | 8083 | `promocao.voto` | `promocao.destaque` | ranking_db |
| **notificacao-service** | 8084 | `promocao.publicada`, `promocao.destaque` | `promocao.categoria.<cat>` | notificacao_db |

## Estrutura de pastas

```
Av4/
├── README.md  ·  .env.example  ·  docs/payloads.md
├── keys/                         (pares RSA gerados; volume compartilhado)
├── scripts/generate-keys.sh
├── backend/
│   ├── pom.xml                   (parent / agregador Maven)
│   ├── Dockerfile                (parametrizado por SERVICE)
│   ├── docker-compose.yml
│   ├── infra/postgres/init.sql
│   ├── shared-lib/               (event/ signature/ messaging/)
│   ├── gateway-service/          (controller/ service/ consumer/ config/ domain/ repository/ dto/)
│   ├── promocao-service/
│   ├── ranking-service/
│   └── notificacao-service/
└── frontend/                     (Nuxt 3: app.vue, pages/, components/, composables/, stores/, services/)
```

## Como rodar

### Opção A — Tudo no Docker (recomendado)

```bash
cd Av4/backend
cp ../.env.example .env        # opcional (defaults já funcionam; sem RESEND_API_KEY o e-mail vai p/ mock)
docker compose up --build
```
Sobe RabbitMQ, PostgreSQL (4 bancos), gera as chaves RSA (serviço `keygen`), os 4 microsserviços e o frontend.

- Frontend: http://localhost:3000
- Gateway API: http://localhost:8080/api
- RabbitMQ UI: http://localhost:15672 (guest/guest)

### Opção B — Local (sem Docker, usando H2)

```bash
# 1. RabbitMQ
docker run -d --name rabbit -p 5672:5672 -p 15672:15672 rabbitmq:3-management

# 2. Chaves RSA
cd Av4 && bash scripts/generate-keys.sh

# 3. Backend (cada serviço em um terminal, a partir do módulo)
cd Av4/backend && mvn -q -DskipTests install
cd gateway-service     && KEYS_DIR=../../keys mvn spring-boot:run
cd ../promocao-service && KEYS_DIR=../../keys mvn spring-boot:run
cd ../ranking-service  && KEYS_DIR=../../keys mvn spring-boot:run
cd ../notificacao-service && KEYS_DIR=../../keys mvn spring-boot:run

# 4. Frontend
cd Av4/frontend && npm install && npm run dev   # http://localhost:3000
```
Em modo local os serviços usam **H2** (arquivo em `./data/`). Para PostgreSQL, defina as
variáveis `DB_*` (ver `.env.example`).

## API REST do Gateway

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/health` | status |
| GET | `/api/categorias` | `{categories:[...]}` |
| POST | `/api/promocoes` | cadastrar promoção (loja) → 202 `{promotionId,eventId}` |
| GET | `/api/promocoes?category=&hot=` | `{count, promotions:[...]}` |
| POST | `/api/promocoes/{id}/voto` | `{vote:1\|-1, consumerId}` → 202 |
| POST | `/api/interesses` | `{consumerId, category}` |
| DELETE | `/api/interesses` | `{consumerId, category}` |
| GET | `/api/interesses?consumerId=` | `{consumerId, interests:[...]}` |
| GET | `/api/notificacoes/stream?consumerId=` | **SSE** (EventSource) |
| GET | `/api/notificacoes?consumerId=&since=` | polling das notificações bufferizadas |

### SSE (frontend)

```js
const es = new EventSource('http://localhost:8080/api/notificacoes/stream?consumerId=cliente_a')
es.addEventListener('notificacao', (e) => console.log(JSON.parse(e.data)))
```
Teste rápido: `curl -N "http://localhost:8080/api/notificacoes/stream?consumerId=cliente_a"`

## Variáveis de ambiente

| Variável | Default | Descrição |
|---|---|---|
| `RABBITMQ_HOST/PORT/USER/PASS` | `localhost/5672/guest/guest` | conexão RabbitMQ |
| `DB_URL/DB_USER/DB_PASS/DB_DRIVER/DB_DIALECT` | H2 file | datasource (PostgreSQL no compose) |
| `HOT_DEAL_THRESHOLD` | `5` | score (positivos−negativos) p/ virar hot deal |
| `KEYS_DIR` | `../../keys` (local) / `/keys` (docker) | diretório das chaves RSA |
| `EMAIL_PROVIDER` | `resend` | `resend` (real) ou qualquer outro = mock |
| `RESEND_API_KEY` | _(vazio)_ | chave Resend; sem ela → mock (loga) |
| `EMAIL_FROM` | `Promocoes <onboarding@resend.dev>` | remetente |
| `NUXT_PUBLIC_GATEWAY_URL` | `http://localhost:8080` | URL do Gateway no frontend |

## Modelo de eventos e exemplos

Envelope padrão (assinado, exceto o campo `signature`):

```json
{ "eventId":"uuid", "type":"promocao.recebida", "timestamp":"ISO", "source":"gateway",
  "signature":"base64", "payload":{ } }
```

Exemplos completos de cada payload em [`docs/payloads.md`](docs/payloads.md).

## Assinatura digital (RSA)

Migrada do Node para Java em `shared-lib`:
- `KeyLoader` — carrega PEM (PKCS#8 privada / X.509 pública) do diretório de chaves.
- `SignatureService` — `SHA256withRSA`, saída Base64.
- `EventSigner` / `EventVerifier` — assinam/verificam o **JSON canônico** do envelope
  (`CanonicalJson`): chaves ordenadas e números normalizados, garantindo bytes idênticos
  entre quem assina (POJO) e quem verifica (mapa desserializado). Eventos com assinatura
  inválida são **rejeitados e logados**.

## Estratégia de reaproveitamento do Trab1

1. **Mapeamento** do projeto Node: exchanges (`promocoes.events`, `promocoes.notificacoes`),
   routing keys (`promocao.recebida/publicada/voto/destaque/categoria`), filas por serviço,
   envelope de evento e a lógica RSA (canonicalização determinística + SHA256).
2. **Preservação de contrato**: mesmos nomes de eventos, exchanges e filas → compatibilidade lógica.
3. **Reescrita por serviço**, mantendo as responsabilidades e o fluxo idênticos:
   Gateway (REST+SSE+publish/consume), Promoção (valida+publica), Ranking (score+hot deal),
   Notificação (e-mail+categoria).
4. **Profissionalização**: Spring Boot, JPA (entities/repositories/DTOs), Lombok, Bean
   Validation, multi-módulo Maven com `shared-lib`, Docker Compose, PostgreSQL.

O `Trab1/` original permanece intacto no repositório como referência.
