import threading
from concurrent import futures

import grpc

from server import config
from server.gen import raft_pb2, raft_pb2_grpc
from server.raft_node import RaftNode
from server.transport import GrpcPeers, _entries_from_pb


class RaftServicer(raft_pb2_grpc.RaftServiceServicer):
    def __init__(self, node):
        self.node = node

    def RequestVote(self, request, context):
        r = self.node.handle_request_vote(
            request.term, request.candidate_id,
            request.last_log_index, request.last_log_term)
        return raft_pb2.RequestVoteReply(term=r["term"], vote_granted=r["vote_granted"])

    def AppendEntries(self, request, context):
        r = self.node.handle_append_entries(
            request.term, request.leader_id,
            request.prev_log_index, request.prev_log_term,
            _entries_from_pb(request.entries), request.leader_commit)
        return raft_pb2.AppendEntriesReply(
            term=r["term"], success=r["success"], conflict_index=r["conflict_index"])


class ClientServicer(raft_pb2_grpc.ClientServiceServicer):
    def __init__(self, node):
        self.node = node

    def Publish(self, request, context):
        r = self.node.handle_publish(request.key, request.value)
        return raft_pb2.PublishReply(
            success=r["success"], leader_hint=r["leader_hint"],
            index=r["index"], message=r["message"])

    def Consume(self, request, context):
        r = self.node.handle_consume(request.key)
        return raft_pb2.ConsumeReply(
            success=r["success"],
            items=[raft_pb2.DataItem(key=i["key"], value=i["value"], index=i["index"])
                   for i in r["items"]],
            leader_hint=r["leader_hint"], is_leader=r["is_leader"],
            committed_index=r["committed_index"], pending_count=r["pending_count"],
            pending_replicated_count=r["pending_replicated_count"],
            pending_leader_only_count=r["pending_leader_only_count"])


def serve(node_id):
    transport = GrpcPeers(node_id)
    node = RaftNode(node_id, transport)

    ticker = threading.Thread(target=node.run_ticker, daemon=True)
    ticker.start()

    raft_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    raft_pb2_grpc.add_RaftServiceServicer_to_server(RaftServicer(node), raft_server)
    raft_port = config.RAFT_NODE_ADDRESSES[node_id].split(":")[1]
    raft_server.add_insecure_port(f"[::]:{raft_port}")
    raft_server.start()

    client_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    raft_pb2_grpc.add_ClientServiceServicer_to_server(ClientServicer(node), client_server)
    client_port = config.CLIENT_NODE_ADDRESSES[node_id].split(":")[1]
    client_server.add_insecure_port(f"[::]:{client_port}")
    client_server.start()

    node.log_event(f"RaftService interno em {config.RAFT_NODE_ADDRESSES[node_id]}")
    node.log_event(f"ClientService em {config.CLIENT_NODE_ADDRESSES[node_id]}")

    threading.Thread(target=raft_server.wait_for_termination, daemon=True).start()
    client_server.wait_for_termination()
