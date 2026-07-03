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
    deadline = time.time() + 2
    while time.time() < deadline and n.state != "Lider":
        time.sleep(0.05)
    assert n.state == "Lider"

def test_leader_tick_replicates_on_heartbeat_interval(tmp_path):
    n = node(tmp_path, VoteTransport(granted_from={2, 3}))
    n.start_election()                 # becomes leader
    n.last_heartbeat_sent = 0.0        # force heartbeat due
    n.log = [{"term": 1, "index": 1, "key": "a", "value": "1"}]
    n.next_index = {pid: 1 for pid in config.peer_ids(1)}
    n.match_index = {pid: 0 for pid in config.peer_ids(1)}
    n.tick()
    deadline = time.time() + 2
    while time.time() < deadline and n.match_index.get(2, 0) != 1:
        time.sleep(0.05)
    assert n.match_index[2] == 1       # replicated via heartbeat

class SlowTransport:
    def send_request_vote(self, peer_id, args):
        time.sleep(0.5)
        return {"term": args["term"], "vote_granted": False}
    def send_append_entries(self, peer_id, args):
        time.sleep(0.5)
        return {"term": args["term"], "success": True, "conflict_index": 0}

def test_tick_returns_without_waiting_on_slow_replication(tmp_path):
    n = node(tmp_path, SlowTransport())
    n.state = "Lider"
    n.leader_id = 1
    n.current_term = 1
    n.last_heartbeat_sent = 0.0
    n.next_index = {pid: 1 for pid in config.peer_ids(1)}
    n.match_index = {pid: 0 for pid in config.peer_ids(1)}
    t0 = time.time()
    n.tick()
    assert time.time() - t0 < 0.2
