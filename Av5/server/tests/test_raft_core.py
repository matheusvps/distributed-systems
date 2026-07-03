from server.raft_node import RaftNode
from server.persistence import PersistentState, save_state


class FakeTransport:
    def send_request_vote(self, peer_id, args):
        return None
    def send_append_entries(self, peer_id, args):
        return None


def make_node(tmp_path, nid=1):
    return RaftNode(nid, FakeTransport(), data_path=str(tmp_path / f"node{nid}.json"))


def test_starts_as_follower_with_defaults(tmp_path):
    n = make_node(tmp_path)
    assert n.state == "Seguidor"
    assert n.current_term == 0
    assert n.voted_for is None
    assert n.log == []
    assert n.commit_index == 0

def test_loads_persisted_state(tmp_path):
    path = tmp_path / "node1.json"
    save_state(str(path), PersistentState(
        current_term=7, voted_for=2, commit_index=1,
        log=[{"term": 7, "index": 1, "key": "k", "value": "v"}],
    ))
    n = make_node(tmp_path)
    assert n.current_term == 7
    assert n.voted_for == 2
    assert n.commit_index == 1
    assert n.last_log_index() == 1
    assert n.last_log_term() == 7
    assert n.state == "Seguidor"  # always recovers as follower

def test_starts_with_corrupt_persisted_file(tmp_path, capsys):
    path = tmp_path / "node1.json"
    path.write_text("<<<corrupt>>>", encoding="utf-8")
    n = make_node(tmp_path)
    assert n.current_term == 0
    assert n.log == []
    assert n.state == "Seguidor"
    assert "AVISO" in capsys.readouterr().out

def test_last_log_info_empty(tmp_path):
    n = make_node(tmp_path)
    assert n.last_log_index() == 0
    assert n.last_log_term() == 0

def test_up_to_date_compares_term_then_index(tmp_path):
    n = make_node(tmp_path)
    n.log = [{"term": 2, "index": 1, "key": "a", "value": "1"},
             {"term": 2, "index": 2, "key": "b", "value": "2"}]
    # higher term wins even with shorter log
    assert n._is_up_to_date(last_log_index=1, last_log_term=3) is True
    # same term, candidate index >= ours -> ok
    assert n._is_up_to_date(last_log_index=2, last_log_term=2) is True
    # same term, candidate shorter -> not up to date
    assert n._is_up_to_date(last_log_index=1, last_log_term=2) is False
    # lower term -> not up to date
    assert n._is_up_to_date(last_log_index=9, last_log_term=1) is False

def test_persist_writes_file(tmp_path):
    n = make_node(tmp_path)
    n.current_term = 3
    n.voted_for = 1
    n._persist()
    from server.persistence import load_state
    reloaded = load_state(str(tmp_path / "node1.json"))
    assert reloaded.current_term == 3
    assert reloaded.voted_for == 1
