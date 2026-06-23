import grpc

from server import config
from server.gen import raft_pb2, raft_pb2_grpc


def _entries_to_pb(entries):
    return [raft_pb2.LogEntry(term=e["term"], index=e["index"],
                              key=e["key"], value=e["value"]) for e in entries]


def _entries_from_pb(pb_entries):
    return [{"term": e.term, "index": e.index, "key": e.key, "value": e.value}
            for e in pb_entries]


class GrpcPeers:
    def __init__(self, node_id):
        self.node_id = node_id
        self._channels = {}
        for pid in config.peer_ids(node_id):
            self._channels[pid] = grpc.insecure_channel(config.NODE_ADDRESSES[pid])

    def _stub(self, peer_id):
        return raft_pb2_grpc.RaftServiceStub(self._channels[peer_id])

    def send_request_vote(self, peer_id, args):
        try:
            reply = self._stub(peer_id).RequestVote(
                raft_pb2.RequestVoteArgs(
                    term=args["term"], candidate_id=args["candidate_id"],
                    last_log_index=args["last_log_index"],
                    last_log_term=args["last_log_term"]),
                timeout=config.RPC_TIMEOUT)
            return {"term": reply.term, "vote_granted": reply.vote_granted}
        except grpc.RpcError:
            return None

    def send_append_entries(self, peer_id, args):
        try:
            reply = self._stub(peer_id).AppendEntries(
                raft_pb2.AppendEntriesArgs(
                    term=args["term"], leader_id=args["leader_id"],
                    prev_log_index=args["prev_log_index"],
                    prev_log_term=args["prev_log_term"],
                    entries=_entries_to_pb(args["entries"]),
                    leader_commit=args["leader_commit"]),
                timeout=config.RPC_TIMEOUT)
            return {"term": reply.term, "success": reply.success,
                    "conflict_index": reply.conflict_index}
        except grpc.RpcError:
            return None
