import unittest
import threading
import time
from unittest.mock import patch, MagicMock
import raft_node
from raft_node import RaftNode, LEADER_NS_NAME, build_uri

class MockProxy:
    def __init__(self, uri, nodes_dict, fail_nodes=None):
        self.uri = uri
        self.nodes_dict = nodes_dict
        self.fail_nodes = fail_nodes or set()
        self._pyroTimeout = 0

    def __getattr__(self, name):
        target_node = None
        for node in self.nodes_dict.values():
            if node.uri == self.uri:
                target_node = node
                break
        
        if not target_node or target_node.node_id in self.fail_nodes:
            def failed_call(*args, **kwargs):
                raise RuntimeError(f"Node {target_node.node_id if target_node else 'unknown'} is down")
            return failed_call

        return getattr(target_node, name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class RaftAdvancedTests(unittest.TestCase):
    def setUp(self):
        self.node_ids = [1, 2, 3]
        self.nodes = {i: RaftNode(i) for i in self.node_ids}
        self.fail_nodes = set()

    def get_proxy_mock(self, uri):
        return MockProxy(uri, self.nodes, self.fail_nodes)

    @patch("Pyro5.api.Proxy")
    @patch("Pyro5.api.locate_ns")
    def test_ns_resilience_follower(self, mock_locate_ns, mock_proxy_class):
        mock_proxy_class.side_effect = self.get_proxy_mock
        mock_locate_ns.side_effect = RuntimeError("NS DOWN")
        
        follower = self.nodes[1]
        follower.leader_id = 2
        follower.leader_ns_valid = False
        
        follower.appendEntries(term=1, leader_id=2, prev_log_index=0, prev_log_term=0, entries=[], leader_commit=0)
        
        follower._validate_leader_in_ns(2)
        
        self.assertTrue(follower.leader_ns_valid)
        
    @patch("Pyro5.api.Proxy")
    @patch("Pyro5.api.locate_ns")
    def test_follower_catchup(self, mock_locate_ns, mock_proxy_class):
        mock_proxy_class.side_effect = self.get_proxy_mock
        mock_ns = MagicMock()
        mock_locate_ns.return_value.__enter__.return_value = mock_ns
        
        leader = self.nodes[1]
        leader._become_leader()
        
        self.fail_nodes.add(3)
        
        leader.client_command("CMD1")
        leader.client_command("CMD2")
        
        self.assertEqual(len(leader.log), 2)
        self.assertEqual(len(self.nodes[2].log), 2)
        self.assertEqual(len(self.nodes[3].log), 0)
        
        self.fail_nodes.remove(3)
        
        leader._send_heartbeats()
        
        time.sleep(0.5) 
        
        self.assertEqual(len(self.nodes[3].log), 2)
        self.assertEqual(self.nodes[3].log[1]["command"], "CMD2")

    @patch("Pyro5.api.Proxy")
    @patch("Pyro5.api.locate_ns")
    def test_leader_replacement_and_return(self, mock_locate_ns, mock_proxy_class):
        mock_proxy_class.side_effect = self.get_proxy_mock
        mock_ns = MagicMock()
        mock_locate_ns.return_value.__enter__.return_value = mock_ns
        
        leader1 = self.nodes[1]
        leader1._start_election()
        time.sleep(0.1)
        self.assertEqual(leader1.state, "Lider")
        self.assertEqual(leader1.current_term, 1)
        
        self.fail_nodes.add(1)
        
        node2 = self.nodes[2]
        node2._start_election()
        
        time.sleep(0.5)
        
        self.assertEqual(node2.state, "Lider")
        self.assertEqual(node2.current_term, 2)
        
        node2.client_command("NEW_LEADER_CMD")
        
        self.fail_nodes.remove(1)
        
        node2._send_heartbeats()
        time.sleep(0.2)
        
        self.assertEqual(leader1.state, "Seguidor")
        self.assertEqual(leader1.current_term, 2)
        self.assertEqual(leader1.leader_id, 2)
        self.assertEqual(len(leader1.log), 1)

    @patch("Pyro5.api.Proxy")
    @patch("Pyro5.api.locate_ns")
    def test_async_ns_registration(self, mock_locate_ns, mock_proxy_class):
        mock_proxy_class.side_effect = self.get_proxy_mock
        
        def slow_ns(*args, **kwargs):
            time.sleep(0.3)
            return MagicMock()
        mock_locate_ns.side_effect = slow_ns
        
        leader = self.nodes[1]
        start_time = time.time()
        
        leader._become_leader()
        
        duration = time.time() - start_time
        self.assertLess(duration, 0.1)
        self.assertEqual(leader.state, "Lider")
        
        time.sleep(0.5)

if __name__ == "__main__":
    unittest.main()
