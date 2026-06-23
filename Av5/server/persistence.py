import json
import os
from dataclasses import dataclass, field, asdict


@dataclass
class PersistentState:
    current_term: int = 0
    voted_for: "int | None" = None
    commit_index: int = 0
    log: list = field(default_factory=list)


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
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return PersistentState(
        current_term=data.get("current_term", 0),
        voted_for=data.get("voted_for"),
        commit_index=data.get("commit_index", 0),
        log=data.get("log", []),
    )
