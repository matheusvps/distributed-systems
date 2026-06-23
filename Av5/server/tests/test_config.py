from server import config

def test_quorum_is_fixed_three():
    assert config.QUORUM == 3

def test_four_nodes_with_addresses():
    assert config.NODE_IDS == [1, 2, 3, 4]
    assert config.NODE_ADDRESSES[1] == "node1:6001"
    assert config.NODE_ADDRESSES[4] == "node4:6004"

def test_peer_ids_excludes_self():
    assert config.peer_ids(2) == [1, 3, 4]

def test_data_path_uses_node_id():
    assert config.data_path(3).endswith("node3.json")
