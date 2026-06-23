# Av5 — Raft com gRPC, Protocol Buffers, Persistência e Recuperação de Falhas

**Disciplina:** Sistemas Distribuídos — Profa. Ana Cristina Barreiras Kochem Vendramin
**Avaliação 5 (valor 20)**

## Objetivo

Evoluir a implementação do protocolo Raft da Av3 (que usava Pyro5) para uma
versão baseada em **gRPC + Protocol Buffers**, incorporando **persistência de
estado**, **recuperação de falhas**, **sincronização incremental de réplicas** e
**interoperabilidade entre linguagens** (servidores e cliente em linguagens
diferentes).

## Decisões de projeto (confirmadas)

| Item | Decisão |
|------|---------|
| Linguagem dos 4 nós Raft | **Python** (evolui a lógica da Av3) |
| Linguagem do cliente | **Go** (linguagem diferente → demonstra interoperabilidade gRPC) |
| Transporte | **gRPC** exclusivamente; todas as mensagens via `.proto` |
| Persistência | **Arquivo JSON por nó** (`data/nodeN.json`), escrita atômica |
| Execução / demo | **Docker Compose** completo (nós + cliente) |
| Modelo de aplicação | **Key–value store replicado** (`Publish(key,value)`, `Consume(key)`) |
| Quórum | **Fixo: 3 de 4** (`4//2 + 1`), independente de nós acessíveis |
| Descoberta do líder | **Apenas via respostas dos nós** (sem Name Server) |

## Arquitetura

```
            ┌─────────── Docker Compose ───────────┐
            │                                       │
  Go client │   node1   node2   node3   node4       │
   (gRPC) ──┼──►(py)    (py)    (py)    (py)         │
            │     ▲       ▲       ▲       ▲          │
            │     └───────┴───────┴───────┘          │
            │         RaftService (interno)          │
            └───────────────────────────────────────┘
```

Cada nó executa **um único servidor gRPC** que hospeda **dois serviços
distintos**:

1. **`RaftService`** — RPCs internos nó↔nó. O cliente **não** tem acesso.
   - `RequestVote`
   - `AppendEntries`
2. **`ClientService`** — operações da aplicação, expostas ao cliente.
   - `Publish` (escrita)
   - `Consume` (leitura)

A separação em dois serviços é o mecanismo que garante o requisito *"não será
permitido ao cliente utilizar chamadas internas do protocolo Raft"*: o cliente
Go só conhece e só pode invocar `ClientService`.

### Endereçamento

| Nó | Hostname (compose) | Porta gRPC |
|----|--------------------|------------|
| 1  | `node1`            | 6001       |
| 2  | `node2`            | 6002       |
| 3  | `node3`            | 6003       |
| 4  | `node4`            | 6004       |

Ambos os serviços (`RaftService` e `ClientService`) são servidos na **mesma
porta** de cada nó.

## Definições Protocol Buffers (`proto/raft.proto`)

```proto
syntax = "proto3";
package raft;

// ---------- Aplicação (cliente) ----------
service ClientService {
  rpc Publish (PublishRequest) returns (PublishReply);
  rpc Consume (ConsumeRequest) returns (ConsumeReply);
}

message PublishRequest { string key = 1; string value = 2; }
message PublishReply {
  bool   success      = 1;  // true = efetivado (committed) com sucesso
  string leader_hint  = 2;  // endereço do líder atual se este nó não for líder
  int64  index        = 3;  // índice atribuído à entrada
  string message      = 4;  // motivo: "not_leader" | "no_quorum" | "ok"
}

message ConsumeRequest { string key = 1; }     // key vazia = todos os pares
message ConsumeReply {
  bool             success     = 1;
  repeated DataItem items      = 2;  // SOMENTE entradas committed
  string           leader_hint = 3;
  bool             is_leader   = 4;  // este nó respondeu como líder?
  int64            committed_index = 5; // limite de commit deste nó
  int64            pending_count   = 6; // nº de entradas replicadas porém uncommitted (metadado)
}
message DataItem { string key = 1; string value = 2; int64 index = 3; }

// ---------- Raft (interno) ----------
service RaftService {
  rpc RequestVote   (RequestVoteArgs)   returns (RequestVoteReply);
  rpc AppendEntries (AppendEntriesArgs) returns (AppendEntriesReply);
}

message LogEntry { int64 term = 1; int64 index = 2; string key = 3; string value = 4; }

message RequestVoteArgs {
  int64 term = 1; int32 candidate_id = 2;
  int64 last_log_index = 3; int64 last_log_term = 4;
}
message RequestVoteReply { int64 term = 1; bool vote_granted = 2; }

message AppendEntriesArgs {
  int64 term = 1; int32 leader_id = 2;
  int64 prev_log_index = 3; int64 prev_log_term = 4;
  repeated LogEntry entries = 5;
  int64 leader_commit = 6;
}
message AppendEntriesReply {
  int64 term = 1;
  bool  success = 2;
  int64 conflict_index = 3;  // dica p/ o líder localizar o último trecho consistente
}
```

## Descoberta do líder e redirecionamento (cliente Go)

O cliente é configurado com a lista dos 4 endereços, mas **não sabe** quem é o
líder.

1. Escolhe um nó (cache do último líder conhecido, senão round-robin) e envia
   `Publish`/`Consume`.
2. Se o nó **não** for líder, responde `success=false` + `leader_hint` (o
   endereço do líder, derivado do estado Raft daquele nó).
3. O cliente reconecta no `leader_hint` e repete a requisição; passa a usar esse
   endereço como cache.
4. Se um nó está inacessível, tenta o próximo da lista.
5. A identidade do líder vem **exclusivamente** das respostas dos nós (sem Name
   Server, diferente da Av3).

## Eleição

Reaproveita a lógica da Av3, adaptada para gRPC:

- Cada nó inicia como **seguidor** com `election_timeout` aleatório (faixa, ex.
  3,0–6,0 s).
- Timeout expira → vira **candidato**, incrementa `term`, vota em si, chama
  `RequestVote` nos peers em paralelo.
- Cada nó vota **uma vez por termo** (`voted_for` persistido).
- Voto só é concedido se o log do candidato estiver **tão ou mais atualizado**
  (compara `last_log_term`, depois `last_log_index`).
- Maioria (**≥3**) → torna-se líder; passa a enviar heartbeats periódicos.
- Ausência de heartbeat → novo timeout → nova eleição.

## AppendEntries — Heartbeat e Replicação

- Líder mantém, por réplica, **`next_index`** e **`match_index`**.
- `AppendEntries` envia apenas `log[next_index:]` daquela réplica — **nunca a
  base inteira**. Heartbeat é o mesmo RPC; se a réplica está atrasada, o
  "heartbeat" já carrega as entradas que faltam → réplica recupera mesmo **sem
  novas escritas**.
- Réplica rejeita (`success=false`) quando `prev_log_index`/`prev_log_term` não
  batem com seu log local, retornando **`conflict_index`** para o líder
  retroceder e reenviar **apenas** o trecho ausente.
- Heartbeats sempre recebem resposta das réplicas.
- **Quórum fixo:** uma entrada `N` é efetivada (committed) somente quando
  `match_index ≥ N` em **≥3 nós** (incluindo o líder) **e** `log[N].term ==
  current_term`. Nunca reduz o quórum por indisponibilidade.
- Sem quórum → escrita **rejeitada ou pendente** até restabelecer.
- Após efetivar, líder avança `commit_index`, **aplica** a entrada, responde ao
  cliente `success=true`, e propaga `commit_index` via `leader_commit` nas
  próximas mensagens AppendEntries (inclusive heartbeats).
- Seguidores só aplicam/disponibilizam entradas até `min(leader_commit,
  últimoÍndiceLocal)`.

## Operações de Leitura (`Consume`)

- Atendida pelo **líder** e pelas **réplicas**.
- Retorna **somente** entradas com `index ≤ commit_index` (committed).
- `ConsumeReply` inclui `committed_index` e `pending_count` (nº de entradas
  replicadas porém uncommitted) como **metadados** para evidenciar a distinção
  entre *replicado-uncommitted* e *efetivado* — sem expor o conteúdo
  uncommitted.
- Como as réplicas só avançam `commit_index` via `leader_commit`, elas só
  expõem dados efetivamente confirmados.

## Persistência de Estado

Arquivo JSON por nó (`data/nodeN.json`), escrita **atômica** (arquivo temporário
+ `rename`):

```json
{
  "current_term": 0,
  "voted_for": null,
  "commit_index": 1,
  "log": [
    { "term": 1, "index": 1, "key": "x", "value": "1" }
  ]
}
```

Contém, no mínimo:
- **termo corrente** e **índice corrente** (derivado do log / `commit_index`);
- **ID do último voto** (`voted_for`);
- **dados intermediários (uncommitted)** — entradas com `index > commit_index`;
- **dados finais (committed)** — entradas com `index ≤ commit_index`.

Persiste a cada mudança de: termo, voto, append/truncamento de log, avanço de
commit. `commit_index` é persistido porque o enunciado exige persistir dados
committed (vai além do Raft canônico, que persiste apenas term/votedFor/log).

## Recuperação de Nós e Reintegração

Ao reiniciar após falha/desligamento, o nó:
1. **Carrega** `data/nodeN.json` (se existir) e restaura `current_term`,
   `voted_for`, `log`, `commit_index`.
2. Inicia como **seguidor**.
3. **Identifica o líder corrente** ao receber o primeiro `AppendEntries`
   (heartbeat) e passa a participar normalmente.
4. Se estiver atrasado, o líder o detecta via `next_index`/`conflict_index` e o
   sincroniza **incrementalmente**.

## Modelo de concorrência (servidor Python)

- `grpc.server` com `ThreadPoolExecutor`.
- Uma thread de **ticker** em background: trata timeout de eleição (seguidor/
  candidato) e envio de heartbeats (líder).
- `threading.RLock` protege o estado compartilhado (espelha a Av3).

## Estrutura do repositório

```
Av5/
  proto/
    raft.proto
  server/                  # Python (4 nós)
    raft_node.py           # máquina de estados Raft
    server.py              # servidor gRPC: RaftService + ClientService
    persistence.py         # load/save JSON atômico
    config.py              # mapa node_id -> host:porta, timeouts
    run_node.py            # entrypoint (--id)
    gen/                   # stubs gerados do .proto (committed)
    requirements.txt
    Dockerfile
  client/                  # Go (cliente)
    main.go                # CLI: publish / consume / interativo
    discovery.go           # descoberta de líder + retry/redirect
    gen/                   # stubs gerados do .proto (committed)
    go.mod / go.sum
    Dockerfile
  scripts/
    gen-proto.sh           # regenera stubs Python e Go
  docker-compose.yml
  README.md                # os 5 cenários de demonstração, passo a passo
```

Os stubs gerados são **committed** no repositório para garantir build/demo
confiáveis; `scripts/gen-proto.sh` permite regenerá-los.

## Cenários de demonstração (cobertos pelo README)

1. **Operação Normal** — sobe 4 nós → eleição → `Publish` → replicação →
   `Consume`.
2. **Falha do Líder** — `stop` no líder → nova eleição → continuidade de
   publish/consume.
3. **Persistência** — `stop` em um nó → restart → recupera estado persistido.
4. **Recuperação de Réplica** — `stop` em réplica → novas escritas → restart →
   sincronização **apenas das entradas ausentes** (verificável nos logs do
   líder via `next_index`/`conflict_index`).
5. **Consistência de Leitura** — `Consume` no líder e em réplicas → apenas dados
   committed retornados; `pending_count` evidencia entradas uncommitted.

## Fora de escopo (YAGNI)

- Snapshotting / compactação de log.
- Mudança dinâmica de membros do cluster (cluster fixo de 4).
- TLS/autenticação entre nós.
- Reordenação/otimização do conteúdo do `Consume` além de chave única.
