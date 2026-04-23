"""Fetch candidate posts from subreddits via browser CDP (avoids Reddit API auth)."""
import json
from chrome import get_first_tab, navigate, eval_js

MIN_SCORE = 0
MAX_COMMENTS = 30
MIN_SELFTEXT = 80


def get_candidates(port: int, subreddit: str, limit: int = 25) -> list[dict]:
    ws = get_first_tab(port=port)
    try:
        navigate(ws, f"https://old.reddit.com/r/{subreddit}/.json?limit={limit}", wait=5)
        raw = eval_js(ws, "document.body.innerText", msg_id=30)
        data = json.loads(raw)
        posts = data.get("data", {}).get("children", [])
        candidates = []
        for p in posts:
            d = p.get("data", {})
            if d.get("stickied") or d.get("locked"):
                continue
            if d.get("removed_by_category") or d.get("selftext") in ("[removed]", "[deleted]"):
                continue
            if d.get("score", 0) < MIN_SCORE:
                continue
            if d.get("num_comments", 0) > MAX_COMMENTS:
                continue
            selftext = d.get("selftext", "")
            if len(selftext) < MIN_SELFTEXT:
                continue
            candidates.append({
                "id": d["id"],
                "subreddit": d["subreddit"],
                "title": d["title"],
                "selftext": selftext[:2000],
                "score": d["score"],
                "num_comments": d["num_comments"],
                "url": f"https://old.reddit.com/r/{d['subreddit']}/comments/{d['id']}/",
            })
        return candidates
    finally:
        ws.close()
