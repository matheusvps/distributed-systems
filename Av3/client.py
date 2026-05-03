import argparse
import sys
import time

import Pyro5.api

from raft_node import LEADER_NS_NAME, NAMESERVER_HOST, NAMESERVER_PORT


def find_leader_uri() -> str:
    with Pyro5.api.locate_ns(host=NAMESERVER_HOST, port=NAMESERVER_PORT) as ns:
        return ns.lookup(LEADER_NS_NAME)


def send_command(command: str):
    leader_uri = find_leader_uri()
    with Pyro5.api.Proxy(leader_uri) as leader:
        result = leader.client_command(command)
    return result


def interactive_mode() -> None:
    print("Cliente Raft iniciado. Digite comandos (ou 'sair').", flush=True)
    while True:
        try:
            command = input("> ").strip()
        except EOFError:
            print("Entrada encerrada (EOF). Finalizando cliente.", flush=True)
            break
        if not command:
            continue
        if command.lower() in {"sair", "exit", "quit"}:
            break

        try:
            result = send_command(command)
        except Exception as exc:
            print(f"Erro ao enviar comando: {exc}", flush=True)
            time.sleep(1)
            continue

        print(f"Resposta: {result}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Cliente para cluster Raft via PyRO5.")
    parser.add_argument(
        "--command",
        type=str,
        help="Comando unico para envio. Se omitido, inicia modo interativo.",
    )
    args = parser.parse_args()

    if args.command:
        print(send_command(args.command))
    else:
        if not sys.stdin.isatty():
            print(
                "Modo interativo requer terminal (TTY). Use --command para envio unico.",
                flush=True,
            )
            return
        interactive_mode()


if __name__ == "__main__":
    main()
