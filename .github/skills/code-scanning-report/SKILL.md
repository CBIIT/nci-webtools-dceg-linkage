---
name: code-scanning-report
description: "Analyze GitHub Code Scanning (SAST) alerts for this repository and generate a comprehensive report with severity breakdowns, rule/CWE mappings, affected source files with line numbers, and per-rule remediation guidance. Requires gh CLI (preferred) or GITHUB_TOKEN. Uses gh api with --paginate and state=open filter for reliable, complete data retrieval."
tags:
  - security
  - sast
  - code-scanning
  - analysis
---

# Code Scanning Alert Analysis & Report

## Overview

This skill fetches and analyzes only open GitHub Code Scanning alerts from the repository's security page, then generates a detailed report including:

- **Severity summary** (critical / high / medium / low / note)
- **Tool & scanner breakdown** (CodeQL version, any other scanners)
- **Rule / CWE table** with per-rule hit counts
- **Affected source files** with exact line numbers
- **Per-rule remediation guidance** keyed to CWE category
- **Risk prioritization** (critical and high findings addressed first)

## Prerequisites

**Required tools:**
- `gh` (GitHub CLI) — used for all API calls; handles auth and pagination automatically
- `jq` — used for JSON parsing and filtering of API responses

**GitHub authentication (preferred order):**

1. Use `gh` CLI if already authenticated (`gh auth status` returns success)
2. Otherwise fall back to `GITHUB_TOKEN` environment variable

**Option A: GitHub CLI (preferred)**
```bash
gh auth login
gh auth status  # Verify authentication
```

**Option B: Set GITHUB_TOKEN manually**
Set `GITHUB_TOKEN` with a GitHub Personal Access token that has `security_events:read` scope:

```bash
export GITHUB_TOKEN="ghp_your_token_here"
gh auth login --with-token <<< "$GITHUB_TOKEN"
```

⚠️ **Security note:** Never commit `GITHUB_TOKEN` to version control. Use environment variables or CI/CD secrets for sensitive tokens.

⚠️ **Validation note:** Always verify the token works before proceeding. A set-but-expired `GITHUB_TOKEN` will cause a silent 401. Use `gh auth status` or a test API call to confirm access before fetching alerts.

## Workflow

### Input

**GitHub Code Scanning URL** (required)
- Format: `https://github.com/OWNER/REPO/security/code-scanning`
- Example: `https://github.com/CBIIT/nci-webtools-dceg-linkage/security/code-scanning`

### Steps

1. **Verify authentication** before fetching any data:
   ```bash
   gh auth status
   ```
   Check the output for `✓ Logged in` next to the active account. **Do not rely on the exit code alone** — when multiple accounts are configured and one has a stale token, `gh auth status` exits with code 1 even though the active account is valid. Only stop if *no* account shows `- Active account: true` with a valid token. Do **not** fall back silently — a failed or expired token returns HTTP 401 with no useful error body.

2. **Parse the input URL** to extract `OWNER` and `REPO`:
   - Input format: `https://github.com/OWNER/REPO/security/code-scanning`
   - Derived API slug: `OWNER/REPO` (e.g. `CBIIT/nci-webtools-dceg-linkage`)
   - Do **not** pass the full HTML URL to the API — extract the slug first.

3. **Fetch only open Code Scanning alerts** using `gh api` with the `state=open` filter and `--paginate` to handle repos with more than 100 alerts:
   ```bash
   gh api \
     --paginate \
     "repos/OWNER/REPO/code-scanning/alerts?state=open&per_page=100" \
     > /tmp/code-scanning-alerts.json
   ```
   Using `gh api` is strongly preferred over raw `curl` because it:
   - Injects auth headers automatically
   - Handles pagination with `--paginate`
   - Returns clean JSON regardless of response size

4. **Save the response to a temp file** before parsing. Do not attempt to pipe or inline large JSON — the response can exceed 30 KB and will be truncated or mishandled in-shell. Always write to `/tmp/code-scanning-alerts.json` first, then query from there.

5. **Parse with `jq`** — write all complex queries to temp `.jq` files and execute with `jq -f`. Do **not** pass multi-field jq expressions containing `//` directly as shell arguments — jq's null-coalescing operator `//` causes a **"syntax error, unexpected //"** on zsh when inline-quoted. Also do not mix `#` comment lines into runnable command blocks — they produce **"command not found: #"** in the terminal.

   **Count open alerts** (safe to run inline — no `//`):
   ```bash
   jq 'length' /tmp/code-scanning-alerts.json
   ```

   **Severity breakdown** — write to a file first:
   ```bash
   cat > /tmp/severity.jq << 'JQEOF'
   group_by(.rule.security_severity_level) |
   map({severity: .[0].rule.security_severity_level, count: length}) |
   sort_by(.severity)
   JQEOF
   jq -f /tmp/severity.jq /tmp/code-scanning-alerts.json
   ```
   > Note: `rule.security_severity_level` is preferred (values: `critical`, `high`, `medium`, `low`). If some alerts return `null` for that field, fall back to `.rule.severity` (`error`, `warning`, `note`) — but handle this in Python (see below) to avoid the `//` quoting issue.

   **Tool/scanner breakdown** (safe to run inline — no `//`):
   ```bash
   jq 'group_by(.tool.name) | map({tool: .[0].tool.name, version: .[0].tool.version, count: length})' /tmp/code-scanning-alerts.json
   ```

   **Rule / CWE breakdown** — write to a file:
   ```bash
   cat > /tmp/rules.jq << 'JQEOF'
   group_by(.rule.id) |
   map({
     rule_id: .[0].rule.id,
     severity: .[0].rule.security_severity_level,
     cwe_tags: (.[0].rule.tags // [] | map(select(startswith("external/cwe")))),
     description: .[0].rule.description,
     count: length
   }) |
   sort_by(.severity, .rule_id)
   JQEOF
   jq -f /tmp/rules.jq /tmp/code-scanning-alerts.json > /tmp/rules-parsed.json
   ```

   **Flat findings list with file paths and line numbers** — use Python to avoid all quoting issues with `//` and multi-field projections:
   ```bash
   python3 -c "
   import json
   with open('/tmp/code-scanning-alerts.json') as f:
       alerts = json.load(f)
   findings = []
   for a in alerts:
       loc = a.get('most_recent_instance', {}).get('location', {})
       tags = a.get('rule', {}).get('tags') or []
       findings.append({
           'number': a['number'],
           'rule_id': a['rule']['id'],
           'severity': a['rule'].get('security_severity_level') or a['rule'].get('severity', ''),
           'tool': a['tool']['name'],
           'file': loc.get('path', ''),
           'start_line': loc.get('start_line', ''),
           'end_line': loc.get('end_line', ''),
           'message': (a.get('most_recent_instance', {}).get('message') or {}).get('text', ''),
           'cwe_tags': [t for t in tags if t.startswith('external/cwe')]
       })
   findings.sort(key=lambda x: (x['severity'], x['file'], x['start_line'] or 0))
   with open('/tmp/findings.json', 'w') as f:
       json.dump(findings, f, indent=2)
   print(f'Written {len(findings)} findings')
   "
   ```
   This produces `/tmp/findings.json` for use in the cross-reference and report steps.

6. **Cross-reference with local source files**:
   - `server/` for Python backend files
   - `client/src/` for Next.js / TypeScript frontend files

   For each affected file path returned by the API, verify the file exists locally and note the relevant module. This gives context for remediation sequencing (e.g., fix shared utilities before callers).

7. **Map rules to CWE remediation guidance** using the `cwe_tags` extracted above. Common CWE categories and recommended fixes:

   | CWE | Category | Common CodeQL Rule | Remediation |
   |-----|----------|--------------------|-------------|
   | CWE-022 | Path traversal | `py/path-injection`, `js/path-injection` | Validate and canonicalize paths; reject `..` sequences |
   | CWE-078 | OS command injection | `py/command-injection`, `js/shell-command-injection` | Avoid `shell=True`; use subprocess with arg lists; sanitize inputs |
   | CWE-079 | XSS | `js/xss` | Escape output; use framework-level sanitization; avoid `dangerouslySetInnerHTML` |
   | CWE-089 | SQL injection | `py/sql-injection`, `js/sql-injection` | Use parameterized queries / prepared statements |
   | CWE-094 | Code injection | `py/code-injection` | Avoid `eval()`/`exec()` on untrusted input |
   | CWE-116 | Encoding/escaping | `js/incomplete-html-attribute-sanitization` | Use well-tested sanitization libraries |
   | CWE-312 | Cleartext secrets | `py/clear-text-logging-sensitive-data` | Redact sensitive fields before logging |
   | CWE-400 | ReDoS | `js/redos` | Rewrite regex; use `safe-regex` lint rule |
   | CWE-601 | Open redirect | `py/url-redirection`, `js/url-redirection` | Validate redirect targets against an allowlist |
   | CWE-918 | SSRF | `py/full-ssrf`, `py/partial-ssrf` | Validate and restrict outbound request targets |

   For any CWE not listed here, look up the CWE description at `https://cwe.mitre.org/data/definitions/<ID>.html` and describe the fix generically.

8. **Prioritize findings**:
   - **P1 — Fix immediately**: `critical` and `high` severity findings, especially injection (CWE-022, CWE-078, CWE-089, CWE-094, CWE-918) and XSS (CWE-079)
   - **P2 — Fix in next sprint**: `medium` severity and `high` severity non-injection issues
   - **P3 — Track and schedule**: `low` and `note` severity findings, style/code-quality warnings

9. **Generate report** and save it as `CODESCAN-REPORT.md` in the workspace root with the structure described in the Output section.

### Output

Structured markdown report saved to `CODESCAN-REPORT.md` at the workspace root with:

1. **Executive Summary** — total open alerts, count per severity tier, number of unique rules triggered, number of files affected
2. **Tool & Scanner Breakdown** — table of scanners (name, version, alert count)
3. **Rule / CWE Breakdown** — table of every rule triggered (rule ID, CWE tag(s), severity, hit count, one-line description)
4. **Affected Source Files** — per-file list with alert number, rule, and start line
5. **Per-Rule Remediation Guidance** — for each unique rule: severity, CWE, description, concrete fix instructions, and link to the CodeQL or CWE documentation
6. **Risk Prioritization** — P1/P2/P3 buckets listing specific alert numbers and files

## Example Invocation

```
/code-scanning-report https://github.com/CBIIT/nci-webtools-dceg-linkage/security/code-scanning
```

## Notes

- **`gh api` vs `curl`**: Always use `gh api` — it handles auth injection, pagination, and avoids 401s from stale `GITHUB_TOKEN` values silently.
- **Pagination**: Use `--paginate` on `gh api` calls. Repos with many alerts will exceed the default 30-item page limit — without pagination, results will be silently incomplete.
- **Large responses**: API responses can exceed 30 KB. Always write to a temp file (`/tmp/code-scanning-alerts.json`) before parsing; do not attempt inline pipe processing.
- **`jq` required**: All JSON filtering and extraction should use `jq` where possible, or `python3 -c` for complex multi-field queries. Avoid heredoc-based Python scripts in-shell — they fail with multiline strings, special characters, and terminal echo interference.
- **jq `//` operator causes zsh syntax errors when inline**: jq's null-coalescing operator (`//`) is misinterpreted by zsh when passed as a shell argument inside single quotes. Always write jq expressions containing `//` to a temp file (`/tmp/script.jq`) using a heredoc and run via `jq -f /tmp/script.jq`. Alternatively, fall back to `python3 -c` for complex multi-field extractions — this is reliable across all shells.
- **`#` comment lines break multi-command blocks**: Shell comment lines (`# some comment`) cannot appear at the start of a command in a single terminal invocation — they produce "command not found: #". Either run commands individually, place comments inside a shell script file, or omit them from runnable examples.
- **`gh auth status` exit code is unreliable with multiple accounts**: When multiple GitHub accounts are configured and one has an expired token, `gh auth status` exits with code 1 even if the active account is valid. Always inspect the output text for `✓ Logged in` and `- Active account: true` rather than relying on the exit code. Only abort if no active account shows a valid session.
- **State filter at the API level**: Pass `?state=open` as a query parameter to the API rather than filtering client-side. This reduces response size and avoids processing thousands of fixed/dismissed alerts.
- **URL parsing**: The input URL (`https://github.com/OWNER/REPO/security/code-scanning`) is a web UI URL. Extract `OWNER/REPO` from it before constructing the API path — do not pass the full URL to `gh api`.
- **Severity field names**: Code Scanning alerts carry two severity-related fields. Prefer `rule.security_severity_level` (values: `critical`, `high`, `medium`, `low`) over `rule.severity` (values: `error`, `warning`, `note`). The latter is a code-quality signal, not a security rating; always fall back to it with `// .rule.severity` if `security_severity_level` is absent.
- **Tool versions**: The `tool.version` field is present for CodeQL runs. Record it in the report to track whether findings are from an outdated analysis version.
- **Dismissed alerts**: The API returns `state=open` records only. Dismissed alerts (false positives) are excluded and do not need to be processed.
- **Code Scanning must be enabled**: Ensure the repository has Code Scanning enabled in Settings > Security & analysis, and that at least one analysis has been uploaded (via CodeQL Actions workflow or SARIF upload).
- **Private repositories**: Requires proper permissions; verify your token has `security_events:read` scope.

## Related Resources

- [GitHub Code Scanning documentation](https://docs.github.com/en/code-security/code-scanning)
- [CodeQL query help (GitHub)](https://codeql.github.com/codeql-query-help/)
- [CWE list (MITRE)](https://cwe.mitre.org/data/index.html)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Repository source files](../../)
  - [Backend source](../../../server/)
  - [Frontend source](../../../client/src/)
