# Security Report Skills

Two agent skills that turn a GitHub repository's security alerts into a reviewable markdown report.

| Skill | Reads | Produces |
|-------|-------|----------|
| [dependabot-report](dependabot-report/SKILL.md) | Dependabot (dependency) alerts | `DEPENDABOT-REPORT.md` |
| [code-scanning-report](code-scanning-report/SKILL.md) | Code Scanning / CodeQL (SAST) alerts | `CODESCAN-REPORT.md` |

This page covers the setup both skills share. Each `SKILL.md` documents only its own workflow.

## Prerequisites

| Tool | Why |
|------|-----|
| [GitHub CLI](https://cli.github.com/) (`gh`) | All API calls: auth injection and pagination. |
| [jq](https://jqlang.github.io/jq/) | JSON parsing and filtering. |

Check what you have:

```bash
gh --version && jq --version
```

On macOS: `brew install gh jq`.

## Authentication

Both skills read security alerts, which always requires authentication.

### Option A — GitHub CLI (recommended)

```bash
gh auth login
```

Choose `GitHub.com` → `HTTPS` → authenticate in the browser. The default scopes `gh` requests include `repo`,
which already grants read access to the target repository's security alerts — there is nothing extra to select. If
a call is later rejected for scope reasons, top up with:

```bash
gh auth refresh -h github.com -s security_events
```

### Option B — Personal access token

Use this in CI, or when you cannot run an interactive login.

1. Create a token:
   - **Classic token:** [Settings → Developer settings → Personal access tokens (classic)](https://github.com/settings/tokens) → *Generate new token (classic)* → select **`security_events`** (or `repo`, which also covers it). For public repositories `public_repo` is enough.
   - **Fine-grained token:** [Settings → Developer settings → Fine-grained tokens](https://github.com/settings/personal-access-tokens) → grant the target repository **Dependabot alerts: Read-only** and **Code scanning alerts: Read-only**.
2. Export it:
   ```bash
   export GITHUB_TOKEN="your_token_here"
   ```

`gh` picks up `GITHUB_TOKEN` (or `GH_TOKEN`) from the environment automatically — do not run
`gh auth login` as well. While either variable is set it overrides any stored CLI credentials.

### Verify before you run a skill

```bash
gh api user --jq .login
```

If this prints your username, you are authenticated. Prefer it over `gh auth status`, whose exit code is
unreliable: with multiple accounts configured, one stale token makes it exit non-zero even when the active
account is fine.

Confirm the token can actually read alerts on the target repository:

```bash
gh api "repos/OWNER/REPO/dependabot/alerts?state=open&per_page=1" --jq 'length'
```

## Token handling

Do:

- Keep `GITHUB_TOKEN` in your shell profile (`~/.zshrc`, `~/.bashrc`) or a secret manager.
- Grant the narrowest scope that works — `security_events` for a classic token, or read-only fine-grained permissions. Reach for `repo` only if you also need write access.
- Set an expiry and rotate on schedule.
- Use separate tokens per machine and per purpose.

Don't:

- Commit a token, or paste one into chat, email, or an issue.
- Grant `repo` when `security_events` alone is enough.
- Reuse one token across devices, so a leak means revoking everything.

If a token is ever exposed, revoke it immediately at
[Settings → Developer settings](https://github.com/settings/tokens).

## Running a skill

Ask the agent in plain language, naming the repository:

> Generate a Dependabot report for OWNER/REPO

Or invoke a skill's slash command directly, passing the repository URL or `OWNER/REPO` slug:

```
/dependabot-report https://github.com/OWNER/REPO/security/dependabot
/code-scanning-report https://github.com/OWNER/REPO/security/code-scanning
```

Each skill is both auto-loaded when a request matches its description and available as a slash command
(type `/`). There are no separate prompt wrappers.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `HTTP 401` | Token missing, expired, or revoked | Re-run `gh auth login`, or export a fresh `GITHUB_TOKEN`. Verify with `gh api user --jq .login`. |
| `HTTP 403` | Token lacks a scope that grants alert access, or you lack repo access | Regenerate the token with `security_events`, or run `gh auth refresh -s security_events`; confirm your access in the repository's Settings. |
| `HTTP 404` | Wrong slug, private repo, or the feature is disabled | Check `OWNER/REPO`; enable the feature under Settings → Advanced Security. A 404 (not 403) is also how GitHub hides repos you cannot see. |
| `Rate limit exceeded` | Over 5,000 requests/hour | Check the reset time with `gh api rate_limit --jq .rate`. |
| Alert count is lower than the GitHub UI shows | The fetch omitted `--paginate`, so only the first 30-100 alerts were read | See the fetch command in each `SKILL.md`; it must pass `--paginate`. |
| `command not found: #` | A shell comment was sent as the first line of a command | Run the command without the comment. |

## Applying to any repository

These skills are repository-agnostic: pass any `OWNER/REPO` slug or security URL, and each report is
derived entirely from the alert data returned by the API — no repository is hardcoded. The optional
local cross-reference step (step 5 in each skill) reads whatever manifest or source paths the alerts
name, so run the skill from a workspace checked out to the same repository if you want that local
context.

