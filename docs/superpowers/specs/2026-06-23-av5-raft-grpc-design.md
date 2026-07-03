# Av5 — Raft com gRPC, Protocol Buffers, Persistência e Recuperação de Falhas

**Disciplina:** Sistemas Distribuídos — Profa. Ana Cristina Barreiras Kochem Vendramin  
**Avaliação 5 (valor 20)**

> **Fonte da verdade:** o enunciado oficial da avaliação (texto da professora).  
> Este documento é o **design interno** do repositório: descreve como a implementação
> em `Av5/` atende ao enunciado. Não acrescenta requisitos além dele.

## Objetivo

Evoluir a implementação do protocolo Raft da Av3 (Pyro5) para **gRPC + Protocol
Buffers**, incorporando **persistência**, **recuperação de falhas**,
**sincronização incremental de réplicas** e **interoperabilidade entre linguagens**.

## Requisitos do enunciado (mapeamento)

| Bloco | Pontos | Critério resumido |
|-------|--------|-------------------|
| Cliente externo e descoberta do líder | 3,0 | Cliente em outra linguagem; publish/consume sem saber o líder; redirect via resposta do nó; sem RPCs Raft |
| Eleição | 2,0 | Seguidor → candidato; um voto/termo; log atualizado; maioria; heartbeats; nova eleição sem heartbeat |
| Operações de leitura | 3,0 | Leitura no líder e réplicas; distinguir uncommitted vs committed; retornar **só** committed |
| AppendEntries | 5,0 | Replicação + heartbeat; sync incremental; quórum fixo (4 nós); commit propagado; OK ao cliente após commit |
| Persistência | 4,0 | termo, índice, último voto, log uncommitted + committed |
| Recuperação / reintegração | 3,0 | Carregar estado; voltar ao cluster; identificar líder |
| Demonstração | — | Cenários 1–5 (ver README e `scripts/demo-client.sh`) |

O enunciado **não** exige número de porta, listener único nem topologia Docker
específica — apenas gRPC, `.proto` e isolamento do cliente em relação ao Raft.

## Decisões de projeto (implementação)

| Item | Decisão |
|------|---------|
| Linguagem dos 4 nós Raft | **Python** (evolui a lógica da Av3) |
| Linguagem do cliente | **Go** |
| Transporte | **gRPC** exclusivamente; mensagens via `proto/raft.proto` |
| Isolamento cliente ↔ Raft | Dois **serviços** protobuf (`ClientService` / `RaftService`); cliente só invoca o primeiro |
| Rede Docker | Duas redes: `client` (cliente Go) e `raft` (nó↔nó) — cliente não alcança `RaftService` |
| Portas (convenção do repo) | `ClientService` em `nodeN:600N`; `RaftService` em `nodeN-raft:610N` |
| Servidores gRPC por nó | **Dois** `grpc.server` no mesmo processo (um por serviço/porta) |
| Persistência | JSON atômico em `data/nodeN/nodeN.json` |
| Execução / demo | Docker Compose + `scripts/run-scenarios.sh` + `scripts/demo-client.sh` |
| Modelo de aplicação | Key–value (`Publish`, `Consume`) |
| Quórum | **Fixo: 3 de 4** (`len(NODE_IDS) // 2 + 1`), independente de nós acessíveis |
| Descoberta do líder | Apenas `leader_hint` nas respostas (sem Name Server) |

## Arquitetura

```
┌──────────────── Docker Compose ─────────────────────────────────────┐
│                                                                      │
│  rede "client"                    rede "raft" (só entre nós)        │
│  ┌──────────┐                     ┌─────────────────────────────┐   │
│  │ Go client│──gRPC Publish/Consume│ node1:6001  node1-raft:6101 │   │
│  │          │    (ClientService)  │ node2:6002  node2-raft:6102 │   │
│  └──────────┘                     │ node3:6003  node3-raft:6103 │   │
│       │                           │ node4:6004  node4-raft:6104 │   │
│       │ (sem rota para 610N)      │      RequestVote /          │   │
│       │                           │      AppendEntries          │   │
│       └───────────────────────────┴─────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

Cada processo Python hospeda **dois serviços gRPC** definidos no mesmo `.proto`:

1. **`RaftService`** — `RequestVote`, `AppendEntries` (rede `raft` apenas).
2. **`ClientService`** — `Publish`, `Consume` (rede `client`; único acessível ao Go).

Isso atende *"não será permitido ao cliente utilizar chamadas internas do
protocolo Raft"*: o stub Go só gera cliente para `ClientService`, e a rede
Docker impede alcançar `610N` mesmo que alguém tentasse.

### Endereçamento (`server/config.py`)

| Nó | ClientService (cliente) | RaftService (interno) |
|----|-------------------------|------------------------|
| 1  | `node1:6001`            | `node1-raft:6101`      |
| 2  | `node2:6002`            | `node2-raft:6102`      |
| 3  | `node3:6003`            | `node3-raft:6103`      |
| 4  | `node4:6004`            | `node4-raft:6104`      |

Aliases de rede definidos em `docker-compose.yml` (`nodeN` na rede `client`,
`nodeN-raft` na rede `raft`).

## Definições Protocol Buffers (`proto/raft.proto`)

```proto
syntax = "proto3";
package raft;

service ClientService {
  rpc Publish (PublishRequest) returns (PublishReply);
  rpc Consume (ConsumeRequest) returns (ConsumeReply);
}

message PublishRequest { string key = 1; string value = 2; }
message PublishReply {
  bool   success      = 1;
  string leader_hint  = 2;
  int64  index        = 3;
  string message      = 4;  // "not_leader" | "no_quorum" | "ok"
}

message ConsumeRequest { string key = 1; }  // vazio = todos os pares committed
message ConsumeReply {
  bool              success                   = 1;
  repeated DataItem items                     = 2;  // SOMENTE committed
  string            leader_hint               = 3;
  bool              is_leader                 = 4;
  int64             committed_index           = 5;
  int64             pending_count             = 6;
  int64             pending_replicated_count  = 7;
  int64             pending_leader_only_count = 8;
}
message DataItem { string key = 1; string value = 2; int64 index = 3; }

service RaftService {
  rpc RequestVote   (RequestVoteArgs)   returns (RequestVoteReply);
  rpc AppendEntries (AppendEntriesArgs) returns (AppendEntriesReply);
}

message LogEntry { int64 term = 1; int64 index = 2; string key = 3; string value = 4; }
// ... RequestVote / AppendEntries (incl. conflict_index na rejeição)
```

`pending_*` são **metadados** para o cenário 5: distinguem replicado-uncommitted
de efetivado sem expor conteúdo uncommitted na lista `items`.

## Descoberta do líder (cliente Go — `client/discovery.go`)

1. Lista fixa `node1:6001` … `node4:6004`; não sabe quem é líder.
2. Tenta um nó (cache do último líder ou round-robin).
3. Se `not_leader`, usa `leader_hint` e redireciona.
4. Nó inacessível → próximo da lista.
5. Líder identificado **somente** pelas respostas dos nós.

## Eleição (`server/raft_node.py`)

- Seguidor com `election_timeout` aleatório (3,0–6,0 s).
- Timeout → candidato, `term++`, voto em si, `RequestVote` paralelo.
- Um voto por termo (`voted_for` persistido).
- Voto só se log do candidato ≥ local (`last_log_term`, depois `last_log_index`).
- **≥3 votos** (incluindo o próprio) → líder; heartbeats via `AppendEntries`.
- Sem heartbeat → nova eleição.

## AppendEntries — heartbeat e replicação

- Por réplica: `next_index`, `match_index`.
- Envia só `log[next_index:]` — **nunca** a base inteira.
- Heartbeat = `AppendEntries` vazio ou com entradas pendentes.
- Rejeição se `prev_log_index`/`prev_log_term` inconsistentes + `conflict_index`.
- Commit se `match_index ≥ N` em **≥3 nós** e `log[N].term == current_term`.
- Quórum sempre sobre **4 nós**; não reduz por falha.
- Sem quórum: `no_quorum` / pendente.
- `leader_commit` propagado em todo `AppendEntries`; seguidores aplicam até
  `min(leader_commit, last_log_index)`.
- Sucesso ao cliente (`success=true`) só após commit.

## Operações de leitura (`Consume`)

- Atendida no líder e nas réplicas (`--node nodeX:600X`).
- `items`: apenas `index ≤ commit_index`.
- Metadados `committed_index`, `pending_count` (+ breakdown no líder).

## Persistência (`server/persistence.py`)

Arquivo `data/nodeN/nodeN.json`, escrita atômica (temp + `os.replace`):

```json
{
  "current_term": 2,
  "voted_for": null,
  "commit_index": 3,
  "log": [
    { "term": 1, "index": 1, "key": "cidade", "value": "curitiba" }
  ]
}
```

Persiste: termo, `voted_for`, log completo (uncommitted + committed), `commit_index`.

## Recuperação e reintegração

1. `load_state` no `RaftNode.__init__`.
2. Inicia como seguidor.
3. Identifica líder no primeiro `AppendEntries`.
4. Sync incremental via `next_index` / `conflict_index` (cenário 4).

## Modelo de concorrência (servidor Python)

- Dois `grpc.server` com `ThreadPoolExecutor` (`server/server.py`).
- Thread **ticker** (`run_ticker`): eleição e agendamento de heartbeats/replicação.
- Pool de workers para RPCs Raft lentos (não bloquear o ticker).
- `threading.RLock` no estado compartilhado.

## Estrutura do repositório

```
Av5/
  proto/raft.proto
  server/
    raft_node.py       # máquina de estados Raft (sem import grpc)
    server.py          # dois servidores gRPC + servicers
    transport.py       # GrpcPeers (rede raft)
    persistence.py
    config.py
    run_node.py
    gen/
    tests/
  client/
    main.go
    discovery.go
    gen/
  scripts/
    gen-proto.sh
    run-scenarios.sh   # sobe cluster + janelas logs/cliente
    demo-client.sh     # cenários 1–5 interativos
    run-tests.sh
  docker-compose.yml
  README.md
```

## Cenários de demonstração

| # | Enunciado | Automação |
|---|-----------|-----------|
| 1 | Operação normal | `demo-client.sh` scenario_1 |
| 2 | Falha do líder | scenario_2 |
| 3 | Persistência | scenario_3 + `data/nodeN/nodeN.json` |
| 4 | Recuperação de réplica | scenario_4 + poll até `committed_index` alinhar |
| 5 | Consistência de leitura | scenario_5 |

`run-scenarios.sh` pergunta se deseja limpar `data/` antes de subir os nós.

## Fora de escopo

- Snapshotting / compactação de log.
- Membros dinâmicos (cluster fixo de 4).
- TLS/autenticação.
- Name Server / descoberta fora das respostas gRPC.
