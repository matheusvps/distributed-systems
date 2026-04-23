import argparse

from raft_node import NODE_IDS, RaftNode


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa um nó Raft com PyRO5.")
    parser.add_argument("--id", type=int, required=True, help="ID do nó (1-4).")
    args = parser.parse_args()

    if args.id not in NODE_IDS:
        raise ValueError("ID de nó inválido. Use valores entre 1 e 4.")

    node = RaftNode(args.id)
    node.start()


if __name__ == "__main__":
    main()

