import os

NODE_IDS = [1, 2, 3, 4]

# Client-facing API (Publish/Consume) — reachable by the Go client.
CLIENT_NODE_ADDRESSES = {
    1: "node1:6001",
    2: "node2:6002",
    3: "node3:6003",
    4: "node4:6004",
}

# Internal Raft RPCs (RequestVote/AppendEntries) — cluster network only.
RAFT_NODE_ADDRESSES = {
    1: "node1-raft:6101",
    2: "node2-raft:6102",
    3: "node3-raft:6103",
    4: "node4-raft:6104",
}
QUORUM = len(NODE_IDS) // 2 + 1 

ELECTION_TIMEOUT_RANGE = (3.0, 6.0)  # seconds
HEARTBEAT_INTERVAL = 1.0             # seconds
TICK_INTERVAL = 0.1                  # seconds
RPC_TIMEOUT = 2.0                    # seconds

DATA_DIR = os.environ.get("RAFT_DATA_DIR", "data")


def peer_ids(node_id):
    return [nid for nid in NODE_IDS if nid != node_id]


def data_path(node_id):
    return os.path.join(DATA_DIR, f"node{node_id}.json")
