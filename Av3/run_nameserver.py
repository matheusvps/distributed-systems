import os
import subprocess

def main() -> None:
    print("iniciando name server...", flush=True)
    subprocess.run(["python3", "-m", "Pyro5.nameserver", "-n", "localhost", "-p", "9090"])

if __name__ == "__main__":
    main()
