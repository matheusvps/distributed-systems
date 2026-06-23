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
