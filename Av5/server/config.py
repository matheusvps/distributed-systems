import os

NODE_IDS = [1, 2, 3, 4]
NODE_ADDRESSES = {
    1: "node1:6001",
    2: "node2:6002",
    3: "node3:6003",
    4: "node4:6004",
}
QUORUM = len(NODE_IDS) // 2 + 1  # always 3 for a 4-node cluster

ELECTION_TIMEOUT_RANGE = (3.0, 6.0)  # seconds
HEARTBEAT_INTERVAL = 1.0             # seconds
TICK_INTERVAL = 0.1                  # seconds
RPC_TIMEOUT = 2.0                    # seconds

DATA_DIR = os.environ.get("RAFT_DATA_DIR", "data")


def peer_ids(node_id):
    return [nid for nid in NODE_IDS if nid != node_id]


def data_path(node_id):
    return os.path.join(DATA_DIR, f"node{node_id}.json")
