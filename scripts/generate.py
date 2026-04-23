"""Generate a comment using Claude Haiku via Anthropic SDK."""
import os, anthropic
import env; env.load()

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPTS_DIR)
ACCOUNTS_DIR = os.path.join(SKILL_DIR, "accounts")
GLOBAL_PLAYBOOK = os.path.join(SKILL_DIR, "playbook.md")

_client = None
_cache = {}

def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _load(path: str) -> str:
    if path not in _cache:
        _cache[path] = open(path).read()
    return _cache[path]


def generate_comment(post: dict, handle: str, intent: str) -> str:
    soul = _load(os.path.join(ACCOUNTS_DIR, handle, "soul.md"))
    account_playbook = _load(os.path.join(ACCOUNTS_DIR, handle, "playbook.md"))
    global_playbook = _load(GLOBAL_PLAYBOOK)

    prompt = f"""You are operating a Reddit account. Here is the persona:

{soul}

Here are the rules you must follow (intent: {intent}):

{global_playbook}

{account_playbook}

Write a single Reddit comment for the following post. Follow the rules strictly.
Be specific to the post content. Sound like a real human. No templates, no copy-paste patterns.

Post title: {post['title']}
Post content: {post['selftext'][:1500]}
Subreddit: r/{post['subreddit']}

Reply with ONLY the comment text. No explanations, no quotes around it."""

    msg = _get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text.strip()
