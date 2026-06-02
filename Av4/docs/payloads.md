# Exemplos de payloads de eventos (Av4 — Java)

Todos os eventos usam o mesmo envelope. A assinatura (`SHA256withRSA`, Base64) cobre o
JSON canônico de todos os campos **exceto** `signature` (chaves ordenadas, números
normalizados — ver `shared-lib/.../CanonicalJson.java`).

## Envelope

```json
{
  "eventId": "uuid-v4",
  "type": "promocao.recebida",
  "timestamp": "2026-06-02T19:00:00.000Z",
  "source": "gateway",
  "signature": "base64(RSA-SHA256(canonicalJSON(envelope sem signature)))",
  "payload": { }
}
```

## Tabela de eventos

| Evento (`type`) | Exchange | Produtor → Consumidor | Assinado por (`source`) |
|---|---|---|---|
| `promocao.recebida`        | promocoes.events        | Gateway → Promoção     | gateway |
| `promocao.publicada`       | promocoes.events        | Promoção → Gateway/Notificação | promocao |
| `promocao.voto`            | promocoes.events        | Gateway → Ranking      | gateway |
| `promocao.destaque`        | promocoes.events        | Ranking → Notificação/Gateway | ranking |
| `promocao.categoria.<cat>` | promocoes.notificacoes  | Notificação → Gateway  | notificacao |

## promocao.recebida (payload)

```json
{
  "id": "9b1d...",
  "title": "Monitor 4K",
  "description": "27 polegadas",
  "category": "eletronico",
  "price": 1499.90,
  "originalPrice": 2299.90,
  "store": "TechStore",
  "storeEmail": "loja@techstore.com",
  "createdAt": "2026-06-02T19:00:00.000Z"
}
```

## promocao.publicada (payload)

```json
{
  "id": "9b1d...", "title": "Monitor 4K", "category": "eletronico",
  "price": 1499.90, "originalPrice": 2299.90, "store": "TechStore",
  "storeEmail": "loja@techstore.com", "status": "publicada",
  "validatedAt": "2026-06-02T19:00:01.000Z"
}
```

## promocao.voto (payload)

```json
{
  "promotionId": "9b1d...",
  "vote": 1,
  "consumerId": "cliente_a",
  "votedAt": "2026-06-02T19:01:00.000Z",
  "promotion": {
    "id": "9b1d...", "title": "Monitor 4K", "category": "eletronico",
    "store": "TechStore", "storeEmail": "loja@techstore.com", "price": 1499.90
  }
}
```

## promocao.destaque (payload)

```json
{
  "promotionId": "9b1d...", "score": 5, "positiveVotes": 5, "negativeVotes": 0,
  "category": "eletronico", "title": "Monitor 4K", "store": "TechStore",
  "storeEmail": "loja@techstore.com", "price": 1499.90,
  "tag": "hot deal", "highlightedAt": "2026-06-02T19:05:00.000Z"
}
```

## promocao.categoria.<categoria> (payload — exchange de notificações)

Aprovação (nova promoção):
```json
{ "type": "categoria", "message": "Nova promocao publicada",
  "promotionId": "9b1d...", "title": "Monitor 4K", "category": "eletronico",
  "price": 1499.90, "store": "TechStore" }
```

Hot deal:
```json
{ "type": "hotdeal", "message": "Promocao em destaque (hot deal)",
  "promotionId": "9b1d...", "title": "Monitor 4K", "category": "eletronico",
  "score": 5, "store": "TechStore", "tag": "hot deal" }
```

O Gateway repassa esse payload (acrescido de `seq` e `at`) ao frontend via SSE
(evento `notificacao`), filtrando pelos consumidores que seguem a categoria.
