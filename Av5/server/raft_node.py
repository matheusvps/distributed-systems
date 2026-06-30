import concurrent.futures
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
        self.publish_commit_timeout = 3.0  # max seconds to wait for commit in handle_publish
        self._reset_election_deadline()

    def log_event(self, msg, peer_id=None):
        prefix = f"node{self.node_id} [{self.state}] (term={self.current_term})"
        if peer_id is not None:
            print(f"{prefix} -> node{peer_id}: {msg}", flush=True)
        else:
            print(f"{prefix}: {msg}", flush=True)

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

    def _reset_election_deadline(self):
        self.election_deadline = time.time() + random.uniform(*config.ELECTION_TIMEOUT_RANGE)

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

    def handle_append_entries(self, term, leader_id, prev_log_index,
                              prev_log_term, entries, leader_commit):
        with self.lock:
            if term < self.current_term:
                return {"term": self.current_term, "success": False, "conflict_index": 0}

            self._become_follower(max(term, self.current_term), leader_id)

            if prev_log_index > len(self.log):
                return {"term": self.current_term, "success": False,
                        "conflict_index": len(self.log) + 1}
            if prev_log_index > 0 and self._term_of(prev_log_index) != prev_log_term:
                self.log = self.log[: prev_log_index - 1]
                self._persist()
                return {"term": self.current_term, "success": False,
                        "conflict_index": prev_log_index}

            prev_log_len = len(self.log)
            self._merge_entries(entries)
            entries_mutated = len(self.log) != prev_log_len

            commit_advanced = False
            if leader_commit > self.commit_index:
                self.commit_index = min(leader_commit, len(self.log))
                self._apply_committed()
                commit_advanced = True

            if entries_mutated or commit_advanced:
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
            return
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
        peers = config.peer_ids(self.node_id)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(peers)) as ex:
            futures = [ex.submit(self._replicate_to_peer, pid) for pid in peers]
            concurrent.futures.wait(futures)
        self._advance_commit_index()

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

        deadline = time.time() + self.publish_commit_timeout
        poll_interval = 0.1
        while True:
            with self.lock:
                committed = self.commit_index >= index
            if committed:
                return {"success": True, "leader_hint": "",
                        "index": index, "message": "ok"}
            if time.time() >= deadline:
                break
            time.sleep(poll_interval)

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

        peers = config.peer_ids(self.node_id)

        def _request_vote(pid):
            return pid, self.transport.send_request_vote(pid, args)

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(peers)) as ex:
            results = list(ex.map(_request_vote, peers))

        votes = 1
        with self.lock:
            for pid, reply in results:
                if reply is None:
                    continue
                if reply["term"] > self.current_term:
                    self.current_term = reply["term"]
                    self.voted_for = None
                    self._become_follower(reply["term"], None)
                    return
                if self.state != "Candidato" or self.current_term != term:
                    return
                if reply["vote_granted"]:
                    votes += 1

            if self.state == "Candidato" and self.current_term == term and votes >= config.QUORUM:
                self._become_leader()
            elif self.state == "Candidato":
                self.state = "Seguidor"
                self._reset_election_deadline()

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
