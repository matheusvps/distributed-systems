from server.persistence import PersistentState, save_state, load_state

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
