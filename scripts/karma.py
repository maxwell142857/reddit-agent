"""Check current Reddit karma for an account via browser CDP."""
import json
from chrome import get_first_tab, navigate, eval_js


def get_karma(port: int, username: str) -> dict:
    ws = get_first_tab(port=port)
    try:
        navigate(ws, f"https://old.reddit.com/user/{username}/about.json", wait=5)
        raw = eval_js(ws, "document.body.innerText", msg_id=40)
        data = json.loads(raw)
        if "error" in data:
            raise ValueError(f"Reddit API error {data['error']}: {data.get('message', '')}")
        d = data.get("data", {})
        comment_k = d.get("comment_karma", 0)
        link_k = d.get("link_karma", 0)
        return {"comment_karma": comment_k, "link_karma": link_k, "total": comment_k + link_k}
    except Exception as e:
        return {"comment_karma": 0, "link_karma": 0, "total": 0, "error": str(e)}
    finally:
        ws.close()
