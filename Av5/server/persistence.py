import json
import os
from dataclasses import dataclass, field, asdict


@dataclass
class PersistentState:
    current_term: int = 0
    voted_for: "int | None" = None
    commit_index: int = 0
    log: list = field(default_factory=list)


def _backup_corrupt(path):
    bak = f"{path}.corrupt.bak"
    try:
        os.replace(path, bak)
    except OSError:
        pass


def _warn_corrupt(path, reason):
    print(f"AVISO: estado corrompido em {path}: {reason}; "
          f"backup em {path}.corrupt.bak e reinício com estado vazio",
          flush=True)


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_state(data):
    if not isinstance(data, dict):
        return None

    log_in = data.get("log", [])
    if not isinstance(log_in, list):
        log_in = []

    log = []
    for entry in log_in:
        if not isinstance(entry, dict):
            continue
        try:
            term = _as_int(entry.get("term"), -1)
            index = _as_int(entry.get("index"), -1)
            key = entry.get("key")
            value = entry.get("value")
        except (TypeError, ValueError):
            continue
        if term < 0 or index <= 0 or not isinstance(key, str) or not isinstance(value, str):
            continue
        log.append({"term": term, "index": index, "key": key, "value": value})

    log.sort(key=lambda e: e["index"])
    # keep only a contiguous prefix starting at index 1
    clean_log = []
    expected = 1
    for entry in log:
        if entry["index"] != expected:
            break
        clean_log.append(entry)
        expected += 1

    commit_index = max(0, _as_int(data.get("commit_index", 0)))
    commit_index = min(commit_index, len(clean_log))

    voted_for = data.get("voted_for")
    if voted_for is not None:
        voted_for = _as_int(voted_for, -1)
        if voted_for < 0:
            voted_for = None

    return PersistentState(
        current_term=max(0, _as_int(data.get("current_term", 0))),
        voted_for=voted_for,
        commit_index=commit_index,
        log=clean_log,
    )


def save_state(path, state):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(asdict(state), fh, ensure_ascii=False, indent=2)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)  # atomic on POSIX


def load_state(path):
    if not os.path.exists(path):
        return PersistentState()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        _warn_corrupt(path, exc)
        _backup_corrupt(path)
        return PersistentState()

    state = _parse_state(data)
    if state is None:
        _warn_corrupt(path, "formato JSON inválido")
        _backup_corrupt(path)
        return PersistentState()
    return state
