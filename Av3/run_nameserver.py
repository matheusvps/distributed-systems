import os
import subprocess

def kill_previous_process(pattern: str) -> None:
    current_pid = os.getpid()
    try:
        output = subprocess.check_output(["pgrep", "-f", pattern]).decode().strip()
        if output:
            pids = [int(p) for p in output.split()]
            for pid in pids:
                if pid != current_pid:
                    print(f"Encerrando processo anterior ({pattern}) com PID {pid}...", flush=True)
                    os.system(f"kill -9 {pid}")
    except subprocess.CalledProcessError:
        pass

def main() -> None:
    # kill_previous_process("Pyro5.nameserver")
    print("Iniciando novo Name Server...", flush=True)
    subprocess.run(["python3", "-m", "Pyro5.nameserver", "-n", "localhost", "-p", "9090"])

if __name__ == "__main__":
    main()
