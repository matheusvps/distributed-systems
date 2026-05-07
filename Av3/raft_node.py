import random
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

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

        self.state = "Seguidor"
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
        self.ns_registered = False
        self.last_commit_log_sent: Dict[int, int] = dict.fromkeys(NODE_IDS, 0)

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

        self._log(f"iniciado em {self.uri}")
        self.daemon.requestLoop(loopCondition=lambda: self.running)

    def _log(self, msg: str, peer_id: Optional[int] = None) -> None:
        prefix = f"node{self.node_id} [{self.state}]"
        if peer_id is not None:
            print(f"{prefix} -> node{peer_id}: {msg}", flush=True)
        else:
            print(f"{prefix}: {msg}", flush=True)

    def stop(self) -> None:
        with self.lock:
            self.running = False
        if self.daemon:
            self.daemon.shutdown()

    def _reset_election_deadline(self) -> None:
        self.election_deadline = time.time() + random.uniform(*self.election_timeout_range)

    def _ticker_loop(self) -> None:
        while self.running:
            time.sleep(0.1)
            self._tick()

    def _tick(self) -> None:
        with self.lock:
            state = self.state
            deadline = self.election_deadline
        
        now = time.time()
        if state == "Lider":
            self._leader_tick(now)
        elif now >= deadline:
            self._start_election()

    def _leader_tick(self, now: float) -> None:
        if now - self.last_heartbeat_sent >= self.heartbeat_interval:
            self._send_heartbeats()
        
        if not self.ns_registered and self._register_as_leader():
            self.ns_registered = True
            self._log(f"Sucesso: Lider registrado no Name Server como '{LEADER_NS_NAME}'")

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
        try:
            with Pyro5.api.locate_ns(host=NAMESERVER_HOST, port=NAMESERVER_PORT) as ns:
                existing_uri = ns.lookup(LEADER_NS_NAME)
                if existing_uri and existing_uri != self.uri:
                    try:
                        with Pyro5.api.Proxy(existing_uri) as proxy:
                            proxy._pyroTimeout = 1.0
                            proxy.get_status()
                        self._reset_election_deadline()
                        return
                    except Exception:
                        pass
        except Exception:
            pass

        self._log(f"timeout de heartbeat atingido! Iniciando eleicao no termo {self.current_term + 1}")
        with self.lock:
            self.state = "Candidato"
            self.current_term += 1
            term_started = self.current_term
            self.voted_for = self.node_id
            self.leader_id = None
            self._reset_election_deadline()
            last_log_index, last_log_term = self._last_log_info()

        self._log(f"candidatou-se no termo {term_started}")

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
        votes_list: List[Optional[bool]] = [True]
        alive_list = [True]
        threads = []

        def _ask_vote(p_id, p_uri):
            try:
                self._log(f"PEDIU VOTO no termo {term}", peer_id=p_id)
                with Pyro5.api.Proxy(p_uri) as proxy:
                    resp = proxy.requestVote(term, self.node_id, last_idx, last_term)
                alive_list.append(True)
                if resp and isinstance(resp, dict):
                    if resp.get("term", 0) > term:
                        self._become_follower(resp["term"], None)
                        votes_list.append(None)
                    elif resp.get("voteGranted"):
                        votes_list.append(True)
            except Exception as exc:
                if self.peer_alive.get(p_id, True):
                    self._log(f"falha ao solicitar voto: {exc}", peer_id=p_id)
                    self.peer_alive[p_id] = False

        for p_id, p_uri in self.peers.items():
            t = threading.Thread(target=_ask_vote, args=(p_id, p_uri))
            t.start()
            threads.append(t)

        for t in threads:
            t.join(timeout=2.0)

        if None in votes_list:
            return -1, len(alive_list)
        return len(votes_list), len(alive_list)

    def _become_leader(self) -> None:
        self.state = "Lider"
        self.leader_id = self.node_id
        self.last_heartbeat_sent = 0.0
        self.next_index = {p_id: len(self.log) + 1 for p_id in self.peers}
        
        if self._register_as_leader():
            self.ns_registered = True
            self._log(f"eleito LIDER no termo {self.current_term} (registrado no Name Server como '{LEADER_NS_NAME}')")
        else:
            self.ns_registered = False
            self._log(f"eleito LIDER no termo {self.current_term}, mas falhou ao registrar no Name Server (tentando novamente)")

    def _become_follower(self, new_term: int, leader_id: Optional[int]) -> None:
        if self.state == "Lider" and self.current_term < new_term:
            self._log(f"detectou termo maior ({new_term}), deixando de ser lider")
        self.state = "Seguidor"
        self.ns_registered = False
        self.current_term = max(self.current_term, new_term)
        self.voted_for = None
        self.leader_id = leader_id
        self._reset_election_deadline()

    def _register_as_leader(self) -> bool:
        try:
            with Pyro5.api.locate_ns(host=NAMESERVER_HOST, port=NAMESERVER_PORT) as ns:
                ns.register(LEADER_NS_NAME, self.uri, safe=False)
                return True
        except Exception:
            return False

    def _send_heartbeats(self) -> None:
        with self.lock:
            if self.state != "Lider":
                return
            term = self.current_term
            leader_commit = self.commit_index
            self.last_heartbeat_sent = time.time()

        for peer_id, peer_uri in self.peers.items():
            with self.lock:
                next_idx = self.next_index.get(peer_id, 1)
                prev_idx = next_idx - 1
                prev_term = self.log[prev_idx - 1]["term"] if prev_idx > 0 else 0
                entries = self.log[next_idx - 1:]

            threading.Thread(
                target=self.sendEntry,
                args=(peer_id, peer_uri, term, entries, prev_idx, prev_term, leader_commit),
                daemon=True
            ).start()

    def sendEntry(self, peer_id: int, peer_uri: str, term: int, entries: List[Dict], prev_idx: int, prev_term: int, commit_idx: int) -> bool:  # type: ignore
        is_alive_before = self.peer_alive.get(peer_id, True)
        try:
            if is_alive_before:
                self._log_replication(peer_id, entries, commit_idx)

            with Pyro5.api.Proxy(peer_uri) as proxy:
                proxy._pyroTimeout = 2.0
                call = proxy.appendEntries(term, self.node_id, prev_idx, prev_term, entries, commit_idx)
            
            return self._handle_replication_response(peer_id, term, entries, commit_idx, call, is_alive_before)
        except Exception as exc:
            if is_alive_before:
                self._log(f"replicacao falhou: {exc}", peer_id=peer_id)
                self.peer_alive[peer_id] = False
        return False

    def _log_replication(self, peer_id: int, entries: List[Dict], commit_idx: int) -> None:
        for entry in entries:
            self._log(f"appendEntries index={entry['index']} command={entry['command']}", peer_id=peer_id)
        
        last_logged = self.last_commit_log_sent.get(peer_id, 0)
        if commit_idx > last_logged:
            for idx in range(last_logged + 1, commit_idx + 1):
                self._log(f"commit index={idx}", peer_id=peer_id)
            self.last_commit_log_sent[peer_id] = commit_idx

    def _handle_replication_response(self, peer_id: int, term: int, entries: List[Dict], commit_idx: int, call: Any, is_alive_before: bool) -> bool:
        if not call or not isinstance(call, dict):
            return False
        
        if call.get("term", 0) > term:
            self._become_follower(call["term"], None)
            return False
        
        self.peer_alive[peer_id] = True
        if call.get("success"):
            if not is_alive_before:
                self._log_replication(peer_id, entries, commit_idx)
            if entries:
                with self.lock:
                    self.next_index[peer_id] = entries[-1]["index"] + 1
            return True
        
        with self.lock:
            hint_idx = call.get("last_log_index", 0)
            self.next_index[peer_id] = max(1, hint_idx + 1)
        return False

    def notify(self, leader_id: Optional[int] = None) -> None:
        with self.lock:
            while self.last_applied < self.commit_index:
                entry = self.log[self.last_applied]
                self.last_applied += 1
                self._log(f"notify (COMMITTED) index={entry['index']} command={entry['command']}", peer_id=leader_id)

    def _replicate_entry(self, entry: Dict) -> bool:
        with self.lock:
            term = self.current_term
            leader_commit = self.commit_index
            prev_idx = entry["index"] - 1
            prev_term = self.log[prev_idx - 1]["term"] if prev_idx > 0 else 0

        alive_nodes = 1
        for p_id in self.peers:
            if self.peer_alive.get(p_id, True):
                alive_nodes += 1
        
        majority = (alive_nodes // 2) + 1
        
        results = []
        threads = []
        
        def _thread_task(p_id, p_uri):
            success = self.sendEntry(p_id, p_uri, term, [entry], prev_idx, prev_term, leader_commit)
            if success:
                results.append(True)

        for p_id, p_uri in self.peers.items():
            t = threading.Thread(target=_thread_task, args=(p_id, p_uri))
            t.start()
            threads.append(t)
            
        for t in threads:
            t.join(timeout=2.0)

        acks = len(results) + 1
        success = acks >= majority
        
        if not success:
            self._log(f"falha ao replicar index={entry['index']} (acks={acks}, maioria={majority})")
        return success

    @Pyro5.api.expose
    @Pyro5.api.oneway
    def commit(self, term: int, leader_id: int, commit_index: int) -> None:
        with self.lock:
            if term < self.current_term:
                return
            self._become_follower(term, leader_id)
            if commit_index > self.commit_index:
                self.commit_index = min(commit_index, len(self.log))
                self.notify(leader_id=leader_id)

    def _broadcast_commit(self, commit_index: int) -> None:
        with self.lock:
            term = self.current_term
        for peer_id, peer_uri in self.peers.items():
            if not self.peer_alive.get(peer_id, True):
                continue
            try:
                last_logged = self.last_commit_log_sent.get(peer_id, 0)
                if commit_index > last_logged:
                    for idx in range(last_logged + 1, commit_index + 1):
                        self._log(f"commit index={idx}", peer_id=peer_id)
                    self.last_commit_log_sent[peer_id] = commit_index
                
                with Pyro5.api.Proxy(peer_uri) as proxy:
                    proxy.commit(term, self.node_id, commit_index)
            except Exception as exc:
                self._log(f"falha ao enviar commit: {exc}", peer_id=peer_id)

    @Pyro5.api.expose
    def requestVote(self, term: int, candidate_id: int, last_log_index: int, last_log_term: int) -> Dict:  # type: ignore
        with self.lock:
            if term < self.current_term:
                return {"term": self.current_term, "voteGranted": False}

            if term > self.current_term:
                self._become_follower(term, None)

            can_vote = self.voted_for is None or self.voted_for == candidate_id
            up_to_date = self._is_candidate_log_up_to_date(last_log_index, last_log_term)

            if can_vote and up_to_date:
                self.voted_for = candidate_id
                self._reset_election_deadline()
                self._log(f"VOTOU em node{candidate_id} no termo {self.current_term}")
                return {"term": self.current_term, "voteGranted": True}

            self._log(f"RECUSOU voto para node{candidate_id}: {'ja votou' if not can_vote else 'log desatualizado'}")
            return {"term": self.current_term, "voteGranted": False}

    @Pyro5.api.expose
    def appendEntries(  # type: ignore
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

            if term > self.current_term or self.state != "Seguidor":
                self._become_follower(term, leader_id)
            else:
                self.leader_id = leader_id
                self._reset_election_deadline()

            if not self._check_prev_log(prev_log_index, prev_log_term):
                return {"term": self.current_term, "success": False, "last_log_index": len(self.log)}

            self._sync_log(entries)

            last_idx = len(self.log)
            if entries:
                self._log(f"OK index={last_idx}", peer_id=leader_id)

            if leader_commit > self.commit_index:
                new_commit = min(leader_commit, len(self.log))
                if new_commit > self.commit_index:
                    self.commit_index = new_commit
                    self.notify(leader_id=leader_id)
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
            self._log(f"<- client: command={entry['command']}")

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
            self.notify()

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
