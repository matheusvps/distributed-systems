from server.persistence import PersistentState, save_state, load_state
import json

def test_load_missing_returns_defaults(tmp_path):
    state = load_state(str(tmp_path / "node9.json"))
    assert state.current_term == 0
    assert state.voted_for is None
    assert state.commit_index == 0
    assert state.log == []

def test_save_then_load_roundtrip(tmp_path):
    path = str(tmp_path / "node1.json")
    original = PersistentState(
        current_term=5,
        voted_for=3,
        commit_index=2,
        log=[
            {"term": 1, "index": 1, "key": "a", "value": "1"},
            {"term": 4, "index": 2, "key": "b", "value": "2"},
        ],
    )
    save_state(path, original)
    loaded = load_state(path)
    assert loaded.current_term == 5
    assert loaded.voted_for == 3
    assert loaded.commit_index == 2
    assert loaded.log == original.log

def test_save_is_atomic_no_temp_left(tmp_path):
    path = str(tmp_path / "node1.json")
    save_state(path, PersistentState(current_term=1))
    leftovers = [p.name for p in tmp_path.iterdir() if p.name != "node1.json"]
    assert leftovers == []

def test_save_creates_parent_dir(tmp_path):
    path = str(tmp_path / "data" / "node2.json")
    save_state(path, PersistentState(current_term=2))
    assert load_state(path).current_term == 2

def test_load_invalid_json_returns_defaults_and_backups(tmp_path, capsys):
    path = tmp_path / "node1.json"
    path.write_text("{ not valid json", encoding="utf-8")
    state = load_state(str(path))
    assert state == PersistentState()
    assert not path.exists()
    assert (tmp_path / "node1.json.corrupt.bak").exists()
    assert "AVISO" in capsys.readouterr().out

def test_load_invalid_top_level_returns_defaults(tmp_path, capsys):
    path = tmp_path / "node1.json"
    path.write_text('"just a string"', encoding="utf-8")
    state = load_state(str(path))
    assert state == PersistentState()
    assert (tmp_path / "node1.json.corrupt.bak").exists()

def test_load_sanitizes_bad_log_entries(tmp_path):
    path = tmp_path / "node1.json"
    path.write_text(json.dumps({
        "current_term": 3,
        "voted_for": 2,
        "commit_index": 99,
        "log": [
            {"term": 1, "index": 1, "key": "a", "value": "1"},
            {"term": "x", "index": 2, "key": "b", "value": "2"},
            {"term": 1, "index": 3, "key": "c", "value": "3"},
        ],
    }), encoding="utf-8")
    state = load_state(str(path))
    assert state.current_term == 3
    assert state.voted_for == 2
    assert state.log == [{"term": 1, "index": 1, "key": "a", "value": "1"}]
    assert state.commit_index == 1
