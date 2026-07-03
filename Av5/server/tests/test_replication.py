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

def test_empty_heartbeat_updates_match_index_when_follower_in_sync(tmp_path):
    t = ScriptedTransport({2: [], 3: [], 4: []})
    n = leader(tmp_path, t)
    n.current_term = 2
    n.log = [{"term": 2, "index": 1, "key": "a", "value": "1"}]
    n.next_index = {2: 2, 3: 2, 4: 2}
    n.match_index = {2: 0, 3: 0, 4: 0}
    n._replicate_to_peer(2)
    assert n.match_index[2] == 1
    assert n.next_index[2] == 2

def test_commit_after_empty_heartbeats_discover_quorum(tmp_path):
    t = ScriptedTransport({2: [], 3: [], 4: []})
    n = leader(tmp_path, t)
    n.current_term = 2
    n.log = [{"term": 2, "index": 1, "key": "a", "value": "1"}]
    n.next_index = {2: 2, 3: 2, 4: 2}
    n.match_index = {2: 0, 3: 0, 4: 0}
    for pid in config.peer_ids(1):
        n._replicate_to_peer(pid)
    n._advance_commit_index()
    assert n.commit_index == 1
