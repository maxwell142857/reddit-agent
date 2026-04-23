"""Submit a comment via old.reddit.com jQuery AJAX through CDP."""
import json, time
from chrome import get_first_tab, navigate, eval_js


def post_comment(port: int, post_id: str, subreddit: str, text: str, dry_run: bool = False) -> dict:
    if dry_run:
        return {"ok": True, "dry_run": True, "thing_id": f"t3_{post_id}"}

    ws = get_first_tab(port=port)
    try:
        navigate(ws, f"https://old.reddit.com/r/{subreddit}/comments/{post_id}/", wait=7)
        modhash = eval_js(ws, "document.querySelector(\"input[name=uh]\") ? document.querySelector(\"input[name=uh]\").value : (reddit.config.modhash || \"\")", msg_id=31)
        thing_id = eval_js(
            ws,
            "(function(){var l=document.querySelector('.thing.link');return l?l.getAttribute('data-fullname'):'t3_'+window.location.pathname.split('/')[5];})()",
            msg_id=32,
        )

        if not modhash:
            return {"ok": False, "error": "no_modhash"}

        escaped = text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
        js = f"""(function(){{
            $.ajax({{
                type:'POST',
                url:'https://old.reddit.com/api/comment',
                data:{{api_type:'json',thing_id:'{thing_id}',text:'{escaped}',uh:'{modhash}'}},
                success:function(r){{window._cr=JSON.stringify(r);}},
                error:function(e){{window._cr='ERR:'+e.status;}}
            }});
            return 'fired';
        }})()"""
        eval_js(ws, js, msg_id=33)
        time.sleep(5)
        result = eval_js(ws, "window._cr || 'pending'", msg_id=34)

        if result.startswith("ERR:"):
            return {"ok": False, "error": result, "thing_id": thing_id}
        try:
            parsed = json.loads(result)
            errors = parsed.get("json", {}).get("errors", [])
            if errors:
                return {"ok": False, "error": str(errors), "thing_id": thing_id}
        except Exception:
            pass
        return {"ok": True, "error": None, "thing_id": thing_id}
    finally:
        ws.close()
