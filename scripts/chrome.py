"""Chrome CDP helpers — navigate, run JS, extract page data."""
import json, time, websocket, urllib.request


def get_first_tab(port: int = 9222, timeout: int = 20):
    tabs = list_tabs(port)
    pages = [t for t in tabs if t.get("type") == "page"]
    if not pages:
        raise RuntimeError(f"No page tabs found on port {port}")
    tab_id = pages[0]["id"]
    ws = websocket.create_connection(f"ws://localhost:{port}/devtools/page/{tab_id}", timeout=timeout)
    return ws


def send(ws, method: str, params: dict, msg_id: int = 1) -> dict:
    ws.send(json.dumps({"id": msg_id, "method": method, "params": params}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == msg_id:
            return msg


def navigate(ws, url: str, wait: float = 7.0) -> dict:
    r = send(ws, "Page.navigate", {"url": url}, msg_id=10)
    time.sleep(wait)
    return r


def eval_js(ws, expression: str, msg_id: int = 20) -> str:
    r = send(ws, "Runtime.evaluate", {"expression": expression, "returnByValue": True}, msg_id=msg_id)
    return r.get("result", {}).get("result", {}).get("value", "")



def list_tabs(port: int = 9222) -> list[dict]:
    with urllib.request.urlopen(f"http://localhost:{port}/json", timeout=5) as resp:
        return json.loads(resp.read())


def ping(port: int = 9222) -> bool:
    try:
        ws = get_first_tab(port=port, timeout=5)
        ws.close()
        return True
    except Exception:
        return False
