"""
Login manager for reddit-agent.

New account:   python3 login.py --new vocAiInc
Existing:      python3 login.py vocAiInc
"""
import json, os, subprocess, sys, time
from chrome import list_tabs

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPTS_DIR)
ACCOUNTS_DIR = os.path.join(SKILL_DIR, "accounts")
PROFILES_DIR = os.path.join(SKILL_DIR, "chrome-profiles")

START_PORT = 9222


def find_free_port() -> int:
    used = set()
    if os.path.exists(ACCOUNTS_DIR):
        for handle in os.listdir(ACCOUNTS_DIR):
            cfg = os.path.join(ACCOUNTS_DIR, handle, "config.json")
            if os.path.exists(cfg):
                with open(cfg) as f:
                    port = json.load(f).get("chrome_port")
                    if port:
                        used.add(port)
    port = START_PORT
    while port in used:
        port += 1
    return port


def chrome_running(port: int) -> bool:
    try:
        list_tabs(port)
        return True
    except Exception:
        return False


def launch_chrome(port: int, profile_dir: str):
    subprocess.Popen([
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--remote-allow-origins=*",
        "--no-first-run",
        "--no-default-browser-check",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[login] launching Chrome on port {port}...")
    for _ in range(20):
        time.sleep(1)
        if chrome_running(port):
            return
    raise RuntimeError("Chrome did not start in time")


def create_account(port: int, username: str):
    account_dir = os.path.join(ACCOUNTS_DIR, username)
    os.makedirs(os.path.join(account_dir, "logs"), exist_ok=True)

    config_path = os.path.join(account_dir, "config.json")
    with open(config_path, "w") as f:
        json.dump({
            "username": username,
            "chrome_port": port,
            "daily_limits": {"warmup": 8, "promote": 0},
            "daily_likes": 10
        }, f, indent=2)

    for filename in ["soul.md", "playbook.md"]:
        dest = os.path.join(account_dir, filename)
        if not os.path.exists(dest):
            with open(dest, "w") as f:
                f.write(f"# {username} — {filename.replace('.md','').capitalize()}\n\n[Fill in content]\n")

    subs_path = os.path.join(account_dir, "subreddits.json")
    if not os.path.exists(subs_path):
        with open(subs_path, "w") as f:
            json.dump([], f, indent=2)

    print(f"[login] account created: accounts/{username}/")
    print(f"[login] next: fill in soul.md, playbook.md, subreddits.json")


def new_account(username: str):
    account_dir = os.path.join(ACCOUNTS_DIR, username)
    if os.path.exists(account_dir):
        print(f"[login] ERROR: account '{username}' already exists. Use: python3 login.py {username}")
        sys.exit(1)

    port = find_free_port()
    profile_dir = os.path.join(PROFILES_DIR, username)
    os.makedirs(profile_dir, exist_ok=True)

    if not chrome_running(port):
        launch_chrome(port, profile_dir)

    create_account(port, username)
    print(f"[login] Chrome running on port {port}.")
    print(f"[login] go to reddit.com and log in as {username}.")


def existing_account(handle: str):
    config_path = os.path.join(ACCOUNTS_DIR, handle, "config.json")
    if not os.path.exists(config_path):
        print(f"[login] ERROR: account '{handle}' not found. Use: python3 login.py --new {handle}")
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    port = config["chrome_port"]
    username = config["username"]
    profile_dir = os.path.join(PROFILES_DIR, username)

    if chrome_running(port):
        print(f"[login] Chrome already running on port {port} for {username}")
    else:
        if not os.path.exists(profile_dir):
            print(f"[login] ERROR: profile dir not found at {profile_dir}")
            sys.exit(1)
        launch_chrome(port, profile_dir)
        print(f"[login] Chrome launched on port {port} for {username}")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--new":
        new_account(sys.argv[2])
    elif len(sys.argv) == 2 and sys.argv[1] != "--new":
        existing_account(sys.argv[1])
    else:
        print("Usage:")
        print("  python3 login.py --new {username}   # create new account")
        print("  python3 login.py {handle}            # launch Chrome for existing account")
        sys.exit(1)
