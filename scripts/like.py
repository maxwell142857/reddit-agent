"""Upvote posts via old.reddit.com API through CDP."""
import os, random, time
from chrome import get_first_tab, navigate, eval_js
import logger as _logger

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPTS_DIR)
ACCOUNTS_DIR = os.path.join(SKILL_DIR, "accounts")


def upvote(port: int, post_id: str, subreddit: str, retries: int = 2) -> dict:
    for attempt in range(retries + 1):
        try:
            return _upvote_once(port, post_id, subreddit)
        except Exception as e:
            if attempt == retries:
                return {"ok": False, "error": str(e)}
            time.sleep(5)


def _upvote_once(port: int, post_id: str, subreddit: str) -> dict:
    ws = get_first_tab(port=port, timeout=30)
    try:
        navigate(ws, f"https://old.reddit.com/r/{subreddit}/comments/{post_id}/", wait=5)
        modhash = eval_js(ws, "document.querySelector(\"input[name=uh]\") ? document.querySelector(\"input[name=uh]\").value : (reddit.config.modhash || \"\")", msg_id=60)
        if not modhash:
            return {"ok": False, "error": "no_modhash"}

        js = f"""(function(){{
            $.ajax({{
                type: 'POST',
                url: 'https://old.reddit.com/api/vote',
                data: {{id: 't3_{post_id}', dir: 1, uh: '{modhash}', api_type: 'json'}},
                success: function(r){{ window._vr = JSON.stringify(r); }},
                error: function(e){{ window._vr = 'ERR:' + e.status; }}
            }});
            return 'fired';
        }})()"""
        eval_js(ws, js, msg_id=61)
        time.sleep(3)
        result = eval_js(ws, "window._vr || 'pending'", msg_id=62)

        if result.startswith("ERR:"):
            return {"ok": False, "error": result}
        return {"ok": True, "error": None}
    finally:
        ws.close()



def run_likes(handle: str, port: int, candidates: list[dict], limit: int, dry_run: bool = False):
    base = os.path.join(ACCOUNTS_DIR, handle)
    liked = _logger.load_liked(base)
    pool = [p for p in candidates if p["id"] not in liked]
    random.shuffle(pool)

    done = 0
    for post in pool:
        if done >= limit:
            break

        print(f"  [like] r/{post['subreddit']} | {post['title'][:60]}")

        if dry_run:
            print(f"  [like] dry-run, skipping")
            done += 1
            continue

        result = upvote(port, post["id"], post["subreddit"])
        print(f"  [like] result: {result}")

        if result["ok"]:
            liked[post["id"]] = {
                "url": post["url"],
                "title": post["title"],
                "subreddit": post["subreddit"],
            }
            _logger.save_liked(base, liked)
            done += 1
            delay = random.randint(10, 30)
            print(f"  [like] wait {delay}s")
            time.sleep(delay)

    print(f"[like] done. upvoted {done}/{limit}")
