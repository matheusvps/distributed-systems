import argparse
import os
import subprocess

from raft_node import NODE_IDS, RaftNode


def kill_previous_process(pattern: str) -> None:
    current_pid = os.getpid()
    try:
        output = subprocess.check_output(["pgrep", "-f", pattern]).decode().strip()
        if output:
            pids = [int(p) for p in output.split()]
            for pid in pids:
                if pid != current_pid:
                    print(
                        f"Encerrando processo anterior ({pattern}) com PID {pid}...",
                        flush=True,
                    )
                    os.system(f"kill -9 {pid}")
    except subprocess.CalledProcessError:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa um nó Raft com PyRO5.")
    parser.add_argument("--id", type=int, required=True, help="ID do nó (1-4).")
    args = parser.parse_args()

    kill_previous_process(f"run_node.py.*--id[ =]{args.id}")

    if args.id not in NODE_IDS:
        raise ValueError("ID de nó inválido. Use valores entre 1 e 4.")

    node = RaftNode(args.id)
    node.start()


if __name__ == "__main__":
    main()

