# Av5 — Raft com gRPC, Protocol Buffers, Persistência e Recuperação

Consenso Raft em **4 nós Python** (gRPC) com **cliente Go** (interoperabilidade),
persistência em disco, recuperação de falhas e sincronização incremental de
réplicas.

Alunos:
Lucas Yukio Fukuda Matsumoto
Matheus Vinicius Passos de Santana

## Arquitetura

- 4 nós Raft em **Python** (`node1`..`node4`).
- **Duas portas por nó** (dois servidores gRPC separados):
  - `ClientService` em `nodeN:600N` — rede `client` (única acessível ao cliente Go).
  - `RaftService` em `nodeN-raft:610N` — rede `raft` (somente entre nós).
- Cliente em **Go** (linguagem diferente → interoperabilidade gRPC).
- O cliente **não** alcança a rede `raft`; portanto não pode invocar `RequestVote`/`AppendEntries`.
- Quórum **fixo = 3** (de 4), nunca reduzido por indisponibilidade.
- Descoberta do líder **apenas** via `leader_hint` nas respostas (sem Name Server).
- Persistência por nó em `data/nodeN/node{id}.json` (term, voted_for, log
  uncommitted+committed, commit_index), escrita atômica.

## Pré-requisitos

Docker + Docker Compose. (Go e protoc NÃO precisam estar instalados na máquina —
o cliente é compilado dentro do container.)

## Build

```bash
cd Av5
# Pastas de persistência com dono do usuário local (evita data/ root-owned após o 1º up)
mkdir -p data/node{1,2,3,4}
printf 'HOST_UID=%s\nHOST_GID=%s\n' "$(id -u)" "$(id -g)" > .env
docker compose build
```

## Testes unitários (lógica Raft, em Python)

```bash
cd Av5
python3 -m venv .venv && . .venv/bin/activate
pip install -r server/requirements.txt
./scripts/gen-proto.sh
python -m pytest server/tests -v
```

## Demonstração interativa (cenários 1–5)

Script que sobe o cluster, abre **duas janelas** (logs dos nós + cliente interativo)
e guia os cenários passo a passo — pressione uma tecla entre cada comando.
Ao final dos 5 cenários, o modo livre aceita comandos customizados (`publish`, `consume`,
`stop`/`start` de nós, etc.).

```bash
cd Av5
./scripts/run-scenarios.sh
# opções: --skip-build   --startup 3
```

A janela do cliente também pode ser executada sozinha (com o cluster já no ar):

```bash
./scripts/demo-client.sh
```

---

## Cenário 1 — Operação Normal

```bash
# 1. inicializa os 4 nós
docker compose up -d node1 node2 node3 node4

# 2. eleição automática (aguarde ~10s e observe o líder)
docker compose logs -f node1 node2 node3 node4   # procure "eleito LIDER"

# 3. publicação de dados pelo cliente
docker compose run --rm --no-deps client publish cidade curitiba
docker compose run --rm --no-deps client publish estado parana

# 4. replicação: observe nos logs dos nós "OK replicado ate index=..."

# 5. consumo
docker compose run --rm --no-deps client consume          # lista todos os pares committed
docker compose run --rm --no-deps client consume cidade
```

## Cenário 2 — Falha do Líder

```bash
# descubra o líder nos logs (ex.: node2) e interrompa-o
docker compose stop node2

# nova eleição ocorre entre os nós restantes (aguarde alguns segundos)
docker compose logs -f node1 node3 node4         # novo "eleito LIDER"

# operações continuam (cliente redireciona sozinho para o novo líder)
docker compose run --rm --no-deps client publish pais brasil
docker compose run --rm --no-deps client consume pais
```

## Cenário 3 — Persistência

```bash
# encerra um nó
docker compose stop node3

# reinicia o processo
docker compose start node3

# recuperação automática: nos logs do node3, observe que ele carrega term/log
# persistidos de data/node3/node3.json e volta como Seguidor, reconhecendo o líder.
docker compose logs node3 | tail -n 20
cat data/node3/node3.json                        # estado persistido em disco
```

## Cenário 4 — Recuperação de Réplica (sync incremental)

```bash
# interrompe uma réplica (não-líder; se node4 for líder, pare outro nó)
docker compose stop node4

# novas operações enquanto node4 está fora
# (--no-deps evita que o client suba node4 de volta)
docker compose run --rm --no-deps client publish a 1
docker compose run --rm --no-deps client publish b 2
docker compose run --rm --no-deps client publish c 3

# reinicia a réplica
docker compose start node4

# o líder reenvia APENAS as entradas ausentes (via next_index/conflict_index).
# observe nos logs do líder o avanço de next_index para node4 e em node4 o
# "OK replicado ate index=..." — sem reenvio integral da base.
docker compose logs -f node4
docker compose run --rm --no-deps client consume --node node4:6004   # node4 já consistente
```

## Cenário 5 — Consistência de Leitura

```bash
# leitura no líder e em réplicas: apenas dados committed são retornados
docker compose run --rm --no-deps client consume --node node1:6001
docker compose run --rm --no-deps client consume --node node2:6002
docker compose run --rm --no-deps client consume --node node3:6003

# cada resposta mostra committed_index e pending(uncommitted)=N,
# com breakdown replicadas=... / so_lider=... (no líder) ou replicadas=N (na réplica).
# Entradas uncommitted NUNCA aparecem na lista de itens — só as efetivadas.
```

## Encerrar

```bash
docker compose down
# para limpar o estado persistido:
rm -rf data/
```

Se `rm -rf data/` falhar com “Permission denied”, a pasta foi criada como `root` num run
anterior (container sem `user:`). Corrija uma vez com `sudo chown -R "$(id -u):$(id -g)" data/`
ou use o `.env` com `HOST_UID`/`HOST_GID` antes do próximo `docker compose up`.

## Mapa de requisitos → implementação

| Requisito | Onde |
|-----------|------|
| gRPC + Protobuf | `proto/raft.proto`, stubs gerados |
| Cliente em outra linguagem | `client/` (Go) |
| Cliente só usa Publish/Consume | `ClientService` separado de `RaftService` |
| Descoberta de líder via resposta | `leader_hint` + `client/discovery.go` |
| Eleição | `raft_node.start_election`, `tick` |
| Quórum fixo (3 de 4) | `config.QUORUM`, `_advance_commit_index` |
| AppendEntries / heartbeat / conflito | `handle_append_entries`, `_replicate_to_peer` |
| Sync incremental | `next_index`/`match_index`, `_build_append_args` |
| Leitura só de committed | `handle_consume` |
| Persistência | `persistence.py`, `_persist` |
| Recuperação | `RaftNode.__init__` (load_state) |
