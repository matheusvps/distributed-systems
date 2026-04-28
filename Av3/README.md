# AV3 - Raft com PyRO5

Implementacao de consenso Raft para replicacao de log distribuido entre 4 nos, usando `PyRO5`.

## Arquitetura

- 4 processos Raft (`node1`..`node4`), todos iniciando como `Follower`.
- 1 Name Server PyRO5.
- 1 cliente para descobrir o lider e enviar comandos.
- Cada no usa:
  - `Daemon` com porta fixa.
  - `objectId` explicito.
  - URI fixa no formato `PYRO:objectId@localhost:porta`.

### URIs fixas

- `PYRO:raft.node1@localhost:5001`
- `PYRO:raft.node2@localhost:5002`
- `PYRO:raft.node3@localhost:5003`
- `PYRO:raft.node4@localhost:5004`

## Funcionalidades implementadas

### 1) Eleicao de lider

- Timeout de eleicao aleatorio por no.
- Ao expirar o timeout:
  - no vira `Candidate`;
  - incrementa `term`;
  - solicita votos (`request_vote`) aos outros nos.
- Lider eleito ao obter maioria (>= 3 de 4).
- Lider registrado no Name Server com nome `Lider` (sobrescrevendo registro anterior).
- Lider envia heartbeats periodicos (`AppendEntries` sem entradas).
- Se heartbeats param, seguidores disparam nova eleicao automaticamente.

### 2) Replicacao de log

- Cliente consulta `Lider` no Name Server e envia comando.
- Lider:
  - adiciona entrada no log local com `term`, `index`, `command`;
  - envia `AppendEntries` para seguidores.
- Entrada so e considerada commitada apos maioria (>= 3 de 4).
- Depois do commit:
  - lider aplica a entrada;
  - envia confirmacao (`commit_up_to`) aos seguidores;
  - todos aplicam a entrada.

### 3) Logs

Nos prints dos nos aparecem eventos contendo:
- `term`
- `index`
- `command`

## Como executar (Docker)

Pre-requisito: Docker + Docker Compose.

Na pasta `Av3`:

```bash
docker compose up --build
```

Isso sobe:
- Name Server
- 4 nos Raft

## Enviar comandos com cliente

Em outro terminal, na pasta `Av3`:

### comando unico

```bash
docker compose run --rm client --command "SET x 1"
```

### modo interativo

```bash
docker compose run --rm client
```

Digite comandos e veja as respostas.

## Simular falha de lider

1. Descubra qual container esta como lider observando logs:

```bash
docker compose logs -f node1 node2 node3 node4
```

2. Pare o container lider:

```bash
docker compose stop nodeX
```

3. Aguarde timeout de eleicao e observe novo lider sendo eleito e registrado como `Lider`.

## Execucao local (sem Docker)

Opcionalmente, em 6 terminais:

1. Name Server:
```bash
python run_nameserver.py
```
2. Nos:
```bash
python run_node.py --id 1
python run_node.py --id 2
python run_node.py --id 3
python run_node.py --id 4
```
3. Cliente:
```bash
python client.py --command "SET x 1"
```

## Testes

```bash
python -m unittest test_raft_node.py
```

## Referencias

- Slides Coordenação e Acordo (Raft, eleicao e replicacao)
- [The Secret Lives of Data - Raft](https://thesecretlivesofdata.com/raft/)
- [PyRO5 Documentation](https://pyro5.readthedocs.io/en/latest/intro.html)

