import argparse

from server import config
from server.server import serve


def main():
    parser = argparse.ArgumentParser(description="Executa um no Raft (gRPC).")
    parser.add_argument("--id", type=int, required=True, help="ID do no (1-4).")
    args = parser.parse_args()
    if args.id not in config.NODE_IDS:
        raise ValueError("ID invalido. Use 1-4.")
    serve(args.id)


if __name__ == "__main__":
    main()
