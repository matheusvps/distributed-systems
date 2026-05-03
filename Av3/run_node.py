import argparse
import os
import subprocess

from raft_node import NODE_IDS, RaftNode


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa um no Raft com PyRO5.")
    parser.add_argument("--id", type=int, required=True, help="ID do no (1-4).")
    args = parser.parse_args()

    if args.id not in NODE_IDS:
        raise ValueError("ID de no invalido. Use valores entre 1 e 4.")

    node = RaftNode(args.id)
    node.start()


if __name__ == "__main__":
    main()
