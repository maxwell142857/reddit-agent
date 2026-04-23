---
name: reddit-agent
user-invocable: true
description: "Unattended Reddit account operator. Manages karma warmup and promotion campaigns across multiple accounts. Each account has its own soul.md (persona), playbook.md (strategy), and subreddits.json (targets). Triggers: reddit agent, run reddit, reddit warmup, reddit promote, reddit karma"
allowed-tools: Bash(python3:*), Bash(pip3:*), Bash(ls:*), Bash(cat:*), Bash(mkdir:*), Read, Write, Glob
---

# Reddit Agent

Unattended Reddit account operator. Manages karma warmup and promotion across multiple Reddit accounts via Chrome CDP automation.

## Execution

When invoked as `/reddit-agent {handle} {intent} [--dry-run]`:

1. Parse `handle` and `intent` from the invocation. `intent` must be `warmup`, `promote`, or `report`.
2. Check account exists at `~/Desktop/reddit-agent/accounts/{handle}/`. If not, run setup first (see Creating a new account below).
3. Ensure Chrome is running: `python3 ~/Desktop/reddit-agent/scripts/login.py {handle}`
4. Run: `python3 ~/Desktop/reddit-agent/scripts/runner.py {handle} {intent} [--dry-run]`
5. Stream output to user. Report summary when done.

## Directory layout

```
~/Desktop/reddit-agent/
  SKILL.md
  playbook.md              # global rules — all accounts must follow
  .env                     # ANTHROPIC_API_KEY
  scripts/
    env.py                 # loads .env into os.environ
    chrome.py              # Chrome CDP helpers (navigate, eval_js, ping)
    fetch.py               # fetch candidate posts from subreddits
    karma.py               # check Reddit karma via CDP
    submit.py              # submit comment via jQuery AJAX through CDP
    like.py                # upvote posts via CDP
    generate.py            # generate comment using Claude Haiku
    logger.py              # local JSONL logs
    login.py               # Chrome launch + account setup
    runner.py              # main orchestrator
  accounts/
    {handle}/
      config.json          # username, chrome_port, daily_limits, daily_likes
      soul.md              # persona definition
      playbook.md          # per-account strategy (warmup + promote)
      subreddits.json      # target subreddits with intent tags
      logs/
        YYYY-MM-DD.jsonl   # daily comment log (url + ok)
        replied.json       # all replied post_ids with url/title
        liked.json         # all liked post_ids with url/title
        karma.json         # karma history (one entry per day)
  chrome-profiles/
    {handle}/              # Chrome user data dir — stores login cookies
```

## Creating a new account

When asked to create a new account:

1. `python3 ~/Desktop/reddit-agent/scripts/login.py --new {username}` — creates account dir + launches Chrome
2. User manually logs into Reddit in the browser
3. Fill in account files:
   - `config.json` — already created with defaults. Adjust `daily_limits` and `daily_likes` as needed.
   - `soul.md` — persona: who they are, background, writing style, things they say/never say. No placeholder text.
   - `playbook.md` — per-account strategy. Must include `## Intent: warmup` and `## Intent: promote` sections.
   - `subreddits.json` — list of target subreddits, each with `name`, `intent` (`warmup`/`promote`/`both`), `notes`.
4. Keep Chrome running — login session is stored in `chrome-profiles/{handle}/`.

## config.json fields

```json
{
  "username": "Reddit username (exact case)",
  "chrome_port": 9222,
  "daily_limits": {
    "warmup": 8,
    "promote": 0
  },
  "daily_likes": 5
}
```

- `chrome_port` — unique port per account, auto-assigned by login.py
- `daily_limits.warmup` — max comments per run in warmup mode
- `daily_limits.promote` — max comments per run in promote mode (0 = disabled)
- `daily_likes` — max upvotes per run

## Intents

| Intent | Description |
|--------|-------------|
| `warmup` | Build credibility — no product mentions. Prompt instructs Claude to focus on genuine value only. |
| `promote` | Natural product mention — same flow as warmup, prompt instructs Claude to mention the product when contextually relevant. |

## How it works

1. **Login** — Chrome launches with a persistent profile dir. User logs in once. Cookie survives restarts.
2. **CDP** — All Reddit interaction goes through Chrome DevTools Protocol on `localhost:{port}`. No Reddit API keys needed.
3. **Fetch** — Browser navigates to `old.reddit.com/r/{sub}/.json`, reads JSON. Filters: score≥0, comments≤30, selftext≥80 chars, not locked/stickied.
4. **Generate** — Claude Haiku reads global playbook + account playbook + soul, writes a contextual comment.
5. **Submit** — Browser navigates to post page, extracts modhash from `input[name=uh]`, fires jQuery AJAX POST to `/api/comment`.
6. **Like** — Same pattern: navigate to post, extract modhash, POST to `/api/vote`.
7. **Log** — Each comment logged to `YYYY-MM-DD.jsonl`. Replied/liked post IDs tracked to prevent duplicates.

## Anti-ban rules

- Random delay 90–240s between comments
- Random delay 10–30s between likes
- Daily comment limits enforced per config
- Already-replied post IDs tracked in `replied.json`
- Already-liked post IDs tracked in `liked.json`
- Subreddits returning ERR:500 added to `blocked_subs.json` permanently
- Each account uses its own Chrome instance on a unique port

## Multi-account setup

Each account runs on a different Chrome port:
```bash
python3 scripts/login.py --new accountA   # gets port 9222
python3 scripts/login.py --new accountB   # gets port 9223
```

Run each account independently:
```bash
python3 scripts/runner.py accountA warmup
python3 scripts/runner.py accountB warmup
```
