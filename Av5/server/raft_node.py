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
