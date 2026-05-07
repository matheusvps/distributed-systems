# AV3 - Raft com PyRO5

Implementação de consenso Raft para replicação de log distribuído entre 4 nós, usando `PyRO5`.

## Arquitetura

- 4 processos Raft (`node1`..`node4`), todos iniciando como `Seguidor`.
- 1 Name Server PyRO5.
- 1 cliente para descobrir o líder e enviar comandos.
- Cada nó usa:
  - `Daemon` com porta fixa.
  - `objectId` explícito.
  - URI fixa no formato `PYRO:objectId@localhost:porta`.

### URIs fixas

- `PYRO:raft.node1@localhost:5001`
- `PYRO:raft.node2@localhost:5002`
- `PYRO:raft.node3@localhost:5003`
- `PYRO:raft.node4@localhost:5004`

## Funcionalidades implementadas

### 1) Eleição de líder

- Timeout de eleição aleatório por nó.
- Ao expirar o timeout de receber um `heartbeat`:
  - nó vira `Candidato`;
  - incrementa `term`;
  - solicita votos (`requestVote`) aos outros nós.
- Líder eleito ao obter maioria (>= 3 de 4).
- Líder registrado no Name Server com nome `Lider` (sobrescrevendo registro anterior).
- Líder envia heartbeats periódicos (`appendEntries` sem entradas).
- Se heartbeats param, seguidores disparam nova eleição automaticamente.

### 2) Replicação de log

- Cliente consulta `Lider` no Name Server e envia comando.
- Líder:
  - adiciona entrada no log local com `term`, `index`, `command`;
  - utiliza a função `sendEntry` para replicar o comando em paralelo para os seguidores (via `appendEntries`).
- Entrada só é considerada comprometida após replicação na maioria dos nós.
- Após o consenso:
  - líder aplica a entrada e retorna ao cliente;
  - líder utiliza a função `commit` para informar aos seguidores sobre o novo índice de comprometimento;
  - seguidores executam a função `notify` para aplicar as entradas em suas máquinas de estado.

### 3) Logs

Nos prints dos nós aparecem eventos contendo:
- `term`
- `index`
- `command`

## Como executar (Docker)

Pré-requisito: Docker + Docker Compose.

Na pasta `Av3`:

```bash
docker compose up --build
```

Isso sobe:
- Name Server
- 4 nós Raft

## Enviar comandos com cliente

Em outro terminal, na pasta `Av3`:

### comando único

```bash
docker compose run --rm client --command "Teste 123"
```

### modo interativo

```bash
docker compose run --rm client
```

Digite comandos e veja as respostas.

## Simular falha de líder

1. Descubra qual container está como líder observando logs:

```bash
docker compose logs -f node1 node2 node3 node4
```

2. Pare o container líder:

```bash
docker compose stop nodeX
```

3. Aguarde timeout de eleição e observe novo líder sendo eleito e registrado como `Lider`.

## Execução local (sem Docker)

Opcionalmente, em 6 terminais:

1. Name Server:
```bash
python run_nameserver.py
```
2. Nós:
```bash
python run_node.py --id 1
python run_node.py --id 2
python run_node.py --id 3
python run_node.py --id 4
```
3. Cliente:
```bash
python client.py --command "TEST_COMMAND"
```

## Testes

```bash
python -m unittest test_raft_node.py
```

## Referências

- Slides Coordenação e Acordo (Raft, eleição e replicação)
- [The Secret Lives of Data - Raft](https://thesecretlivesofdata.com/raft/)
- [PyRO5 Documentation](https://pyro5.readthedocs.io/en/latest/intro.html)
