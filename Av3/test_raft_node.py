import sys
import types
import unittest


def _install_pyro_stub() -> None:
    if "Pyro5" in sys.modules:
        return

    pyro_module = types.ModuleType("Pyro5")
    api_module = types.ModuleType("Pyro5.api")
    errors_module = types.ModuleType("Pyro5.errors")

    def expose(obj):
        return obj

    def behavior(**_kwargs):
        def decorator(obj):
            return obj

        return decorator

    class DummyDaemon:
        def __init__(self, *args, **kwargs):
            pass

        def register(self, *args, **kwargs):
            return None

        def requestLoop(self, *args, **kwargs):
            return None

        def shutdown(self):
            return None

    class DummyProxy:
        def __init__(self, *_args, **_kwargs):
            raise RuntimeError("Proxy nao disponivel no teste unitario")

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    class DummyNs:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def register(self, *_args, **_kwargs):
            return None

        def lookup(self, *_args, **_kwargs):
            return "PYRO:stub@localhost:5001"

    api_module.expose = expose
    api_module.behavior = behavior
    api_module.Daemon = DummyDaemon
    api_module.Proxy = DummyProxy
    api_module.locate_ns = lambda **_kwargs: DummyNs()

    pyro_module.api = api_module
    pyro_module.errors = errors_module

    sys.modules["Pyro5"] = pyro_module
    sys.modules["Pyro5.api"] = api_module
    sys.modules["Pyro5.errors"] = errors_module


_install_pyro_stub()

from raft_node import RaftNode


class RaftNodeTests(unittest.TestCase):
    def test_follower_vote_when_candidate_log_is_up_to_date(self):
        node = RaftNode(1)
        response = node.request_vote(term=1, candidate_id=2, last_log_index=0, last_log_term=0)
        self.assertTrue(response["vote_granted"])
        self.assertEqual(node.voted_for, 2)
        self.assertEqual(node.current_term, 1)

    def test_append_entries_persists_log_fields(self):
        node = RaftNode(2)
        node.current_term = 1
        response = node.append_entries(
            term=1,
            leader_id=1,
            prev_log_index=0,
            prev_log_term=0,
            entries=[{"term": 1, "index": 1, "command": "SET x 10"}],
            leader_commit=0,
        )

        self.assertTrue(response["success"])
        self.assertEqual(len(node.log), 1)
        self.assertEqual(node.log[0]["term"], 1)
        self.assertEqual(node.log[0]["index"], 1)
        self.assertEqual(node.log[0]["command"], "SET x 10")

    def test_client_command_redirects_when_not_leader(self):
        node = RaftNode(3)
        node.state = "Follower"
        response = node.client_command("SET y 20")
        self.assertFalse(response["success"])
        self.assertEqual(response["reason"], "not_leader")


if __name__ == "__main__":
    unittest.main()

