import random
import threading
import time
from typing import Dict, List, Optional, Tuple

import Pyro5.api
import Pyro5.errors


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


@Pyro5.api.expose
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
            f"[Node {self.node_id}] iniciado em {self.uri} | estado inicial: {self.state}",
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

            if state == "Leader":
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
            self.state = "Candidate"
            self.current_term += 1
            term_started = self.current_term
            self.voted_for = self.node_id
            self.leader_id = None
            self._reset_election_deadline()
            last_log_index, last_log_term = self._last_log_info()

        print(
            f"[Node {self.node_id}] iniciando eleicao no termo {term_started}",
            flush=True,
        )

        votes = 1
        for peer_id, peer_uri in self.peers.items():
            try:
                with Pyro5.api.Proxy(peer_uri) as proxy:
                    response = proxy.request_vote(
                        term_started, self.node_id, last_log_index, last_log_term
                    )
                if response.get("term", 0) > term_started:
                    with self.lock:
                        self._become_follower(response["term"], None)
                    return
                if response.get("vote_granted"):
                    votes += 1
                    print(
                        f"[Node {self.node_id}] voto recebido de {peer_id} (total={votes})",
                        flush=True,
                    )
            except Exception as exc:
                print(
                    f"[Node {self.node_id}] falha ao solicitar voto de {peer_id}: {exc}",
                    flush=True,
                )

        with self.lock:
            if self.state != "Candidate" or self.current_term != term_started:
                return
            if votes >= 3:
                self.state = "Leader"
                self.leader_id = self.node_id
                self.last_heartbeat_sent = 0.0
                print(
                    f"[Node {self.node_id}] eleito LIDER no termo {self.current_term}",
                    flush=True,
                )
                self._register_as_leader()
            else:
                self._become_follower(self.current_term, None)

    def _become_follower(self, new_term: int, leader_id: Optional[int]) -> None:
        self.state = "Follower"
        self.current_term = max(self.current_term, new_term)
        self.voted_for = None
        self.leader_id = leader_id
        self._reset_election_deadline()

    def _register_as_leader(self) -> None:
        try:
            with Pyro5.api.locate_ns(host=NAMESERVER_HOST, port=NAMESERVER_PORT) as ns:
                ns.register(LEADER_NS_NAME, self.uri, safe=False)
                print(
                    f"[Node {self.node_id}] registrado no Name Server como '{LEADER_NS_NAME}'",
                    flush=True,
                )
        except Exception as exc:
            print(
                f"[Node {self.node_id}] erro ao registrar lider no Name Server: {exc}",
                flush=True,
            )

    def _send_heartbeats(self) -> None:
        with self.lock:
            if self.state != "Leader":
                return
            term = self.current_term
            leader_commit = self.commit_index
            prev_log_index, prev_log_term = self._last_log_info()
            self.last_heartbeat_sent = time.time()

        for peer_id, peer_uri in self.peers.items():
            try:
                with Pyro5.api.Proxy(peer_uri) as proxy:
                    response = proxy.append_entries(
                        term,
                        self.node_id,
                        prev_log_index,
                        prev_log_term,
                        [],
                        leader_commit,
                    )
                if response.get("term", 0) > term:
                    with self.lock:
                        self._become_follower(response["term"], None)
                    return
            except Exception as exc:
                print(
                    f"[Node {self.node_id}] heartbeat para {peer_id} falhou: {exc}",
                    flush=True,
                )

    def _apply_entries(self) -> None:
        while self.last_applied < self.commit_index:
            entry = self.log[self.last_applied]
            self.last_applied += 1
            print(
                f"[Node {self.node_id}] APPLY term={entry['term']} index={entry['index']} command={entry['command']}",
                flush=True,
            )

    def _replicate_entry(self, entry: Dict) -> bool:
        with self.lock:
            term = self.current_term
            leader_commit = self.commit_index
            prev_log_index = entry["index"] - 1
            prev_log_term = self.log[prev_log_index - 1]["term"] if prev_log_index > 0 else 0

        acks = 1
        for peer_id, peer_uri in self.peers.items():
            try:
                with Pyro5.api.Proxy(peer_uri) as proxy:
                    response = proxy.append_entries(
                        term,
                        self.node_id,
                        prev_log_index,
                        prev_log_term,
                        [entry],
                        leader_commit,
                    )
                if response.get("term", 0) > term:
                    with self.lock:
                        self._become_follower(response["term"], None)
                    return False
                if response.get("success"):
                    acks += 1
            except Exception as exc:
                print(
                    f"[Node {self.node_id}] replicacao para {peer_id} falhou: {exc}",
                    flush=True,
                )
        return acks >= 3

    def _broadcast_commit(self, commit_index: int) -> None:
        with self.lock:
            term = self.current_term
        for peer_id, peer_uri in self.peers.items():
            try:
                with Pyro5.api.Proxy(peer_uri) as proxy:
                    proxy.commit_up_to(term, self.node_id, commit_index)
            except Exception as exc:
                print(
                    f"[Node {self.node_id}] confirmacao de commit para {peer_id} falhou: {exc}",
                    flush=True,
                )

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
                    f"[Node {self.node_id}] votou em {candidate_id} no termo {self.current_term}",
                    flush=True,
                )
                return {"term": self.current_term, "vote_granted": True}

            return {"term": self.current_term, "vote_granted": False}

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

            if prev_log_index > len(self.log):
                return {"term": self.current_term, "success": False}

            if prev_log_index > 0:
                local_prev_term = self.log[prev_log_index - 1]["term"]
                if local_prev_term != prev_log_term:
                    self.log = self.log[: prev_log_index - 1]
                    return {"term": self.current_term, "success": False}

            for entry in entries:
                idx = entry["index"]
                if idx <= len(self.log):
                    if self.log[idx - 1]["term"] != entry["term"]:
                        self.log = self.log[: idx - 1]
                        self.log.append(entry)
                else:
                    self.log.append(entry)
                print(
                    f"[Node {self.node_id}] RECV term={entry['term']} index={entry['index']} command={entry['command']}",
                    flush=True,
                )

            if leader_commit > self.commit_index:
                self.commit_index = min(leader_commit, len(self.log))
                self._apply_entries()

            return {"term": self.current_term, "success": True}

    def commit_up_to(self, term: int, leader_id: int, commit_index: int) -> Dict:
        with self.lock:
            if term < self.current_term:
                return {"term": self.current_term, "success": False}
            self._become_follower(term, leader_id)
            self.commit_index = min(commit_index, len(self.log))
            self._apply_entries()
            return {"term": self.current_term, "success": True}

    def client_command(self, command: str) -> Dict:
        with self.lock:
            if self.state != "Leader":
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
                f"[Node {self.node_id}] CLIENT term={entry['term']} index={entry['index']} command={entry['command']}",
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

