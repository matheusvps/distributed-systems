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
