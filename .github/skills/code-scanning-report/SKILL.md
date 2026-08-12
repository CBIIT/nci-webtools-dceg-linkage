---
name: code-scanning-report
description: "Analyze GitHub Code Scanning (SAST) alerts for a GitHub repository and generate a comprehensive report with severity breakdowns, rule/CWE mappings, affected source files with line numbers, and per-rule remediation guidance. Requires gh CLI (preferred) or GITHUB_TOKEN. Uses gh api with --paginate and a state=open filter for reliable, complete data retrieval."
argument-hint: "Code Scanning security URL or OWNER/REPO slug"
tags:
  - security
  - sast
  - code-scanning
  - analysis
---

# Code Scanning Alert Analysis & Report

## At a glance

| | |
|---|---|
| **Input** | A Code Scanning security URL, or an `OWNER/REPO` slug |
| **Output** | `CODESCAN-REPORT.md` at the workspace root (overwritten each run) |
| **Requires** | `gh`, `jq`, and a token that can read security alerts |
| **Reads** | Source files named in each alert's `location.path` |

## Overview

This skill fetches and analyzes only open GitHub Code Scanning alerts from the repository's security page, then generates a detailed report including:

- **Severity summary** (critical / high / medium / low / note)
- **Tool & scanner breakdown** (CodeQL version, any other scanners)
- **Rule / CWE table** with per-rule hit counts
- **Affected source files** with exact line numbers
- **Per-rule remediation guidance** keyed to CWE category
- **Risk prioritization** (critical and high findings addressed first)

## Prerequisites

See [Security Report Skills — setup](../README.md) for tool installation, authentication options, token
handling, and troubleshooting. In short: install `gh` and `jq`, then run `gh auth login` — or export a
`GITHUB_TOKEN` carrying the `security_events` scope.

**Security note:** never commit a token. Use environment variables or CI/CD secrets.

## Workflow

### Input

A Code Scanning security URL or an `OWNER/REPO` slug, passed as the slash-command argument.
- URL format: `https://github.com/OWNER/REPO/security/code-scanning`
- Example: `https://github.com/OWNER/REPO/security/code-scanning`
- A target is **required**. If none is given, ask for one rather than assuming a repository. Always write the result to `CODESCAN-REPORT.md` at the workspace root.

### Steps

1. **Verify authentication** before fetching any data:
   ```bash
   gh api user --jq .login
   ```
   This must print a username before continuing. Use it rather than `gh auth status`, whose exit code is unreliable when multiple accounts are configured — one stale token makes it exit non-zero even though the active account is valid. Stop and report the failure rather than falling back silently: an expired token returns HTTP 401 with no useful error body.

2. **Parse the input URL** to extract `OWNER` and `REPO`:
   - Input format: `https://github.com/OWNER/REPO/security/code-scanning`
   - Derived API slug: `OWNER/REPO`
   - Do **not** pass the full HTML URL to the API — extract the slug first.

3. **Fetch only open Code Scanning alerts** using `gh api` with the `state=open` filter, plus `--paginate` to handle repos with more than 100 alerts:
   ```bash
   gh api --paginate \
     "repos/OWNER/REPO/code-scanning/alerts?state=open&per_page=100" \
     > /tmp/code-scanning-alerts.json
   ```
   The page size defaults to 30 and caps at 100, so `--paginate` is mandatory — many repositories exceed one page. For array-returning REST endpoints like this one, `gh` merges the pages into a single JSON array, so the file is ready for `jq` as-is. Do **not** add `--slurp`; that flag is for GraphQL and object-returning endpoints, and here it would nest the results one level deeper.

   Using `gh api` is strongly preferred over raw `curl` because it injects auth headers automatically, follows pagination, and returns clean JSON regardless of response size. Always redirect to the temp file rather than piping the response onward — it can exceed 30 KB and gets truncated or mishandled in-shell.

4. **Parse with `jq`.** Keep short queries inline; move longer multi-line queries into a `.jq` file and run them with `jq -f`, which avoids nested-quoting mistakes. Do not mix `#` comment lines into runnable command blocks — they produce **"command not found: #"** in the terminal.

   **Confirm the fetch returned alerts, not an error.** A disabled feature or bad slug returns a JSON error *object*, not an array — on which `jq 'length'` misleadingly counts keys and `group_by` fails with `Cannot index string with string`. Guard before parsing:
   ```bash
   jq -e 'type == "array"' /tmp/code-scanning-alerts.json >/dev/null \
     || { jq -r '.message? // "Unexpected response"' /tmp/code-scanning-alerts.json; exit 1; }
   ```

   **Count open alerts:**
   ```bash
   jq 'length' /tmp/code-scanning-alerts.json
   ```

   **Severity breakdown:**
   ```bash
   cat > /tmp/severity.jq << 'JQEOF'
   group_by(.rule.security_severity_level // .rule.severity) |
   map({severity: (.[0].rule.security_severity_level // .[0].rule.severity), count: length}) |
   sort_by({critical:0,high:1,medium:2,low:3,error:4,warning:5,note:6}[.severity] // 9)
   JQEOF
   jq -f /tmp/severity.jq /tmp/code-scanning-alerts.json
   ```
   > Note: `rule.security_severity_level` is preferred (values: `critical`, `high`, `medium`, `low`). Non-security quality rules return `null` for it; fall back to `.rule.severity` (`error`, `warning`, `note`) for those.

   **Tool/scanner breakdown:**
   ```bash
   jq 'group_by(.tool.name) | map({tool: .[0].tool.name, version: .[0].tool.version, count: length})' /tmp/code-scanning-alerts.json
   ```
   > Record `tool.version` in the report — it reveals whether findings came from an outdated CodeQL analysis.

   **Rule / CWE breakdown:**
   ```bash
   cat > /tmp/rules.jq << 'JQEOF'
   group_by(.rule.id) |
   map({
     rule_id: .[0].rule.id,
     severity: (.[0].rule.security_severity_level // .[0].rule.severity),
     cwe_tags: (.[0].rule.tags // [] | map(select(startswith("external/cwe")))),
     description: .[0].rule.description,
     count: length
   }) |
   sort_by({critical:0,high:1,medium:2,low:3,error:4,warning:5,note:6}[.severity] // 9, .rule_id)
   JQEOF
   jq -f /tmp/rules.jq /tmp/code-scanning-alerts.json > /tmp/rules-parsed.json
   ```

   **Flat findings list with file paths and line numbers:**
   ```bash
   cat > /tmp/findings.jq << 'JQEOF'
   map({
     number,
     rule_id: .rule.id,
     severity: (.rule.security_severity_level // .rule.severity // ""),
     tool: .tool.name,
     file: (.most_recent_instance.location.path // ""),
     start_line: (.most_recent_instance.location.start_line // null),
     end_line: (.most_recent_instance.location.end_line // null),
     message: (.most_recent_instance.message.text // ""),
     cwe_tags: (.rule.tags // [] | map(select(startswith("external/cwe"))))
   }) |
   sort_by({critical:0,high:1,medium:2,low:3,error:4,warning:5,note:6}[.severity] // 9, .file, (.start_line // 0))
   JQEOF
   jq -f /tmp/findings.jq /tmp/code-scanning-alerts.json > /tmp/findings.json
   ```
   This produces `/tmp/findings.json` for use in the cross-reference and report steps.

5. **Cross-reference with local source files** — only when the scanned repo is the one checked out in the workspace. The `most_recent_instance.location.path` on each alert is the source of truth; local files are a best-effort convenience.

   When the target repo matches the workspace, verify each affected path exists locally and note the relevant module for remediation sequencing (e.g., fix shared utilities before callers). When it does not, skip local lookups and rely on the API paths.

6. **Map rules to CWE remediation guidance** using the `cwe_tags` extracted above. Common CWE categories and recommended fixes:

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

7. **Prioritize findings**:
   - **P1 — Fix immediately**: `critical` and `high` severity findings, especially injection (CWE-022, CWE-078, CWE-089, CWE-094, CWE-918) and XSS (CWE-079)
   - **P2 — Fix in next sprint**: `medium` severity and `high` severity non-injection issues
   - **P3 — Track and schedule**: `low` and `note` severity findings, style/code-quality warnings

8. **Generate report** and save it as `CODESCAN-REPORT.md` in the workspace root with the structure described in the Output section.

### Output

Structured markdown report saved to `CODESCAN-REPORT.md` at the workspace root with:

1. **Executive Summary** — total open alerts, count per severity tier, number of unique rules triggered, number of files affected
2. **Tool & Scanner Breakdown** — table of scanners (name, version, alert count)
3. **Rule / CWE Breakdown** — table of every rule triggered (rule ID, CWE tag(s), severity, hit count, one-line description)
4. **Affected Source Files** — per-file list with alert number, rule, and start line
5. **Per-Rule Remediation Guidance** — for each unique rule: severity, CWE, description, concrete fix instructions, and link to the CodeQL or CWE documentation
6. **Risk Prioritization** — P1/P2/P3 buckets listing specific alert numbers and files

## Example Invocation

Ask in plain language (the agent auto-loads this skill by description):

> Generate a code scanning report for OWNER/REPO

Or invoke its slash command directly:

```
/code-scanning-report https://github.com/OWNER/REPO/security/code-scanning
```

## Troubleshooting

See the [shared troubleshooting table](../README.md#troubleshooting) for auth, permission, and rate-limit
errors. Two issues are specific to this skill:

| Symptom | Fix |
|---------|-----|
| `HTTP 404` on a repository you can browse | Code Scanning is disabled, or no analysis has been uploaded yet. Enable it under Settings → Advanced Security and run the CodeQL workflow. |
| Every alert reports a `null` severity | The query read `rule.security_severity_level` without falling back to `rule.severity`. |

## Related Resources

- [GitHub Code Scanning documentation](https://docs.github.com/en/code-security/code-scanning)
- [Code scanning alerts REST API](https://docs.github.com/en/rest/code-scanning/code-scanning)
- [CodeQL query help](https://codeql.github.com/codeql-query-help/)
- [CWE list (MITRE)](https://cwe.mitre.org/data/index.html)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- Affected source files are discovered per alert via `most_recent_instance.location.path`; no fixed source tree is assumed.
