"""Main runner — orchestrates a full daily session for one account."""
import json, os, random, sys, time
from datetime import date

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPTS_DIR)
sys.path.insert(0, SCRIPTS_DIR)

import chrome as _chrome
import fetch as _fetch
import submit as _submit
import karma as _karma
import logger as _logger
import generate as _generate
import like as _like

OPERATOR_DIR = os.path.join(SKILL_DIR, "accounts")


def load_account(handle: str) -> dict:
    base = os.path.join(OPERATOR_DIR, handle)
    with open(os.path.join(base, "config.json")) as f:
        config = json.load(f)
    with open(os.path.join(base, "subreddits.json")) as f:
        subreddits = json.load(f)
    config["_base"] = base
    config["_subreddits"] = subreddits
    return config


def run(handle: str, intent: str, dry_run: bool = False):
    print(f"[reddit-agent] {handle} | intent={intent} | date={date.today()} | dry_run={dry_run}")

    account = load_account(handle)
    base = account["_base"]
    port = account.get("chrome_port", 9222)
    username = account["username"]

    if not _chrome.ping(port=port):
        print(f"[reddit-agent] ERROR: Chrome not reachable at port {port}. Launch Chrome with --remote-debugging-port={port}")
        sys.exit(1)

    karma = _karma.get_karma(port, username)
    if "error" in karma:
        print(f"[reddit-agent] ERROR: karma check failed — {karma['error']}")
        sys.exit(1)
    _logger.log_karma(base, karma)
    print(f"[karma] comment={karma['comment_karma']} link={karma['link_karma']} total={karma['total']}")

    daily_limit = account.get("daily_limits", {}).get(intent, 5)
    stats = _logger.today_stats(base)
    already_today = stats["comments"]
    remaining = daily_limit - already_today

    if remaining <= 0:
        print(f"[reddit-agent] Daily limit reached ({daily_limit}). Done.")
        return

    print(f"[reddit-agent] Will post up to {remaining} comments today (already: {already_today})")

    replied = _logger.load_replied(base)
    blocked = _logger.blocked_subs(base)
    subs_config = account["_subreddits"]

    subs = [s["name"] for s in subs_config if s.get("intent") in (intent, "both") and s["name"] not in blocked]
    random.shuffle(subs)

    candidates = []
    for sub in subs:
        try:
            posts = _fetch.get_candidates(port, sub, limit=25)
            for p in posts:
                if p["id"] not in replied:
                    candidates.append(p)

        except Exception as e:
            print(f"[fetch] r/{sub} error: {e}")
        if len(candidates) >= remaining * 3:
            break

    random.shuffle(candidates)
    posted = 0

    for post in candidates:
        if posted >= remaining:
            break

        print(f"\n[post] r/{post['subreddit']} | {post['id']} | score={post['score']} | comments={post['num_comments']}")
        print(f"  title: {post['title'][:80]}")

        comment = _generate.generate_comment(post, handle, intent)
        if not comment:
            print("  [skip] empty comment generated")
            continue
        print(f"  comment: {comment[:120]}...")

        result = _submit.post_comment(port, post["id"], post["subreddit"], comment, dry_run=dry_run)
        print(f"  result: {result}")

        entry = {
            "url": post["url"],
            "ok": result["ok"],
        }
        if not dry_run:
            _logger.log_comment(base, entry)

        if (result.get("error") or "").startswith("ERR:500"):
            print(f"  [blocked] adding r/{post['subreddit']} to blocked list")
            _logger.add_blocked_sub(base, post["subreddit"])
        elif result["ok"]:
            replied[post["id"]] = {
                "url": post["url"],
                "title": post["title"],
                "subreddit": post["subreddit"],
            }
            _logger.save_replied(base, replied)
            posted += 1

        if posted < remaining:
            delay = random.randint(90, 240)
            print(f"  [wait] {delay}s")
            if not dry_run:
                time.sleep(delay)

    print(f"\n[reddit-agent] Done. Posted {posted} comments today (total: {already_today + posted}/{daily_limit})")
    final_stats = _logger.today_stats(base)
    print(f"[stats] ok={final_stats['ok']} errors={final_stats['errors']}")

    daily_likes = account.get("daily_likes", 0)
    if daily_likes > 0:
        print(f"\n[like] starting upvote session (limit={daily_likes})")
        _like.run_likes(handle, port, candidates, daily_likes, dry_run=dry_run)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("handle")
    parser.add_argument("intent", choices=["warmup", "promote"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(args.handle, args.intent, dry_run=args.dry_run)
