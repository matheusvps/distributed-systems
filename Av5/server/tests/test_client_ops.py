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
