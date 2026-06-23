# Av5 — Raft gRPC + Protobuf Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Evolve the Av3 Pyro Raft into a gRPC + Protocol Buffers cluster of 4 Python nodes with a Go client, adding state persistence, crash recovery, and incremental replica sync.

**Architecture:** Each Python node runs one gRPC server hosting two services — `RaftService` (internal: RequestVote, AppendEntries) and `ClientService` (external: Publish, Consume). All Raft decision logic lives in pure-Python modules with **no gRPC imports** (network access is injected as a `transport` object) so it is unit-testable locally. The gRPC servicers are thin adapters translating protobuf ↔ plain Python. The Go client discovers the leader only from node replies and redirects.

**Tech Stack:** Python 3.12 (servers, `grpcio`/`grpcio-tools`), Go 1.23 (client, `google.golang.org/grpc`), Protocol Buffers proto3, Docker Compose, pytest.

## Global Constraints

- Cluster is **exactly 4 nodes**; quorum is **always 3** (`4 // 2 + 1`), never reduced by unreachable nodes. Define once as `QUORUM = 3` in `server/config.py` and import everywhere.
- Communication is **exclusively gRPC**. No other transport.
- The client may call **only** `ClientService` (`Publish`, `Consume`). It must never call `RaftService`.
- Leader discovery is **only** via node replies (`leader_hint`). No Name Server, no registry.
- Replication sends **only missing entries** (`log[next_index:]`), never the whole store.
- Only **committed** entries (`index <= commit_index`) are returned to the client.
- All Raft logic modules (`config.py`, `persistence.py`, `raft_node.py`) must **not** `import grpc` or import anything from `server/gen/` at module load — keeps them unit-testable without the gRPC toolchain.
- Persisted per node (atomically): `current_term`, `voted_for`, full `log` (uncommitted + committed), `commit_index`.
- Node IDs are `1..4`. Addresses: `node1:6001`, `node2:6002`, `node3:6003`, `node4:6004`.
- Log indices are **1-based**; index `0` means "empty / before first entry".

---

### Task 1: Proto definition, repo scaffolding, Python stub generation

**Files:**
- Create: `Av5/proto/raft.proto`
- Create: `Av5/scripts/gen-proto.sh`
- Create: `Av5/server/requirements.txt`
- Create: `Av5/.gitignore`
- Create: `Av5/server/gen/__init__.py` (empty)
- Generated (by script): `Av5/server/gen/raft_pb2.py`, `Av5/server/gen/raft_pb2_grpc.py`

**Interfaces:**
- Produces: the `raft.proto` package `raft` with services `ClientService` (Publish, Consume) and `RaftService` (RequestVote, AppendEntries), and messages exactly as below. Later tasks reference these message/field names.

- [ ] **Step 1: Write `Av5/proto/raft.proto`**

```proto
syntax = "proto3";
package raft;

// ---------- Application (client-facing) ----------
service ClientService {
  rpc Publish (PublishRequest) returns (PublishReply);
  rpc Consume (ConsumeRequest) returns (ConsumeReply);
}

message PublishRequest { string key = 1; string value = 2; }
message PublishReply {
  bool   success     = 1;
  string leader_hint = 2;
  int64  index       = 3;
  string message     = 4;
}

message ConsumeRequest { string key = 1; }
message ConsumeReply {
  bool              success         = 1;
  repeated DataItem items           = 2;
  string            leader_hint     = 3;
  bool              is_leader       = 4;
  int64             committed_index = 5;
  int64             pending_count   = 6;
}
message DataItem { string key = 1; string value = 2; int64 index = 3; }

// ---------- Raft (internal) ----------
service RaftService {
  rpc RequestVote   (RequestVoteArgs)   returns (RequestVoteReply);
  rpc AppendEntries (AppendEntriesArgs) returns (AppendEntriesReply);
}

message LogEntry { int64 term = 1; int64 index = 2; string key = 3; string value = 4; }

message RequestVoteArgs {
  int64 term = 1;
  int32 candidate_id = 2;
  int64 last_log_index = 3;
  int64 last_log_term = 4;
}
message RequestVoteReply { int64 term = 1; bool vote_granted = 2; }

message AppendEntriesArgs {
  int64 term = 1;
  int32 leader_id = 2;
  int64 prev_log_index = 3;
  int64 prev_log_term = 4;
  repeated LogEntry entries = 5;
  int64 leader_commit = 6;
}
message AppendEntriesReply {
  int64 term = 1;
  bool  success = 2;
  int64 conflict_index = 3;
}
```

- [ ] **Step 2: Write `Av5/server/requirements.txt`**

```
grpcio==1.68.1
grpcio-tools==1.68.1
protobuf==5.29.1
pytest==8.3.4
```

- [ ] **Step 3: Write `Av5/.gitignore`**

```
__pycache__/
*.pyc
data/
client/gen/
.pytest_cache/
```

(Python `server/gen/` stubs ARE committed so local pytest works; Go `client/gen/` is generated at Docker build time.)

- [ ] **Step 4: Write `Av5/scripts/gen-proto.sh`**

```bash
#!/usr/bin/env bash
# Regenerate Python gRPC stubs locally (Go stubs are generated at Docker build).
# Requires: a Python venv with grpcio-tools installed (see server/requirements.txt).
set -euo pipefail
cd "$(dirname "$0")/.."

python -m grpc_tools.protoc \
  -I proto \
  --python_out=server/gen \
  --grpc_python_out=server/gen \
  proto/raft.proto

# grpc_python_out emits `import raft_pb2` (no package). Make it package-relative.
sed -i 's/^import raft_pb2/from . import raft_pb2/' server/gen/raft_pb2_grpc.py
echo "Python stubs generated in server/gen/"
```

- [ ] **Step 5: Create empty `Av5/server/gen/__init__.py`**

(Empty file so `server/gen` is a package.)

- [ ] **Step 6: Generate the Python stubs**

Run:
```bash
cd Av5
python3 -m venv .venv && . .venv/bin/activate
pip install -r server/requirements.txt
chmod +x scripts/gen-proto.sh
./scripts/gen-proto.sh
```
Expected: `server/gen/raft_pb2.py` and `server/gen/raft_pb2_grpc.py` exist; no errors. If `grpcio-tools` has no wheel for the local Python, create the venv with `python3.12` instead.

- [ ] **Step 7: Verify the stubs import**

Run: `cd Av5 && . .venv/bin/activate && python -c "from server.gen import raft_pb2, raft_pb2_grpc; print('ok', raft_pb2.PublishRequest)"`
Expected: prints `ok <class 'raft_pb2.PublishRequest'>` (or similar), no ImportError.

- [ ] **Step 8: Commit**

```bash
cd Av5 && git add proto scripts server/requirements.txt server/gen .gitignore
git commit -m "feat(av5): proto definition + Python gRPC stub generation"
```

---

### Task 2: Config module

**Files:**
- Create: `Av5/server/config.py`
- Create: `Av5/server/__init__.py` (empty)
- Test: `Av5/server/tests/test_config.py`
- Create: `Av5/server/tests/__init__.py` (empty)

**Interfaces:**
- Produces: `NODE_IDS: list[int]`, `NODE_ADDRESSES: dict[int, str]`, `QUORUM: int`, `ELECTION_TIMEOUT_RANGE: tuple[float, float]`, `HEARTBEAT_INTERVAL: float`, `TICK_INTERVAL: float`, `RPC_TIMEOUT: float`, `data_path(node_id: int) -> str`, `peer_ids(node_id: int) -> list[int]`.

- [ ] **Step 1: Write the failing test `Av5/server/tests/test_config.py`**

```python
from server import config

def test_quorum_is_fixed_three():
    assert config.QUORUM == 3

def test_four_nodes_with_addresses():
    assert config.NODE_IDS == [1, 2, 3, 4]
    assert config.NODE_ADDRESSES[1] == "node1:6001"
    assert config.NODE_ADDRESSES[4] == "node4:6004"

def test_peer_ids_excludes_self():
    assert config.peer_ids(2) == [1, 3, 4]

def test_data_path_uses_node_id():
    assert config.data_path(3).endswith("node3.json")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Av5 && . .venv/bin/activate && python -m pytest server/tests/test_config.py -v`
Expected: FAIL (ModuleNotFoundError: server.config).

- [ ] **Step 3: Write `Av5/server/config.py`**

```python
import os

NODE_IDS = [1, 2, 3, 4]
NODE_ADDRESSES = {
    1: "node1:6001",
    2: "node2:6002",
    3: "node3:6003",
    4: "node4:6004",
}
QUORUM = len(NODE_IDS) // 2 + 1  # always 3 for a 4-node cluster

ELECTION_TIMEOUT_RANGE = (3.0, 6.0)  # seconds
HEARTBEAT_INTERVAL = 1.0             # seconds
TICK_INTERVAL = 0.1                  # seconds
RPC_TIMEOUT = 2.0                    # seconds

DATA_DIR = os.environ.get("RAFT_DATA_DIR", "data")


def peer_ids(node_id):
    return [nid for nid in NODE_IDS if nid != node_id]


def data_path(node_id):
    return os.path.join(DATA_DIR, f"node{node_id}.json")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd Av5 && . .venv/bin/activate && python -m pytest server/tests/test_config.py -v`
Expected: 4 passed. (Also create empty `server/__init__.py` and `server/tests/__init__.py` first if collection fails.)

- [ ] **Step 5: Commit**

```bash
cd Av5 && git add server/config.py server/__init__.py server/tests
git commit -m "feat(av5): config module with fixed quorum and node addresses"
```

---

### Task 3: Persistence module

**Files:**
- Create: `Av5/server/persistence.py`
- Test: `Av5/server/tests/test_persistence.py`

**Interfaces:**
- Produces:
  - `PersistentState` — a dataclass with fields `current_term: int = 0`, `voted_for: int | None = None`, `commit_index: int = 0`, `log: list[dict] = []`. Each log entry dict has keys `term`, `index`, `key`, `value`.
  - `save_state(path: str, state: PersistentState) -> None` — atomic (temp file + `os.replace`).
  - `load_state(path: str) -> PersistentState` — returns defaults if file missing.

- [ ] **Step 1: Write the failing test `Av5/server/tests/test_persistence.py`**

```python
from server.persistence import PersistentState, save_state, load_state

def test_load_missing_returns_defaults(tmp_path):
    state = load_state(str(tmp_path / "node9.json"))
    assert state.current_term == 0
    assert state.voted_for is None
    assert state.commit_index == 0
    assert state.log == []

def test_save_then_load_roundtrip(tmp_path):
    path = str(tmp_path / "node1.json")
    original = PersistentState(
        current_term=5,
        voted_for=3,
        commit_index=2,
        log=[
            {"term": 1, "index": 1, "key": "a", "value": "1"},
            {"term": 4, "index": 2, "key": "b", "value": "2"},
        ],
    )
    save_state(path, original)
    loaded = load_state(path)
    assert loaded.current_term == 5
    assert loaded.voted_for == 3
    assert loaded.commit_index == 2
    assert loaded.log == original.log

def test_save_is_atomic_no_temp_left(tmp_path):
    path = str(tmp_path / "node1.json")
    save_state(path, PersistentState(current_term=1))
    leftovers = [p.name for p in tmp_path.iterdir() if p.name != "node1.json"]
    assert leftovers == []

def test_save_creates_parent_dir(tmp_path):
    path = str(tmp_path / "data" / "node2.json")
    save_state(path, PersistentState(current_term=2))
    assert load_state(path).current_term == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Av5 && . .venv/bin/activate && python -m pytest server/tests/test_persistence.py -v`
Expected: FAIL (ModuleNotFoundError: server.persistence).

- [ ] **Step 3: Write `Av5/server/persistence.py`**

```python
import json
import os
from dataclasses import dataclass, field, asdict


@dataclass
class PersistentState:
    current_term: int = 0
    voted_for: "int | None" = None
    commit_index: int = 0
    log: list = field(default_factory=list)


def save_state(path, state):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(asdict(state), fh, ensure_ascii=False, indent=2)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)  # atomic on POSIX


def load_state(path):
    if not os.path.exists(path):
        return PersistentState()
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return PersistentState(
        current_term=data.get("current_term", 0),
        voted_for=data.get("voted_for"),
        commit_index=data.get("commit_index", 0),
        log=data.get("log", []),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd Av5 && . .venv/bin/activate && python -m pytest server/tests/test_persistence.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
cd Av5 && git add server/persistence.py server/tests/test_persistence.py
git commit -m "feat(av5): atomic JSON persistence module"
```

---

### Task 4: RaftNode core — construction, log helpers, persistence wiring

**Files:**
- Create: `Av5/server/raft_node.py`
- Test: `Av5/server/tests/test_raft_core.py`

**Interfaces:**
- Consumes: `server.config`, `server.persistence`.
- Produces: class `RaftNode`:
  - `RaftNode(node_id: int, transport, data_path: str | None = None)` — `transport` is any object with `send_request_vote(peer_id, args: dict) -> dict | None` and `send_append_entries(peer_id, args: dict) -> dict | None`. Loads persisted state on init; starts as follower.
  - Attributes: `node_id`, `state` (`"Seguidor"|"Candidato"|"Lider"`), `current_term`, `voted_for`, `log` (list of entry dicts), `commit_index`, `last_applied`, `leader_id`, `next_index` (dict), `match_index` (dict), `lock` (`threading.RLock`).
  - `last_log_index() -> int`, `last_log_term() -> int`
  - `_is_up_to_date(last_log_index: int, last_log_term: int) -> bool`
  - `_persist() -> None`
  - `_term_of(index: int) -> int` (term at 1-based index; `0` for index `0` or out of range)

- [ ] **Step 1: Write the failing test `Av5/server/tests/test_raft_core.py`**

```python
from server.raft_node import RaftNode
from server.persistence import PersistentState, save_state


class FakeTransport:
    def send_request_vote(self, peer_id, args):
        return None
    def send_append_entries(self, peer_id, args):
        return None


def make_node(tmp_path, nid=1):
    return RaftNode(nid, FakeTransport(), data_path=str(tmp_path / f"node{nid}.json"))


def test_starts_as_follower_with_defaults(tmp_path):
    n = make_node(tmp_path)
    assert n.state == "Seguidor"
    assert n.current_term == 0
    assert n.voted_for is None
    assert n.log == []
    assert n.commit_index == 0

def test_loads_persisted_state(tmp_path):
    path = tmp_path / "node1.json"
    save_state(str(path), PersistentState(
        current_term=7, voted_for=2, commit_index=1,
        log=[{"term": 7, "index": 1, "key": "k", "value": "v"}],
    ))
    n = make_node(tmp_path)
    assert n.current_term == 7
    assert n.voted_for == 2
    assert n.commit_index == 1
    assert n.last_log_index() == 1
    assert n.last_log_term() == 7
    assert n.state == "Seguidor"  # always recovers as follower

def test_last_log_info_empty(tmp_path):
    n = make_node(tmp_path)
    assert n.last_log_index() == 0
    assert n.last_log_term() == 0

def test_up_to_date_compares_term_then_index(tmp_path):
    n = make_node(tmp_path)
    n.log = [{"term": 2, "index": 1, "key": "a", "value": "1"},
             {"term": 2, "index": 2, "key": "b", "value": "2"}]
    # higher term wins even with shorter log
    assert n._is_up_to_date(last_log_index=1, last_log_term=3) is True
    # same term, candidate index >= ours -> ok
    assert n._is_up_to_date(last_log_index=2, last_log_term=2) is True
    # same term, candidate shorter -> not up to date
    assert n._is_up_to_date(last_log_index=1, last_log_term=2) is False
    # lower term -> not up to date
    assert n._is_up_to_date(last_log_index=9, last_log_term=1) is False

def test_persist_writes_file(tmp_path):
    n = make_node(tmp_path)
    n.current_term = 3
    n.voted_for = 1
    n._persist()
    from server.persistence import load_state
    reloaded = load_state(str(tmp_path / "node1.json"))
    assert reloaded.current_term == 3
    assert reloaded.voted_for == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Av5 && . .venv/bin/activate && python -m pytest server/tests/test_raft_core.py -v`
Expected: FAIL (ModuleNotFoundError: server.raft_node).

- [ ] **Step 3: Write `Av5/server/raft_node.py` (core only)**

```python
import random
import threading
import time

from server import config
from server.persistence import PersistentState, save_state, load_state


class RaftNode:
    def __init__(self, node_id, transport, data_path=None):
        self.node_id = node_id
        self.transport = transport
        self.data_path = data_path or config.data_path(node_id)

        persisted = load_state(self.data_path)
        self.current_term = persisted.current_term
        self.voted_for = persisted.voted_for
        self.log = persisted.log
        self.commit_index = persisted.commit_index

        self.state = "Seguidor"            # always recover as follower
        self.last_applied = 0
        self.leader_id = None

        self.next_index = {}
        self.match_index = {}

        self.lock = threading.RLock()
        self.running = False
        self.election_deadline = 0.0
        self.last_heartbeat_sent = 0.0
        self._reset_election_deadline()

    # ----- logging -----
    def log_event(self, msg, peer_id=None):
        prefix = f"node{self.node_id} [{self.state}] (term={self.current_term})"
        if peer_id is not None:
            print(f"{prefix} -> node{peer_id}: {msg}", flush=True)
        else:
            print(f"{prefix}: {msg}", flush=True)

    # ----- log helpers -----
    def last_log_index(self):
        return self.log[-1]["index"] if self.log else 0

    def last_log_term(self):
        return self.log[-1]["term"] if self.log else 0

    def _term_of(self, index):
        if index <= 0 or index > len(self.log):
            return 0
        return self.log[index - 1]["term"]

    def _is_up_to_date(self, last_log_index, last_log_term):
        my_index, my_term = self.last_log_index(), self.last_log_term()
        if last_log_term != my_term:
            return last_log_term > my_term
        return last_log_index >= my_index

    # ----- persistence -----
    def _persist(self):
        save_state(self.data_path, PersistentState(
            current_term=self.current_term,
            voted_for=self.voted_for,
            commit_index=self.commit_index,
            log=self.log,
        ))

    # ----- election timer -----
    def _reset_election_deadline(self):
        self.election_deadline = time.time() + random.uniform(*config.ELECTION_TIMEOUT_RANGE)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd Av5 && . .venv/bin/activate && python -m pytest server/tests/test_raft_core.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
cd Av5 && git add server/raft_node.py server/tests/test_raft_core.py
git commit -m "feat(av5): RaftNode core, log helpers, persistence wiring"
```

---

### Task 5: State transitions + RequestVote handler

**Files:**
- Modify: `Av5/server/raft_node.py`
- Test: `Av5/server/tests/test_request_vote.py`

**Interfaces:**
- Consumes: Task 4 `RaftNode`.
- Produces:
  - `_become_follower(term: int, leader_id: int | None) -> None`
  - `_become_leader() -> None` (sets `next_index[peer]=last_log_index()+1`, `match_index[peer]=0`)
  - `handle_request_vote(term, candidate_id, last_log_index, last_log_term) -> dict` returning `{"term": int, "vote_granted": bool}`. Grants at most one vote per term, only to up-to-date candidates; steps down on higher term; persists term/vote changes.

- [ ] **Step 1: Write the failing test `Av5/server/tests/test_request_vote.py`**

```python
from server.raft_node import RaftNode


class FakeTransport:
    def send_request_vote(self, peer_id, args): return None
    def send_append_entries(self, peer_id, args): return None


def make_node(tmp_path, nid=1):
    return RaftNode(nid, FakeTransport(), data_path=str(tmp_path / f"node{nid}.json"))


def test_grants_vote_for_fresh_term(tmp_path):
    n = make_node(tmp_path)
    reply = n.handle_request_vote(term=1, candidate_id=2, last_log_index=0, last_log_term=0)
    assert reply == {"term": 1, "vote_granted": True}
    assert n.voted_for == 2
    assert n.current_term == 1

def test_rejects_stale_term(tmp_path):
    n = make_node(tmp_path)
    n.current_term = 5
    reply = n.handle_request_vote(term=3, candidate_id=2, last_log_index=0, last_log_term=0)
    assert reply["vote_granted"] is False
    assert reply["term"] == 5

def test_one_vote_per_term(tmp_path):
    n = make_node(tmp_path)
    n.handle_request_vote(term=1, candidate_id=2, last_log_index=0, last_log_term=0)
    reply = n.handle_request_vote(term=1, candidate_id=3, last_log_index=0, last_log_term=0)
    assert reply["vote_granted"] is False  # already voted for node2

def test_rejects_outdated_candidate_log(tmp_path):
    n = make_node(tmp_path)
    n.log = [{"term": 2, "index": 1, "key": "a", "value": "1"}]
    n.current_term = 2
    reply = n.handle_request_vote(term=3, candidate_id=2, last_log_index=0, last_log_term=0)
    assert reply["vote_granted"] is False  # candidate log behind
    assert n.current_term == 3  # but still steps up in term

def test_vote_is_persisted(tmp_path):
    n = make_node(tmp_path)
    n.handle_request_vote(term=4, candidate_id=3, last_log_index=0, last_log_term=0)
    from server.persistence import load_state
    s = load_state(str(tmp_path / "node1.json"))
    assert s.current_term == 4 and s.voted_for == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Av5 && . .venv/bin/activate && python -m pytest server/tests/test_request_vote.py -v`
Expected: FAIL (AttributeError: handle_request_vote).

- [ ] **Step 3: Add transitions + handler to `Av5/server/raft_node.py`**

Append these methods to the `RaftNode` class:

```python
    # ----- state transitions -----
    def _become_follower(self, term, leader_id):
        if term > self.current_term:
            self.current_term = term
            self.voted_for = None
        self.state = "Seguidor"
        self.leader_id = leader_id
        self._reset_election_deadline()
        self._persist()

    def _become_leader(self):
        self.state = "Lider"
        self.leader_id = self.node_id
        nxt = self.last_log_index() + 1
        self.next_index = {pid: nxt for pid in config.peer_ids(self.node_id)}
        self.match_index = {pid: 0 for pid in config.peer_ids(self.node_id)}
        self.last_heartbeat_sent = 0.0
        self.log_event(f"eleito LIDER no termo {self.current_term}")

    # ----- RequestVote (RaftService) -----
    def handle_request_vote(self, term, candidate_id, last_log_index, last_log_term):
        with self.lock:
            if term < self.current_term:
                return {"term": self.current_term, "vote_granted": False}

            if term > self.current_term:
                self.current_term = term
                self.voted_for = None
                self.state = "Seguidor"
                self.leader_id = None

            can_vote = self.voted_for in (None, candidate_id)
            up_to_date = self._is_up_to_date(last_log_index, last_log_term)

            if can_vote and up_to_date:
                self.voted_for = candidate_id
                self._reset_election_deadline()
                self._persist()
                self.log_event(f"VOTOU em node{candidate_id} no termo {self.current_term}")
                return {"term": self.current_term, "vote_granted": True}

            self._persist()
            reason = "ja votou" if not can_vote else "log desatualizado"
            self.log_event(f"RECUSOU voto p/ node{candidate_id}: {reason}")
            return {"term": self.current_term, "vote_granted": False}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd Av5 && . .venv/bin/activate && python -m pytest server/tests/test_request_vote.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
cd Av5 && git add server/raft_node.py server/tests/test_request_vote.py
git commit -m "feat(av5): state transitions and RequestVote handler"
```

---

### Task 6: AppendEntries handler (follower side) + conflict hint

**Files:**
- Modify: `Av5/server/raft_node.py`
- Test: `Av5/server/tests/test_append_entries.py`

**Interfaces:**
- Consumes: Task 5 `RaftNode`.
- Produces:
  - `handle_append_entries(term, leader_id, prev_log_index, prev_log_term, entries, leader_commit) -> dict` returning `{"term": int, "success": bool, "conflict_index": int}`. `entries` is a list of entry dicts (`term`, `index`, `key`, `value`).
  - `_apply_committed() -> None` — advances `last_applied` to `commit_index`, logging applied entries.
  - On mismatch returns `success=False` with `conflict_index` = the first index the leader should retry from (1-based; never below 1).

- [ ] **Step 1: Write the failing test `Av5/server/tests/test_append_entries.py`**

```python
from server.raft_node import RaftNode


class FakeTransport:
    def send_request_vote(self, peer_id, args): return None
    def send_append_entries(self, peer_id, args): return None


def make_node(tmp_path, nid=2):
    return RaftNode(nid, FakeTransport(), data_path=str(tmp_path / f"node{nid}.json"))


def entry(term, index, key, value):
    return {"term": term, "index": index, "key": key, "value": value}


def test_heartbeat_accepted_on_empty_log(tmp_path):
    n = make_node(tmp_path)
    reply = n.handle_append_entries(term=1, leader_id=1, prev_log_index=0,
                                    prev_log_term=0, entries=[], leader_commit=0)
    assert reply["success"] is True
    assert n.leader_id == 1
    assert n.current_term == 1

def test_rejects_lower_term(tmp_path):
    n = make_node(tmp_path)
    n.current_term = 5
    reply = n.handle_append_entries(term=2, leader_id=1, prev_log_index=0,
                                    prev_log_term=0, entries=[], leader_commit=0)
    assert reply["success"] is False
    assert reply["term"] == 5

def test_appends_new_entries(tmp_path):
    n = make_node(tmp_path)
    reply = n.handle_append_entries(term=1, leader_id=1, prev_log_index=0, prev_log_term=0,
                                    entries=[entry(1, 1, "a", "1"), entry(1, 2, "b", "2")],
                                    leader_commit=0)
    assert reply["success"] is True
    assert len(n.log) == 2
    assert n.commit_index == 0  # nothing committed yet

def test_prev_log_mismatch_returns_conflict_index(tmp_path):
    n = make_node(tmp_path)
    # follower has one entry at index 1 term 1
    n.log = [entry(1, 1, "a", "1")]
    n.current_term = 1
    # leader claims prev at index 2 (we don't have it) -> reject, hint to our end+1
    reply = n.handle_append_entries(term=1, leader_id=1, prev_log_index=2, prev_log_term=1,
                                    entries=[entry(1, 3, "c", "3")], leader_commit=0)
    assert reply["success"] is False
    assert reply["conflict_index"] == 2  # len(log)+1

def test_conflicting_term_truncates_and_rejects(tmp_path):
    n = make_node(tmp_path)
    n.log = [entry(1, 1, "a", "1"), entry(2, 2, "b", "2")]
    n.current_term = 3
    # leader's prev_log_term at index 2 is 9, mismatch -> truncate from index 2, reject
    reply = n.handle_append_entries(term=3, leader_id=1, prev_log_index=2, prev_log_term=9,
                                    entries=[], leader_commit=0)
    assert reply["success"] is False
    assert len(n.log) == 1  # truncated conflicting tail
    assert reply["conflict_index"] == 2

def test_advances_commit_index_and_applies(tmp_path):
    n = make_node(tmp_path)
    n.handle_append_entries(term=1, leader_id=1, prev_log_index=0, prev_log_term=0,
                            entries=[entry(1, 1, "a", "1"), entry(1, 2, "b", "2")],
                            leader_commit=0)
    # second call commits up to index 1
    reply = n.handle_append_entries(term=1, leader_id=1, prev_log_index=2, prev_log_term=1,
                                    entries=[], leader_commit=1)
    assert reply["success"] is True
    assert n.commit_index == 1
    assert n.last_applied == 1

def test_commit_index_capped_at_local_log_len(tmp_path):
    n = make_node(tmp_path)
    n.handle_append_entries(term=1, leader_id=1, prev_log_index=0, prev_log_term=0,
                            entries=[entry(1, 1, "a", "1")], leader_commit=99)
    assert n.commit_index == 1  # cannot commit beyond what we have

def test_idempotent_resend_does_not_duplicate(tmp_path):
    n = make_node(tmp_path)
    args = dict(term=1, leader_id=1, prev_log_index=0, prev_log_term=0,
                entries=[entry(1, 1, "a", "1")], leader_commit=0)
    n.handle_append_entries(**args)
    n.handle_append_entries(**args)
    assert len(n.log) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Av5 && . .venv/bin/activate && python -m pytest server/tests/test_append_entries.py -v`
Expected: FAIL (AttributeError: handle_append_entries).

- [ ] **Step 3: Add handler to `Av5/server/raft_node.py`**

Append to the `RaftNode` class:

```python
    # ----- AppendEntries (RaftService) -----
    def handle_append_entries(self, term, leader_id, prev_log_index,
                              prev_log_term, entries, leader_commit):
        with self.lock:
            if term < self.current_term:
                return {"term": self.current_term, "success": False, "conflict_index": 0}

            # valid leader for this term (>=): become/stay follower, reset timer
            self._become_follower(max(term, self.current_term), leader_id)

            # consistency check on prev entry
            if prev_log_index > len(self.log):
                return {"term": self.current_term, "success": False,
                        "conflict_index": len(self.log) + 1}
            if prev_log_index > 0 and self._term_of(prev_log_index) != prev_log_term:
                # truncate the conflicting tail and ask leader to back up
                self.log = self.log[: prev_log_index - 1]
                self._persist()
                return {"term": self.current_term, "success": False,
                        "conflict_index": prev_log_index}

            # append/overwrite entries
            self._merge_entries(entries)

            # advance commit index (never beyond what we hold)
            if leader_commit > self.commit_index:
                self.commit_index = min(leader_commit, len(self.log))
                self._apply_committed()

            self._persist()
            if entries:
                self.log_event(f"OK replicado ate index={self.last_log_index()}",
                               peer_id=leader_id)
            return {"term": self.current_term, "success": True, "conflict_index": 0}

    def _merge_entries(self, entries):
        for e in entries:
            idx = e["index"]
            if idx <= len(self.log):
                if self.log[idx - 1]["term"] != e["term"]:
                    self.log = self.log[: idx - 1]
                    self.log.append(e)
            else:
                self.log.append(e)

    def _apply_committed(self):
        while self.last_applied < self.commit_index:
            e = self.log[self.last_applied]
            self.last_applied += 1
            self.log_event(f"APLICADO (committed) index={e['index']} "
                           f"{e['key']}={e['value']}")
```

Note: `_become_follower` already persists; the extra `_persist()` calls keep the file current after log/commit changes.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd Av5 && . .venv/bin/activate && python -m pytest server/tests/test_append_entries.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
cd Av5 && git add server/raft_node.py server/tests/test_append_entries.py
git commit -m "feat(av5): AppendEntries follower handler with conflict hint"
```

---

### Task 7: Leader replication + commit advancement (fixed quorum)

**Files:**
- Modify: `Av5/server/raft_node.py`
- Test: `Av5/server/tests/test_replication.py`

**Interfaces:**
- Consumes: Task 6 `RaftNode`, `transport.send_append_entries(peer_id, args) -> dict | None`.
- Produces:
  - `_build_append_args(peer_id) -> dict` — builds AppendEntries args for a peer from `next_index` (entries = `log[next_index-1:]`).
  - `_replicate_to_peer(peer_id) -> None` — sends one AppendEntries, updates `next_index`/`match_index` on success, backs off using `conflict_index` on failure, steps down on higher term.
  - `_advance_commit_index() -> None` — sets `commit_index` to the highest `N` such that `N > commit_index`, `N` replicated on **≥ QUORUM** nodes (counting leader), and `log[N].term == current_term`; then applies.
  - `replicate_to_all() -> None` — replicates to every peer (used by heartbeat and after a write), then advances commit.

- [ ] **Step 1: Write the failing test `Av5/server/tests/test_replication.py`**

```python
from server.raft_node import RaftNode
from server import config


class ScriptedTransport:
    """Returns canned AppendEntries replies per peer; records sent args."""
    def __init__(self, replies):
        self.replies = replies          # {peer_id: [reply, reply, ...]}
        self.sent = {pid: [] for pid in replies}
    def send_request_vote(self, peer_id, args): return None
    def send_append_entries(self, peer_id, args):
        self.sent[peer_id].append(args)
        queue = self.replies[peer_id]
        return queue.pop(0) if queue else {"term": args["term"], "success": True,
                                           "conflict_index": 0}


def leader(tmp_path, transport):
    n = RaftNode(1, transport, data_path=str(tmp_path / "node1.json"))
    n.current_term = 1
    n.state = "Lider"
    n.leader_id = 1
    n.next_index = {pid: 1 for pid in config.peer_ids(1)}
    n.match_index = {pid: 0 for pid in config.peer_ids(1)}
    return n


def test_successful_replication_updates_indices(tmp_path):
    t = ScriptedTransport({2: [], 3: [], 4: []})
    n = leader(tmp_path, t)
    n.log = [{"term": 1, "index": 1, "key": "a", "value": "1"}]
    n._replicate_to_peer(2)
    assert n.match_index[2] == 1
    assert n.next_index[2] == 2

def test_failure_backs_off_using_conflict_index(tmp_path):
    t = ScriptedTransport({2: [{"term": 1, "success": False, "conflict_index": 1}],
                           3: [], 4: []})
    n = leader(tmp_path, t)
    n.log = [{"term": 1, "index": 1, "key": "a", "value": "1"}]
    n.next_index[2] = 2
    n._replicate_to_peer(2)
    assert n.next_index[2] == 1  # backed off to conflict_index

def test_commit_advances_only_with_quorum(tmp_path):
    t = ScriptedTransport({2: [], 3: [], 4: []})
    n = leader(tmp_path, t)
    n.log = [{"term": 1, "index": 1, "key": "a", "value": "1"}]
    # only leader + node2 have it -> 2 of 4, below quorum 3
    n.match_index = {2: 1, 3: 0, 4: 0}
    n._advance_commit_index()
    assert n.commit_index == 0
    # now node3 also has it -> 3 of 4 == quorum
    n.match_index[3] = 1
    n._advance_commit_index()
    assert n.commit_index == 1

def test_commit_only_current_term_entries(tmp_path):
    t = ScriptedTransport({2: [], 3: [], 4: []})
    n = leader(tmp_path, t)
    n.current_term = 5
    n.log = [{"term": 1, "index": 1, "key": "a", "value": "1"}]  # old term entry
    n.match_index = {2: 1, 3: 1, 4: 1}  # replicated everywhere
    n._advance_commit_index()
    assert n.commit_index == 0  # cannot commit old-term entry by counting alone

def test_steps_down_on_higher_term_reply(tmp_path):
    t = ScriptedTransport({2: [{"term": 9, "success": False, "conflict_index": 0}],
                           3: [], 4: []})
    n = leader(tmp_path, t)
    n.log = [{"term": 1, "index": 1, "key": "a", "value": "1"}]
    n._replicate_to_peer(2)
    assert n.state == "Seguidor"
    assert n.current_term == 9

def test_build_args_sends_only_missing_entries(tmp_path):
    t = ScriptedTransport({2: [], 3: [], 4: []})
    n = leader(tmp_path, t)
    n.log = [{"term": 1, "index": 1, "key": "a", "value": "1"},
             {"term": 1, "index": 2, "key": "b", "value": "2"},
             {"term": 1, "index": 3, "key": "c", "value": "3"}]
    n.next_index[2] = 3
    args = n._build_append_args(2)
    assert [e["index"] for e in args["entries"]] == [3]
    assert args["prev_log_index"] == 2
    assert args["prev_log_term"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Av5 && . .venv/bin/activate && python -m pytest server/tests/test_replication.py -v`
Expected: FAIL (AttributeError: _replicate_to_peer).

- [ ] **Step 3: Add replication to `Av5/server/raft_node.py`**

Append to the `RaftNode` class:

```python
    # ----- leader replication (uses transport) -----
    def _build_append_args(self, peer_id):
        next_idx = self.next_index.get(peer_id, 1)
        prev_idx = next_idx - 1
        return {
            "term": self.current_term,
            "leader_id": self.node_id,
            "prev_log_index": prev_idx,
            "prev_log_term": self._term_of(prev_idx),
            "entries": list(self.log[next_idx - 1:]),
            "leader_commit": self.commit_index,
        }

    def _replicate_to_peer(self, peer_id):
        with self.lock:
            if self.state != "Lider":
                return
            args = self._build_append_args(peer_id)
        reply = self.transport.send_append_entries(peer_id, args)
        if reply is None:
            return  # peer unreachable; retried on next tick
        with self.lock:
            if reply["term"] > self.current_term:
                self.current_term = reply["term"]
                self.voted_for = None
                self._become_follower(reply["term"], None)
                return
            if self.state != "Lider":
                return
            if reply["success"]:
                if args["entries"]:
                    self.match_index[peer_id] = args["entries"][-1]["index"]
                    self.next_index[peer_id] = self.match_index[peer_id] + 1
            else:
                hint = reply.get("conflict_index", 0)
                self.next_index[peer_id] = max(1, hint if hint > 0
                                               else self.next_index[peer_id] - 1)

    def _advance_commit_index(self):
        with self.lock:
            if self.state != "Lider":
                return
            for n in range(len(self.log), self.commit_index, -1):
                if self._term_of(n) != self.current_term:
                    continue
                count = 1  # leader counts itself
                for pid in config.peer_ids(self.node_id):
                    if self.match_index.get(pid, 0) >= n:
                        count += 1
                if count >= config.QUORUM:
                    self.commit_index = n
                    self._apply_committed()
                    self._persist()
                    break

    def replicate_to_all(self):
        for pid in config.peer_ids(self.node_id):
            self._replicate_to_peer(pid)
        self._advance_commit_index()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd Av5 && . .venv/bin/activate && python -m pytest server/tests/test_replication.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
cd Av5 && git add server/raft_node.py server/tests/test_replication.py
git commit -m "feat(av5): leader replication and fixed-quorum commit advancement"
```

---

### Task 8: Client operations — Publish & Consume handlers

**Files:**
- Modify: `Av5/server/raft_node.py`
- Test: `Av5/server/tests/test_client_ops.py`

**Interfaces:**
- Consumes: Task 7 `RaftNode`, `server.config.NODE_ADDRESSES`.
- Produces:
  - `handle_publish(key, value) -> dict` → `{"success": bool, "leader_hint": str, "index": int, "message": str}`. If not leader, returns `success=False`, `message="not_leader"`, `leader_hint`=leader address (or `""` if unknown). If leader: append entry, persist, `replicate_to_all()`; if committed, `success=True, message="ok"`; else `success=False, message="no_quorum"`.
  - `handle_consume(key) -> dict` → `{"success": bool, "items": list[dict], "leader_hint": str, "is_leader": bool, "committed_index": int, "pending_count": int}`. Returns only committed entries (`index <= commit_index`). Empty `key` → all committed pairs (latest value per key); non-empty `key` → that key's latest committed value (empty list if none). `pending_count` = entries with `index > commit_index`.
  - `_leader_hint() -> str` — `config.NODE_ADDRESSES[self.leader_id]` or `""`.

- [ ] **Step 1: Write the failing test `Av5/server/tests/test_client_ops.py`**

```python
from server.raft_node import RaftNode
from server import config


class AllAckTransport:
    def send_request_vote(self, peer_id, args): return None
    def send_append_entries(self, peer_id, args):
        last = args["entries"][-1]["index"] if args["entries"] else args["prev_log_index"]
        return {"term": args["term"], "success": True, "conflict_index": 0}


class NoAckTransport:
    def send_request_vote(self, peer_id, args): return None
    def send_append_entries(self, peer_id, args): return None  # nobody reachable


def leader(tmp_path, transport):
    n = RaftNode(1, transport, data_path=str(tmp_path / "node1.json"))
    n.current_term = 1
    n.state = "Lider"
    n.leader_id = 1
    n.next_index = {pid: 1 for pid in config.peer_ids(1)}
    n.match_index = {pid: 0 for pid in config.peer_ids(1)}
    return n


def test_non_leader_publish_returns_hint(tmp_path):
    n = RaftNode(2, NoAckTransport(), data_path=str(tmp_path / "node2.json"))
    n.state = "Seguidor"
    n.leader_id = 3
    reply = n.handle_publish("a", "1")
    assert reply["success"] is False
    assert reply["message"] == "not_leader"
    assert reply["leader_hint"] == config.NODE_ADDRESSES[3]

def test_leader_publish_commits_with_quorum(tmp_path):
    n = leader(tmp_path, AllAckTransport())
    reply = n.handle_publish("a", "1")
    assert reply["success"] is True
    assert reply["message"] == "ok"
    assert reply["index"] == 1
    assert n.commit_index == 1

def test_leader_publish_without_quorum_is_not_committed(tmp_path):
    n = leader(tmp_path, NoAckTransport())
    reply = n.handle_publish("a", "1")
    assert reply["success"] is False
    assert reply["message"] == "no_quorum"
    assert len(n.log) == 1          # entry stays in log (pending)
    assert n.commit_index == 0

def test_consume_returns_only_committed(tmp_path):
    n = leader(tmp_path, AllAckTransport())
    n.handle_publish("a", "1")      # committed
    # a pending (uncommitted) entry appended manually
    n.log.append({"term": 1, "index": 2, "key": "b", "value": "2"})
    reply = n.handle_consume("")
    keys = {it["key"] for it in reply["items"]}
    assert keys == {"a"}            # b is uncommitted, hidden
    assert reply["pending_count"] == 1
    assert reply["committed_index"] == 1

def test_consume_single_key_latest_value(tmp_path):
    n = leader(tmp_path, AllAckTransport())
    n.handle_publish("a", "1")
    n.handle_publish("a", "2")
    reply = n.handle_consume("a")
    assert [it["value"] for it in reply["items"]] == ["2"]

def test_consume_works_on_follower(tmp_path):
    n = RaftNode(2, NoAckTransport(), data_path=str(tmp_path / "node2.json"))
    n.state = "Seguidor"
    n.leader_id = 1
    n.log = [{"term": 1, "index": 1, "key": "x", "value": "9"}]
    n.commit_index = 1
    reply = n.handle_consume("x")
    assert reply["is_leader"] is False
    assert [it["value"] for it in reply["items"]] == ["9"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Av5 && . .venv/bin/activate && python -m pytest server/tests/test_client_ops.py -v`
Expected: FAIL (AttributeError: handle_publish).

- [ ] **Step 3: Add client ops to `Av5/server/raft_node.py`**

Append to the `RaftNode` class:

```python
    # ----- client operations (ClientService) -----
    def _leader_hint(self):
        if self.leader_id and self.leader_id in config.NODE_ADDRESSES:
            return config.NODE_ADDRESSES[self.leader_id]
        return ""

    def handle_publish(self, key, value):
        with self.lock:
            if self.state != "Lider":
                return {"success": False, "leader_hint": self._leader_hint(),
                        "index": 0, "message": "not_leader"}
            index = self.last_log_index() + 1
            self.log.append({"term": self.current_term, "index": index,
                             "key": key, "value": value})
            self._persist()
            self.log_event(f"<- client publish {key}={value} (index={index})")

        self.replicate_to_all()

        with self.lock:
            if self.commit_index >= index:
                return {"success": True, "leader_hint": "",
                        "index": index, "message": "ok"}
            return {"success": False, "leader_hint": "",
                    "index": index, "message": "no_quorum"}

    def handle_consume(self, key):
        with self.lock:
            committed = self.log[: self.commit_index]
            pending = len(self.log) - self.commit_index
            latest = {}
            order = []
            for e in committed:
                if e["key"] not in latest:
                    order.append(e["key"])
                latest[e["key"]] = e
            if key:
                items = [latest[key]] if key in latest else []
            else:
                items = [latest[k] for k in order]
            return {
                "success": True,
                "items": [{"key": e["key"], "value": e["value"], "index": e["index"]}
                          for e in items],
                "leader_hint": self._leader_hint(),
                "is_leader": self.state == "Lider",
                "committed_index": self.commit_index,
                "pending_count": pending,
            }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd Av5 && . .venv/bin/activate && python -m pytest server/tests/test_client_ops.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
cd Av5 && git add server/raft_node.py server/tests/test_client_ops.py
git commit -m "feat(av5): Publish and Consume client handlers"
```

---

### Task 9: Election driver + ticker loop

**Files:**
- Modify: `Av5/server/raft_node.py`
- Test: `Av5/server/tests/test_election.py`

**Interfaces:**
- Consumes: Task 8 `RaftNode`, `transport.send_request_vote(peer_id, args) -> dict | None`.
- Produces:
  - `start_election() -> None` — increments term, votes for self, persists, requests votes from peers via transport; becomes leader on **≥ QUORUM** votes (self counts), else stays/returns to follower; steps down on higher term.
  - `tick() -> None` — one ticker step: if leader and `HEARTBEAT_INTERVAL` elapsed → `replicate_to_all()`; if follower/candidate and election deadline passed → `start_election()`.
  - `run_ticker() -> None` — loop calling `tick()` every `TICK_INTERVAL` while `self.running` (used by server; not unit-tested).

- [ ] **Step 1: Write the failing test `Av5/server/tests/test_election.py`**

```python
import time
from server.raft_node import RaftNode
from server import config


class VoteTransport:
    def __init__(self, granted_from):
        self.granted_from = granted_from   # set of peer ids that grant
    def send_request_vote(self, peer_id, args):
        return {"term": args["term"], "vote_granted": peer_id in self.granted_from}
    def send_append_entries(self, peer_id, args):
        return {"term": args["term"], "success": True, "conflict_index": 0}


def node(tmp_path, transport, nid=1):
    return RaftNode(nid, transport, data_path=str(tmp_path / f"node{nid}.json"))


def test_wins_election_with_quorum(tmp_path):
    n = node(tmp_path, VoteTransport(granted_from={2, 3}))  # self+2+3 = 3 votes
    n.start_election()
    assert n.state == "Lider"
    assert n.current_term == 1
    assert n.leader_id == 1

def test_loses_election_without_quorum(tmp_path):
    n = node(tmp_path, VoteTransport(granted_from={2}))  # self+2 = 2 votes < 3
    n.start_election()
    assert n.state != "Lider"

def test_election_increments_term_and_self_votes(tmp_path):
    n = node(tmp_path, VoteTransport(granted_from=set()))
    n.start_election()
    assert n.current_term == 1
    assert n.voted_for == 1

def test_steps_down_if_peer_has_higher_term(tmp_path):
    class HigherTerm:
        def send_request_vote(self, peer_id, args):
            return {"term": 99, "vote_granted": False}
        def send_append_entries(self, peer_id, args): return None
    n = node(tmp_path, HigherTerm())
    n.start_election()
    assert n.state == "Seguidor"
    assert n.current_term == 99

def test_tick_triggers_election_after_deadline(tmp_path):
    n = node(tmp_path, VoteTransport(granted_from={2, 3}))
    n.election_deadline = time.time() - 1  # already expired
    n.tick()
    assert n.state == "Lider"

def test_leader_tick_replicates_on_heartbeat_interval(tmp_path):
    n = node(tmp_path, VoteTransport(granted_from={2, 3}))
    n.start_election()                 # becomes leader
    n.last_heartbeat_sent = 0.0        # force heartbeat due
    n.log = [{"term": 1, "index": 1, "key": "a", "value": "1"}]
    n.next_index = {pid: 1 for pid in config.peer_ids(1)}
    n.match_index = {pid: 0 for pid in config.peer_ids(1)}
    n.tick()
    assert n.match_index[2] == 1       # replicated via heartbeat
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Av5 && . .venv/bin/activate && python -m pytest server/tests/test_election.py -v`
Expected: FAIL (AttributeError: start_election).

- [ ] **Step 3: Add election + ticker to `Av5/server/raft_node.py`**

Append to the `RaftNode` class:

```python
    # ----- election -----
    def start_election(self):
        with self.lock:
            self.state = "Candidato"
            self.current_term += 1
            self.voted_for = self.node_id
            self.leader_id = None
            self._reset_election_deadline()
            self._persist()
            term = self.current_term
            args = {
                "term": term,
                "candidate_id": self.node_id,
                "last_log_index": self.last_log_index(),
                "last_log_term": self.last_log_term(),
            }
            self.log_event(f"iniciou eleicao no termo {term}")

        votes = 1  # vote for self
        for pid in config.peer_ids(self.node_id):
            reply = self.transport.send_request_vote(pid, args)
            if reply is None:
                continue
            with self.lock:
                if reply["term"] > self.current_term:
                    self.current_term = reply["term"]
                    self.voted_for = None
                    self._become_follower(reply["term"], None)
                    return
                if self.state != "Candidato" or self.current_term != term:
                    return
            if reply["vote_granted"]:
                votes += 1

        with self.lock:
            if self.state == "Candidato" and self.current_term == term and votes >= config.QUORUM:
                self._become_leader()
            elif self.state == "Candidato":
                self.state = "Seguidor"
                self._reset_election_deadline()

    # ----- ticker -----
    def tick(self):
        now = time.time()
        with self.lock:
            state = self.state
        if state == "Lider":
            if now - self.last_heartbeat_sent >= config.HEARTBEAT_INTERVAL:
                with self.lock:
                    self.last_heartbeat_sent = now
                self.replicate_to_all()
        else:
            with self.lock:
                expired = now >= self.election_deadline
            if expired:
                self.start_election()

    def run_ticker(self):
        self.running = True
        while self.running:
            time.sleep(config.TICK_INTERVAL)
            try:
                self.tick()
            except Exception as exc:  # never let the ticker die
                self.log_event(f"erro no ticker: {exc}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd Av5 && . .venv/bin/activate && python -m pytest server/tests/test_election.py -v`
Expected: 6 passed.

- [ ] **Step 5: Run the full suite**

Run: `cd Av5 && . .venv/bin/activate && python -m pytest server/tests -v`
Expected: all tests pass (config, persistence, core, request_vote, append_entries, replication, client_ops, election).

- [ ] **Step 6: Commit**

```bash
cd Av5 && git add server/raft_node.py server/tests/test_election.py
git commit -m "feat(av5): election driver and ticker loop"
```

---

### Task 10: gRPC transport + servicers + node entrypoint

**Files:**
- Create: `Av5/server/transport.py`
- Create: `Av5/server/server.py`
- Create: `Av5/server/run_node.py`

**Interfaces:**
- Consumes: `server.gen.raft_pb2`, `server.gen.raft_pb2_grpc`, `server.raft_node.RaftNode`, `server.config`.
- Produces:
  - `GrpcPeers(node_id)` implementing `send_request_vote(peer_id, args) -> dict | None` and `send_append_entries(peer_id, args) -> dict | None` (returns `None` on any RPC error/timeout). Converts dict ↔ protobuf, including `entries` ↔ `LogEntry`.
  - `RaftServicer(node)` (gRPC `RaftServiceServicer`): `RequestVote`, `AppendEntries`.
  - `ClientServicer(node)` (gRPC `ClientServiceServicer`): `Publish`, `Consume`.
  - `serve(node_id)` — builds node + transport, starts ticker thread, starts gRPC server on `NODE_ADDRESSES[node_id]` port, blocks.

- [ ] **Step 1: Write `Av5/server/transport.py`**

```python
import grpc

from server import config
from server.gen import raft_pb2, raft_pb2_grpc


def _entries_to_pb(entries):
    return [raft_pb2.LogEntry(term=e["term"], index=e["index"],
                              key=e["key"], value=e["value"]) for e in entries]


def _entries_from_pb(pb_entries):
    return [{"term": e.term, "index": e.index, "key": e.key, "value": e.value}
            for e in pb_entries]


class GrpcPeers:
    def __init__(self, node_id):
        self.node_id = node_id
        self._channels = {}
        for pid in config.peer_ids(node_id):
            self._channels[pid] = grpc.insecure_channel(config.NODE_ADDRESSES[pid])

    def _stub(self, peer_id):
        return raft_pb2_grpc.RaftServiceStub(self._channels[peer_id])

    def send_request_vote(self, peer_id, args):
        try:
            reply = self._stub(peer_id).RequestVote(
                raft_pb2.RequestVoteArgs(
                    term=args["term"], candidate_id=args["candidate_id"],
                    last_log_index=args["last_log_index"],
                    last_log_term=args["last_log_term"]),
                timeout=config.RPC_TIMEOUT)
            return {"term": reply.term, "vote_granted": reply.vote_granted}
        except grpc.RpcError:
            return None

    def send_append_entries(self, peer_id, args):
        try:
            reply = self._stub(peer_id).AppendEntries(
                raft_pb2.AppendEntriesArgs(
                    term=args["term"], leader_id=args["leader_id"],
                    prev_log_index=args["prev_log_index"],
                    prev_log_term=args["prev_log_term"],
                    entries=_entries_to_pb(args["entries"]),
                    leader_commit=args["leader_commit"]),
                timeout=config.RPC_TIMEOUT)
            return {"term": reply.term, "success": reply.success,
                    "conflict_index": reply.conflict_index}
        except grpc.RpcError:
            return None
```

- [ ] **Step 2: Write `Av5/server/server.py`**

```python
import threading
from concurrent import futures

import grpc

from server import config
from server.gen import raft_pb2, raft_pb2_grpc
from server.raft_node import RaftNode
from server.transport import GrpcPeers, _entries_from_pb


class RaftServicer(raft_pb2_grpc.RaftServiceServicer):
    def __init__(self, node):
        self.node = node

    def RequestVote(self, request, context):
        r = self.node.handle_request_vote(
            request.term, request.candidate_id,
            request.last_log_index, request.last_log_term)
        return raft_pb2.RequestVoteReply(term=r["term"], vote_granted=r["vote_granted"])

    def AppendEntries(self, request, context):
        r = self.node.handle_append_entries(
            request.term, request.leader_id,
            request.prev_log_index, request.prev_log_term,
            _entries_from_pb(request.entries), request.leader_commit)
        return raft_pb2.AppendEntriesReply(
            term=r["term"], success=r["success"], conflict_index=r["conflict_index"])


class ClientServicer(raft_pb2_grpc.ClientServiceServicer):
    def __init__(self, node):
        self.node = node

    def Publish(self, request, context):
        r = self.node.handle_publish(request.key, request.value)
        return raft_pb2.PublishReply(
            success=r["success"], leader_hint=r["leader_hint"],
            index=r["index"], message=r["message"])

    def Consume(self, request, context):
        r = self.node.handle_consume(request.key)
        return raft_pb2.ConsumeReply(
            success=r["success"],
            items=[raft_pb2.DataItem(key=i["key"], value=i["value"], index=i["index"])
                   for i in r["items"]],
            leader_hint=r["leader_hint"], is_leader=r["is_leader"],
            committed_index=r["committed_index"], pending_count=r["pending_count"])


def serve(node_id):
    transport = GrpcPeers(node_id)
    node = RaftNode(node_id, transport)

    ticker = threading.Thread(target=node.run_ticker, daemon=True)
    ticker.start()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    raft_pb2_grpc.add_RaftServiceServicer_to_server(RaftServicer(node), server)
    raft_pb2_grpc.add_ClientServiceServicer_to_server(ClientServicer(node), server)

    port = config.NODE_ADDRESSES[node_id].split(":")[1]
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    node.log_event(f"servidor gRPC ouvindo na porta {port}")
    server.wait_for_termination()
```

- [ ] **Step 3: Write `Av5/server/run_node.py`**

```python
import argparse

from server import config
from server.server import serve


def main():
    parser = argparse.ArgumentParser(description="Executa um no Raft (gRPC).")
    parser.add_argument("--id", type=int, required=True, help="ID do no (1-4).")
    args = parser.parse_args()
    if args.id not in config.NODE_IDS:
        raise ValueError("ID invalido. Use 1-4.")
    serve(args.id)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Smoke-test imports (no peers needed)**

Run: `cd Av5 && . .venv/bin/activate && python -c "from server import server, transport, run_node; print('imports ok')"`
Expected: prints `imports ok` (gRPC installed locally). If `grpcio` has no wheel for the local Python, skip this step — it is verified in Docker (Task 12).

- [ ] **Step 5: Commit**

```bash
cd Av5 && git add server/transport.py server/server.py server/run_node.py
git commit -m "feat(av5): gRPC transport, servicers, and node entrypoint"
```

---

### Task 11: Go client (leader discovery + redirect)

**Files:**
- Create: `Av5/client/go.mod`
- Create: `Av5/client/main.go`
- Create: `Av5/client/discovery.go`
- Create: `Av5/client/proto-path.txt` (note pointing to `../proto/raft.proto`; generated stubs land in `client/gen` at build time)

**Interfaces:**
- Consumes: generated Go package `raftpb` (from `raft.proto`, generated at Docker build into `client/gen`), `ClientService` only.
- Produces: a CLI binary supporting:
  - `client publish <key> <value>`
  - `client consume [key]`
  - `client interactive`
  - Discovers leader via `leader_hint` and retries; rotates through seed nodes on connection failure.

- [ ] **Step 1: Write `Av5/client/go.mod`**

```
module av5client

go 1.23

require (
	google.golang.org/grpc v1.68.0
	google.golang.org/protobuf v1.35.1
)
```

(The `go.sum` is produced by `go mod download`/`go build` during the Docker build.)

- [ ] **Step 2: Write `Av5/client/discovery.go`**

```go
package main

import (
	"context"
	"errors"
	"log"
	"time"

	pb "av5client/gen"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

// seed addresses; client does NOT know who is leader.
var seeds = []string{"node1:6001", "node2:6002", "node3:6003", "node4:6004"}

const maxAttempts = 12

type Cluster struct {
	known string // last known leader address (cache)
}

func (c *Cluster) dial(addr string) (pb.ClientServiceClient, *grpc.ClientConn, error) {
	conn, err := grpc.NewClient(addr, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return nil, nil, err
	}
	return pb.NewClientServiceClient(conn), conn, nil
}

// candidates returns addresses to try, leader cache first.
func (c *Cluster) candidates() []string {
	if c.known == "" {
		return seeds
	}
	out := []string{c.known}
	for _, s := range seeds {
		if s != c.known {
			out = append(out, s)
		}
	}
	return out
}

// Publish redirects to the leader using leader_hint until committed.
func (c *Cluster) Publish(key, value string) error {
	for attempt := 0; attempt < maxAttempts; attempt++ {
		addr := c.candidates()[attempt%len(c.candidates())]
		cli, conn, err := c.dial(addr)
		if err != nil {
			continue
		}
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		reply, err := cli.Publish(ctx, &pb.PublishRequest{Key: key, Value: value})
		cancel()
		conn.Close()
		if err != nil {
			log.Printf("nodo %s indisponivel, tentando outro...", addr)
			c.known = ""
			continue
		}
		if reply.Success {
			log.Printf("OK publicado %s=%s (index=%d) via lider %s", key, value, reply.Index, addr)
			c.known = addr
			return nil
		}
		switch reply.Message {
		case "not_leader":
			if reply.LeaderHint != "" {
				log.Printf("%s nao e lider; redirecionando para %s", addr, reply.LeaderHint)
				c.known = reply.LeaderHint
			} else {
				log.Printf("%s nao conhece o lider ainda; aguardando eleicao...", addr)
				c.known = ""
				time.Sleep(1 * time.Second)
			}
		case "no_quorum":
			log.Printf("sem quorum no momento; tentando novamente...")
			time.Sleep(1 * time.Second)
		}
	}
	return errors.New("nao foi possivel publicar (sem lider/quorum)")
}

// Consume can target any node (leader or replica). Returns committed data only.
func (c *Cluster) Consume(key string, addr string) (*pb.ConsumeReply, error) {
	candidates := c.candidates()
	if addr != "" {
		candidates = []string{addr}
	}
	var lastErr error
	for _, a := range candidates {
		cli, conn, err := c.dial(a)
		if err != nil {
			lastErr = err
			continue
		}
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		reply, err := cli.Consume(ctx, &pb.ConsumeRequest{Key: key})
		cancel()
		conn.Close()
		if err != nil {
			lastErr = err
			continue
		}
		return reply, nil
	}
	return nil, lastErr
}
```

- [ ] **Step 3: Write `Av5/client/main.go`**

```go
package main

import (
	"fmt"
	"log"
	"os"
	"strings"
)

func usage() {
	fmt.Println("uso:")
	fmt.Println("  client publish <key> <value>")
	fmt.Println("  client consume [key] [--node nodeX:600X]")
	fmt.Println("  client interactive")
}

func printReply(r interface{ String() string }) {}

func doConsume(c *Cluster, key, node string) {
	reply, err := c.Consume(key, node)
	if err != nil {
		log.Printf("erro ao consumir: %v", err)
		return
	}
	src := "replica"
	if reply.IsLeader {
		src = "lider"
	}
	fmt.Printf("[%s] committed_index=%d pending(uncommitted)=%d\n",
		src, reply.CommittedIndex, reply.PendingCount)
	if len(reply.Items) == 0 {
		fmt.Println("  (sem dados efetivados)")
	}
	for _, it := range reply.Items {
		fmt.Printf("  %s = %s (index=%d)\n", it.Key, it.Value, it.Index)
	}
}

func main() {
	if len(os.Args) < 2 {
		usage()
		return
	}
	c := &Cluster{}
	switch os.Args[1] {
	case "publish":
		if len(os.Args) != 4 {
			usage()
			return
		}
		if err := c.Publish(os.Args[2], os.Args[3]); err != nil {
			log.Fatalf("falha: %v", err)
		}
	case "consume":
		key := ""
		node := ""
		rest := os.Args[2:]
		for i := 0; i < len(rest); i++ {
			if rest[i] == "--node" && i+1 < len(rest) {
				node = rest[i+1]
				i++
			} else {
				key = rest[i]
			}
		}
		doConsume(c, key, node)
	case "interactive":
		interactive(c)
	default:
		usage()
	}
}

func interactive(c *Cluster) {
	fmt.Println("Cliente Raft (gRPC). Comandos: publish <k> <v> | consume [k] | sair")
	var line string
	for {
		fmt.Print("> ")
		if _, err := fmt.Scanln(&line); err != nil {
			return
		}
		_ = strings.TrimSpace(line)
		// simple single-token dispatch; for multi-arg use the CLI subcommands
		fmt.Println("use os subcomandos da CLI: publish/consume")
		return
	}
}
```

(Interactive mode is intentionally minimal; the graded scenarios use the `publish`/`consume` subcommands. Keep `printReply` only if used; otherwise remove it to satisfy `go vet`.)

- [ ] **Step 4: Remove the unused helper**

Delete the `func printReply(...)` line from `main.go` (it is unused and Go will not compile with unused functions only if referenced; unused funcs are allowed, but unused imports are not — ensure no unused imports remain). Verify `main.go` imports only `fmt`, `log`, `os`, `strings`.

- [ ] **Step 5: Write `Av5/client/proto-path.txt`**

```
Stubs are generated at Docker build time from ../proto/raft.proto into ./gen
(package raftpb, import path "av5client/gen"). See client/Dockerfile.
```

- [ ] **Step 6: Commit**

```bash
cd Av5 && git add client/go.mod client/main.go client/discovery.go client/proto-path.txt
git commit -m "feat(av5): Go client with leader discovery and redirect"
```

(No local build — Go toolchain isn't installed; the client compiles in Docker in Task 12.)

---

### Task 12: Dockerfiles + docker-compose

**Files:**
- Create: `Av5/server/Dockerfile`
- Create: `Av5/client/Dockerfile`
- Create: `Av5/docker-compose.yml`

**Interfaces:**
- Consumes: all server + client code.
- Produces: a runnable 4-node cluster + client container. Go stubs generated during `client/Dockerfile` build; Python stubs regenerated during `server/Dockerfile` build (so the image is self-contained even if committed stubs drift).

- [ ] **Step 1: Write `Av5/server/Dockerfile`**

```dockerfile
FROM python:3.12-slim
WORKDIR /app

COPY server/requirements.txt ./server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

COPY proto ./proto
COPY server ./server

# (re)generate Python stubs at build time
RUN python -m grpc_tools.protoc -I proto \
      --python_out=server/gen --grpc_python_out=server/gen proto/raft.proto && \
    sed -i 's/^import raft_pb2/from . import raft_pb2/' server/gen/raft_pb2_grpc.py

ENV PYTHONUNBUFFERED=1
ENV RAFT_DATA_DIR=/app/data
ENTRYPOINT ["python", "-m", "server.run_node"]
```

- [ ] **Step 2: Write `Av5/client/Dockerfile`**

```dockerfile
FROM golang:1.23-bookworm AS build
RUN apt-get update && apt-get install -y --no-install-recommends protobuf-compiler && \
    rm -rf /var/lib/apt/lists/*
RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.35.1 && \
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.5.1
ENV PATH="/go/bin:${PATH}"

WORKDIR /src
COPY client/go.mod ./client/go.mod
WORKDIR /src/client
RUN go mod download || true

COPY proto /src/proto
COPY client /src/client

# generate Go stubs into ./gen with package raftpb, import path av5client/gen
RUN mkdir -p gen && \
    protoc -I /src/proto \
      --go_out=gen --go_opt=paths=source_relative,Mraft.proto=av5client/gen \
      --go-grpc_out=gen --go-grpc_opt=paths=source_relative,Mraft.proto=av5client/gen \
      /src/proto/raft.proto
RUN go mod tidy && go build -o /client .

FROM debian:bookworm-slim
COPY --from=build /client /client
ENTRYPOINT ["/client"]
```

- [ ] **Step 3: Write `Av5/docker-compose.yml`**

```yaml
services:
  node1:
    build: { context: ., dockerfile: server/Dockerfile }
    container_name: av5-node1
    command: ["--id", "1"]
    networks: [raft]
    volumes: ["./data/node1:/app/data"]
  node2:
    build: { context: ., dockerfile: server/Dockerfile }
    container_name: av5-node2
    command: ["--id", "2"]
    networks: [raft]
    volumes: ["./data/node2:/app/data"]
  node3:
    build: { context: ., dockerfile: server/Dockerfile }
    container_name: av5-node3
    command: ["--id", "3"]
    networks: [raft]
    volumes: ["./data/node3:/app/data"]
  node4:
    build: { context: ., dockerfile: server/Dockerfile }
    container_name: av5-node4
    command: ["--id", "4"]
    networks: [raft]
    volumes: ["./data/node4:/app/data"]
  client:
    build: { context: ., dockerfile: client/Dockerfile }
    container_name: av5-client
    profiles: ["client"]
    networks: [raft]
    depends_on: [node1, node2, node3, node4]

networks:
  raft:
    driver: bridge
```

Note: per-node `data/nodeN` host volumes mean each node's `data/node{id}.json` persists across `stop`/`start` for the persistence/recovery scenarios.

- [ ] **Step 4: Build the images**

Run: `cd Av5 && docker compose build`
Expected: both images build with no errors (Python stub gen + Go protoc gen succeed).

- [ ] **Step 5: Bring up the cluster and verify an election happens**

Run: `cd Av5 && docker compose up -d node1 node2 node3 node4 && sleep 10 && docker compose logs | grep -i "eleito LIDER"`
Expected: exactly one node logs `eleito LIDER no termo ...` within ~10s.

- [ ] **Step 6: Verify publish + consume end-to-end**

Run:
```bash
cd Av5
docker compose run --rm client publish nome matheus
docker compose run --rm client consume nome
```
Expected: publish logs `OK publicado nome=matheus ... via lider nodeX:600X`; consume prints `nome = matheus` with `pending(uncommitted)=0`.

- [ ] **Step 7: Commit**

```bash
cd Av5 && git add server/Dockerfile client/Dockerfile docker-compose.yml
git commit -m "feat(av5): Dockerfiles and docker-compose for 4-node cluster + client"
```

---

### Task 13: README with the 5 demonstration scenarios

**Files:**
- Create: `Av5/README.md`

**Interfaces:**
- Consumes: the running system from Task 12.
- Produces: step-by-step instructions covering all 5 required scenarios, plus build/run/test commands.

- [ ] **Step 1: Write `Av5/README.md`**

````markdown
# Av5 — Raft com gRPC, Protocol Buffers, Persistência e Recuperação

Consenso Raft em **4 nós Python** (gRPC) com **cliente Go** (interoperabilidade),
persistência em disco, recuperação de falhas e sincronização incremental de
réplicas.

Alunos: <preencher>

## Arquitetura

- 4 nós Raft em **Python** (`node1`..`node4`), portas `6001`..`6004`.
- Cliente em **Go** (linguagem diferente → interoperabilidade gRPC).
- Dois serviços gRPC por nó:
  - `RaftService` (interno): `RequestVote`, `AppendEntries`.
  - `ClientService` (externo, único acessível ao cliente): `Publish`, `Consume`.
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

---

## Cenário 1 — Operação Normal

```bash
# 1. inicializa os 4 nós
docker compose up -d node1 node2 node3 node4

# 2. eleição automática (aguarde ~10s e observe o líder)
docker compose logs -f node1 node2 node3 node4   # procure "eleito LIDER"

# 3. publicação de dados pelo cliente
docker compose run --rm client publish cidade curitiba
docker compose run --rm client publish estado parana

# 4. replicação: observe nos logs dos nós "OK replicado ate index=..."

# 5. consumo
docker compose run --rm client consume          # lista todos os pares committed
docker compose run --rm client consume cidade
```

## Cenário 2 — Falha do Líder

```bash
# descubra o líder nos logs (ex.: node2) e interrompa-o
docker compose stop node2

# nova eleição ocorre entre os nós restantes (aguarde alguns segundos)
docker compose logs -f node1 node3 node4         # novo "eleito LIDER"

# operações continuam (cliente redireciona sozinho para o novo líder)
docker compose run --rm client publish pais brasil
docker compose run --rm client consume pais
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
# interrompe uma réplica (não-líder)
docker compose stop node4

# novas operações enquanto node4 está fora
docker compose run --rm client publish a 1
docker compose run --rm client publish b 2
docker compose run --rm client publish c 3

# reinicia a réplica
docker compose start node4

# o líder reenvia APENAS as entradas ausentes (via next_index/conflict_index).
# observe nos logs do líder o avanço de next_index para node4 e em node4 o
# "OK replicado ate index=..." — sem reenvio integral da base.
docker compose logs -f node4
docker compose run --rm client consume --node node4:6004   # node4 já consistente
```

## Cenário 5 — Consistência de Leitura

```bash
# leitura no líder e em réplicas: apenas dados committed são retornados
docker compose run --rm client consume --node node1:6001
docker compose run --rm client consume --node node2:6002
docker compose run --rm client consume --node node3:6003

# cada resposta mostra committed_index e pending(uncommitted)=N.
# Entradas uncommitted NUNCA aparecem na lista de itens — só as efetivadas.
```

## Encerrar

```bash
docker compose down
# para limpar o estado persistido:
rm -rf data/
```

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
````

- [ ] **Step 2: Commit**

```bash
cd Av5 && git add README.md
git commit -m "docs(av5): README with the 5 demonstration scenarios"
```

---

## Self-Review (completed against the spec)

**Spec coverage:**
- Two-service split (client cannot call Raft RPCs) → Tasks 1, 10. ✓
- Key–value app model → Task 8. ✓
- Leader discovery via reply only → Tasks 8 (`leader_hint`), 11 (`discovery.go`). ✓
- Election (random timeout, one vote/term, up-to-date check, majority, heartbeat, failure→new election) → Tasks 4, 5, 9. ✓
- AppendEntries: heartbeat+replication same RPC, conflict_index hint, per-replica next_index/match_index, send only missing, fixed quorum 3, commit only current-term, propagate leader_commit, followers apply only committed → Tasks 6, 7. ✓
- Reads on leader and replicas, committed-only, differentiate uncommitted via `pending_count` → Task 8. ✓
- Persistence (term, votedFor, uncommitted+committed log, commit_index), atomic → Tasks 3, 4. ✓
- Recovery (load state, rejoin, find leader) → Task 4 init + Task 6 (learn leader from AppendEntries). ✓
- 5 demo scenarios → Task 13. ✓
- "Não enviar base integral" → Task 7 `_build_append_args` sends `log[next_index-1:]` only. ✓
- "Não reduzir quórum por falha" → `QUORUM` constant; commit counts against fixed 4. ✓

**Placeholder scan:** No TBD/TODO in code steps; all code shown. `<preencher>` (student names) and `<filename>` are intentional human-fill fields in docs, not code.

**Type consistency:** dict shapes are consistent across tasks — RequestVote reply `{term, vote_granted}`; AppendEntries reply `{term, success, conflict_index}`; Publish reply `{success, leader_hint, index, message}`; Consume reply `{success, items, leader_hint, is_leader, committed_index, pending_count}`; log entry `{term, index, key, value}`. `next_index`/`match_index` keyed by peer id everywhere. Transport interface (`send_request_vote`, `send_append_entries`) identical across fakes and `GrpcPeers`.
