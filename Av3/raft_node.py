import random
import threading
import time
from typing import Dict, List, Optional, Tuple

import Pyro5.api

NODE_IDS = [1, 2, 3, 4]
NODE_PORTS = {1: 5001, 2: 5002, 3: 5003, 4: 5004}
NODE_OBJECT_IDS = {
    1: "raft.node1",
    2: "raft.node2",
    3: "raft.node3",
    4: "raft.node4",
}
NAMESERVER_HOST = "localhost"
NAMESERVER_PORT = 9090
LEADER_NS_NAME = "Lider"


def build_uri(node_id: int) -> str:
    return f"PYRO:{NODE_OBJECT_IDS[node_id]}@localhost:{NODE_PORTS[node_id]}"


@Pyro5.api.behavior(instance_mode="single")
class RaftNode:
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.uri = build_uri(node_id)
        self.peers: Dict[int, str] = {
            peer_id: build_uri(peer_id) for peer_id in NODE_IDS if peer_id != node_id
        }

        self.state = "Follower"
        self.current_term = 0
        self.voted_for: Optional[int] = None
        self.log: List[Dict] = []
        self.commit_index = 0
        self.last_applied = 0
        self.leader_id: Optional[int] = None

        self.election_timeout_range = (3.0, 6.0)
        self.heartbeat_interval = 1.0
        self.election_deadline = 0.0
        self.last_heartbeat_sent = 0.0
        self.next_index: Dict[int, int] = {}
        self.peer_alive: Dict[int, bool] = dict.fromkeys(self.peers, True)

        self.running = False
        self.lock = threading.RLock()
        self.daemon: Optional[Pyro5.api.Daemon] = None

    def start(self) -> None:
        self._reset_election_deadline()
        self.daemon = Pyro5.api.Daemon(host="localhost", port=NODE_PORTS[self.node_id])
        self.daemon.register(self, objectId=NODE_OBJECT_IDS[self.node_id])
        self.running = True

        ticker = threading.Thread(target=self._ticker_loop, daemon=True)
        ticker.start()

        print(
            f"node{self.node_id}: iniciado em {self.uri} | estado: {self.state}",
            flush=True,
        )
        self.daemon.requestLoop(loopCondition=lambda: self.running)

    def stop(self) -> None:
        with self.lock:
            self.running = False
        if self.daemon:
            self.daemon.shutdown()

    def _reset_election_deadline(self) -> None:
        self.election_deadline = time.time() + random.uniform(*self.election_timeout_range)

    def _ticker_loop(self) -> None:
        while True:
            with self.lock:
                if not self.running:
                    return
                state = self.state
                now = time.time()
                deadline = self.election_deadline

            if state == "Lider":
                if now - self.last_heartbeat_sent >= self.heartbeat_interval:
                    self._send_heartbeats()
            else:
                if now >= deadline:
                    self._start_election()

            time.sleep(0.1)

    def _last_log_info(self) -> Tuple[int, int]:
        if not self.log:
            return 0, 0
        last = self.log[-1]
        return last["index"], last["term"]

    def _is_candidate_log_up_to_date(self, last_log_index: int, last_log_term: int) -> bool:
        my_last_index, my_last_term = self._last_log_info()
        if last_log_term != my_last_term:
            return last_log_term > my_last_term
        return last_log_index >= my_last_index

    def _start_election(self) -> None:
        with self.lock:
            self.state = "Candidato"
            self.current_term += 1
            term_started = self.current_term
            self.voted_for = self.node_id
            self.leader_id = None
            self._reset_election_deadline()
            last_log_index, last_log_term = self._last_log_info()

        print(f"node{self.node_id}: candidatou-se no termo {term_started}", flush=True)

        votes, alive_nodes = self._collect_votes(term_started, last_log_index, last_log_term)
        if votes < 0:
            return

        majority = (alive_nodes // 2) + 1
        with self.lock:
            if self.state != "Candidato" or self.current_term != term_started:
                return
            if votes >= majority:
                self._become_leader()
            else:
                self._become_follower(self.current_term, None)

    def _collect_votes(self, term: int, last_idx: int, last_term: int) -> Tuple[int, int]:
        votes = 1
        alive_nodes = 1
        for peer_id, peer_uri in self.peers.items():
            try:
                print(f"node{self.node_id} -> node{peer_id}: PEDIU VOTO no termo {term}", flush=True)
                with Pyro5.api.Proxy(peer_uri) as proxy:
                    resp = proxy.request_vote(term, self.node_id, last_idx, last_term)
                alive_nodes += 1
                if resp and isinstance(resp, dict):
                    if resp.get("term", 0) > term:
                        self._become_follower(resp["term"], None)
                        return -1, alive_nodes
                    if resp.get("vote_granted"):
                        votes += 1
            except Exception as exc:
                if self.peer_alive.get(peer_id, True):
                    print(f"node{self.node_id} -> node{peer_id}: falha ao solicitar voto: {exc}", flush=True)
                    self.peer_alive[peer_id] = False
        return votes, alive_nodes

    def _become_leader(self) -> None:
        if not self._register_as_leader():
            print(f"node{self.node_id}: falha critica ao registrar no Name Server. Voltando a Follower.", flush=True)
            self._become_follower(self.current_term, None)
            return

        self.state = "Lider"
        self.leader_id = self.node_id
        self.last_heartbeat_sent = 0.0
        self.next_index = {p_id: len(self.log) + 1 for p_id in self.peers}
        
        print(f"node{self.node_id}: eleito LIDER no termo {self.current_term} (registrado no Name Server como '{LEADER_NS_NAME}')", flush=True)

    def _become_follower(self, new_term: int, leader_id: Optional[int]) -> None:
        self.state = "Follower"
        self.current_term = max(self.current_term, new_term)
        self.voted_for = None
        self.leader_id = leader_id
        self._reset_election_deadline()

    def _register_as_leader(self) -> bool:
        try:
            with Pyro5.api.locate_ns(host=NAMESERVER_HOST, port=NAMESERVER_PORT) as ns:
                ns.register(LEADER_NS_NAME, self.uri, safe=False)
                return True
        except Exception as exc:
            print(f"node{self.node_id}: erro ao registrar lider no Name Server: {exc}", flush=True)
            return False

    def _send_heartbeats(self) -> None:
        with self.lock:
            if self.state != "Lider":
                return
            term = self.current_term
            leader_commit = self.commit_index
            self.last_heartbeat_sent = time.time()

        for peer_id, peer_uri in self.peers.items():
            self._send_append_entries_to_peer(peer_id, peer_uri, term, leader_commit)

    def _send_append_entries_to_peer(self, peer_id: int, peer_uri: str, term: int, commit: int) -> None:
        with self.lock:
            next_idx = self.next_index.get(peer_id, 1)
            prev_idx = next_idx - 1
            prev_term = self.log[prev_idx - 1]["term"] if prev_idx > 0 else 0
            entries = self.log[next_idx - 1 :]

        try:
            if entries and self.peer_alive.get(peer_id, True):
                print(f"node{self.node_id} -> node{peer_id}: APPEND_ENTRIES index={entries[0]['index']} command={entries[0]['command']} termo {term}", flush=True)
                
            with Pyro5.api.Proxy(peer_uri) as proxy:
                resp = proxy.append_entries(term, self.node_id, prev_idx, prev_term, entries, commit)
                self._handle_append_entries_resp(peer_id, resp, term)
        except Exception as exc:
            if self.peer_alive.get(peer_id, True):
                print(f"node{self.node_id} -> node{peer_id}: conexao perdida: {exc}", flush=True)
                self.peer_alive[peer_id] = False

    def _handle_append_entries_resp(self, peer_id: int, resp: Optional[Dict], term: int) -> None:
        self.peer_alive[peer_id] = True
        if not resp or not isinstance(resp, dict):
            return
        if resp.get("term", 0) > term:
            self._become_follower(resp["term"], None)
            return
        with self.lock:
            if resp.get("success"):
                self.next_index[peer_id] = len(self.log) + 1
            else:
                self.next_index[peer_id] = max(1, self.next_index[peer_id] - 1)

    def _apply_entries(self, silent: bool = False) -> None:
        while self.last_applied < self.commit_index:
            entry = self.log[self.last_applied]
            self.last_applied += 1
            if not silent:
                print(
                    f"node{self.node_id}: COMMITTED index={entry['index']} command={entry['command']}",
                    flush=True,
                )

    def _replicate_entry(self, entry: Dict) -> bool:
        with self.lock:
            term = self.current_term
            leader_commit = self.commit_index
            prev_idx = entry["index"] - 1
            prev_term = self.log[prev_idx - 1]["term"] if prev_idx > 0 else 0

        acks = 1
        alive_nodes = 1
        for p_id, p_uri in self.peers.items():
            if self._send_entry_to_peer(p_id, p_uri, term, entry, prev_idx, prev_term, leader_commit):
                acks += 1
            if self.peer_alive.get(p_id, True):
                alive_nodes += 1

        majority = (alive_nodes // 2) + 1
        success = acks >= majority
        if not success:
            print(f"node{self.node_id}: falha ao replicar index={entry['index']} (acks={acks}, maioria={majority})", flush=True)
        return success

    def _send_entry_to_peer(self, peer_id: int, peer_uri: str, term: int, entry: Dict, prev_idx: int, prev_term: int, commit: int) -> bool:
        if not self.peer_alive.get(peer_id, True):
            print(f"node{self.node_id} -> node{peer_id}: APPEND_ENTRIES (falhou: offline)", flush=True)
            return False
        try:
            print(f"node{self.node_id} -> node{peer_id}: APPEND_ENTRIES index={entry['index']} command={entry['command']}", flush=True)
            with Pyro5.api.Proxy(peer_uri) as proxy:
                call = proxy.append_entries(term, self.node_id, prev_idx, prev_term, [entry], commit)
            if call and isinstance(call, dict):
                if call.get("term", 0) > term:
                    self._become_follower(call["term"], None)
                    return False
                if call.get("success"):
                    print(f"node{peer_id} -> node{self.node_id}: OK index={entry['index']}", flush=True)
                    with self.lock:
                        self.next_index[peer_id] = entry["index"] + 1
                    return True
        except Exception as exc:
            if self.peer_alive.get(peer_id, True):
                print(f"node{self.node_id} -> node{peer_id}: replicacao falhou: {exc}", flush=True)
                self.peer_alive[peer_id] = False
        return False

    def _broadcast_commit(self, commit_index: int) -> None:
        with self.lock:
            term = self.current_term
        for peer_id, peer_uri in self.peers.items():
            if not self.peer_alive.get(peer_id, True):
                print(f"node{self.node_id} -> node{peer_id}: COMMIT (falhou: offline)", flush=True)
                continue
            try:
                print(f"node{self.node_id} -> node{peer_id}: COMMIT index={commit_index}", flush=True)
                with Pyro5.api.Proxy(peer_uri) as proxy:
                    proxy.commit_up_to(term, self.node_id, commit_index)
            except Exception as exc:
                print(
                    f"node{self.node_id} -> node{peer_id}: falha ao enviar commit: {exc}",
                    flush=True,
                )

    @Pyro5.api.expose
    def request_vote(
        self, term: int, candidate_id: int, last_log_index: int, last_log_term: int
    ) -> Dict:
        with self.lock:
            if term < self.current_term:
                return {"term": self.current_term, "vote_granted": False}

            if term > self.current_term:
                self._become_follower(term, None)

            can_vote = self.voted_for is None or self.voted_for == candidate_id
            up_to_date = self._is_candidate_log_up_to_date(last_log_index, last_log_term)

            if can_vote and up_to_date:
                self.voted_for = candidate_id
                self._reset_election_deadline()
                print(
                    f"node{self.node_id} -> node{candidate_id}: VOTO em node{candidate_id} no termo {self.current_term}",
                    flush=True,
                )
                return {"term": self.current_term, "vote_granted": True}

            return {"term": self.current_term, "vote_granted": False}

    @Pyro5.api.expose
    def append_entries(
        self,
        term: int,
        leader_id: int,
        prev_log_index: int,
        prev_log_term: int,
        entries: List[Dict],
        leader_commit: int,
    ) -> Dict:
        with self.lock:
            if term < self.current_term:
                return {"term": self.current_term, "success": False}

            if term > self.current_term or self.state != "Follower":
                self._become_follower(term, leader_id)
            else:
                self.leader_id = leader_id
                self._reset_election_deadline()

            if not self._check_prev_log(prev_log_index, prev_log_term):
                return {"term": self.current_term, "success": False}

            self._sync_log(entries)

            if leader_commit > self.commit_index:
                new_commit = min(leader_commit, len(self.log))
                if new_commit > self.commit_index:
                    entry = self.log[new_commit - 1]
                    print(f"node{leader_id} -> node{self.node_id}: COMMIT index={new_commit}", flush=True)
                    self.commit_index = new_commit
                    print(f"node{self.node_id} -> node{leader_id}: COMMITTED index={self.commit_index} command={entry['command']}", flush=True)
                    self._apply_entries(silent=True)

            return {"term": self.current_term, "success": True}

    def _sync_log(self, entries: List[Dict]) -> None:
        for entry in entries:
            idx = entry["index"]
            if idx <= len(self.log):
                if self.log[idx - 1]["term"] != entry["term"]:
                    self.log = self.log[: idx - 1]
                    self.log.append(entry)
            else:
                self.log.append(entry)

    def _check_prev_log(self, prev_log_index: int, prev_log_term: int) -> bool:
        if prev_log_index > len(self.log):
            return False

        if prev_log_index > 0:
            local_prev_term = self.log[prev_log_index - 1]["term"]
            if local_prev_term != prev_log_term:
                self.log = self.log[: prev_log_index - 1]
                return False
            
        return True

    @Pyro5.api.expose
    @Pyro5.api.oneway
    def commit_up_to(self, term: int, leader_id: int, commit_index: int) -> None:
        with self.lock:
            if term < self.current_term:
                return
            self._become_follower(term, leader_id)
            if commit_index > self.commit_index:
                self.commit_index = min(commit_index, len(self.log))
                entry = self.log[self.commit_index - 1]
                print(f"node{self.node_id} -> node{leader_id}: COMMITTED index={self.commit_index} command={entry['command']}", flush=True)
                self._apply_entries(silent=True)

    @Pyro5.api.expose
    def client_command(self, command: str) -> Dict:
        with self.lock:
            if self.state != "Lider":
                leader_uri = build_uri(self.leader_id) if self.leader_id else None
                return {
                    "success": False,
                    "reason": "not_leader",
                    "leader_uri": leader_uri,
                }

            entry = {
                "term": self.current_term,
                "index": len(self.log) + 1,
                "command": command,
            }
            self.log.append(entry)
            print(
                f"client -> node{self.node_id}: command={entry['command']}",
                flush=True,
            )

        committed = self._replicate_entry(entry)
        if not committed:
            return {
                "success": False,
                "reason": "no_majority",
                "term": entry["term"],
                "index": entry["index"],
            }

        with self.lock:
            self.commit_index = entry["index"]
            self._apply_entries()

        self._broadcast_commit(self.commit_index)
        return {
            "success": True,
            "term": entry["term"],
            "index": entry["index"],
            "command": command,
        }

    @Pyro5.api.expose
    def get_status(self) -> Dict:
        with self.lock:
            return {
                "node_id": self.node_id,
                "state": self.state,
                "term": self.current_term,
                "leader_id": self.leader_id,
                "commit_index": self.commit_index,
                "log_size": len(self.log),
            }
