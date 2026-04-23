"""Local JSONL logger for reddit-agent. One file per day per account."""
import json, os
from datetime import date


def log_dir(account_dir: str) -> str:
    d = os.path.join(account_dir, "logs")
    os.makedirs(d, exist_ok=True)
    return d


def log_comment(account_dir: str, entry: dict):
    path = os.path.join(log_dir(account_dir), f"{date.today()}.jsonl")
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def load_replied(account_dir: str) -> dict:
    path = os.path.join(log_dir(account_dir), "replied.json")
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def save_replied(account_dir: str, replied: dict):
    path = os.path.join(log_dir(account_dir), "replied.json")
    with open(path, "w") as f:
        json.dump(replied, f, indent=2)


def log_karma(account_dir: str, karma: dict):
    path = os.path.join(log_dir(account_dir), "karma.json")
    history = []
    if os.path.exists(path):
        with open(path) as f:
            history = json.load(f)
    today = str(date.today())
    history = [e for e in history if e.get("date") != today]
    history.append({"date": today, **karma})
    with open(path, "w") as f:
        json.dump(history, f, indent=2)


def today_stats(account_dir: str) -> dict:
    path = os.path.join(log_dir(account_dir), f"{date.today()}.jsonl")
    if not os.path.exists(path):
        return {"comments": 0, "ok": 0, "errors": 0}
    entries = [json.loads(l) for l in open(path)]
    return {
        "comments": len(entries),
        "ok": sum(1 for e in entries if e.get("ok")),
        "errors": sum(1 for e in entries if not e.get("ok")),
    }


def load_liked(account_dir: str) -> dict:
    path = os.path.join(log_dir(account_dir), "liked.json")
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def save_liked(account_dir: str, liked: dict):
    path = os.path.join(log_dir(account_dir), "liked.json")
    with open(path, "w") as f:
        json.dump(liked, f, indent=2)



def blocked_subs(account_dir: str) -> set:
    path = os.path.join(account_dir, "blocked_subs.json")
    if not os.path.exists(path):
        return set()
    with open(path) as f:
        return set(json.load(f))


def add_blocked_sub(account_dir: str, sub: str):
    current = blocked_subs(account_dir)
    current.add(sub)
    path = os.path.join(account_dir, "blocked_subs.json")
    with open(path, "w") as f:
        json.dump(sorted(current), f)
