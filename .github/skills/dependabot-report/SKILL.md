---
name: dependabot-report
description: "Analyze GitHub Dependabot security alerts for this repository and generate a comprehensive upgrade report with breaking changes, effort estimates, and recommended versions. Requires gh CLI (preferred) or GITHUB_TOKEN. Uses gh api with --paginate and state=open filter for reliable, complete data retrieval."
tags:
  - dependencies
  - security
  - upgrades
  - analysis
---

# Dependabot Alert Analysis & Upgrade Report

## Overview

This skill fetches and analyzes only open GitHub Dependabot security alerts from the repository's security page, then generates a detailed report including:

- **Vulnerability summary** by severity and ecosystem
- **Affected packages** with current vs. recommended versions
- **Breaking changes** identified per package
- **Upgrade effort estimates** (low/medium/high)
- **Recommended upgrade path** (sequencing, compatibility)
- **Risk assessment** for each dependency

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

**GitHub Dependabot URL** (required)
- Format: `https://github.com/OWNER/REPO/security/dependabot`
- Example: `https://github.com/CBIIT/nci-webtools-dceg-linkage/security/dependabot`

### Steps

1. **Verify authentication** before fetching any data:
   ```bash
   gh auth status
   ```
   Check the output for `✓ Logged in` next to the active account. **Do not rely on the exit code alone** — when multiple accounts are configured and one has a stale token, `gh auth status` exits with code 1 even though the active account is valid. Only stop if *no* account shows `- Active account: true` with a valid token. Do **not** fall back silently — a failed or expired token returns HTTP 401 with no useful error body.

2. **Parse the input URL** to extract `OWNER` and `REPO`:
   - Input format: `https://github.com/OWNER/REPO/security/dependabot`
   - Derived API slug: `OWNER/REPO` (e.g. `CBIIT/nci-webtools-dceg-linkage`)
   - Do **not** pass the full HTML URL to the API — extract the slug first.

3. **Fetch only open Dependabot alerts** using `gh api` with the `state=open` filter and `--paginate` to handle repos with more than 100 alerts:
   ```bash
   gh api \
     --paginate \
     "repos/OWNER/REPO/dependabot/alerts?state=open&per_page=100" \
     > /tmp/dependabot-alerts.json
   ```
   Using `gh api` is strongly preferred over raw `curl` because it:
   - Injects auth headers automatically
   - Handles pagination with `--paginate`
   - Returns clean JSON regardless of response size

4. **Save the response to a temp file** before parsing. Do not attempt to pipe or inline large JSON — the response can exceed 30KB and will be truncated or mishandled in-shell. Always write to `/tmp/dependabot-alerts.json` first, then query from there.

5. **Parse with `jq`** — do not place `#` comment lines inside runnable command blocks; they produce **"command not found: #"** in zsh. Run each command individually or omit the comments.

   **Count open alerts:**
   ```bash
   jq 'length' /tmp/dependabot-alerts.json
   ```

   **Group by ecosystem with severity counts:**
   ```bash
   jq 'group_by(.dependency.package.ecosystem) |
     map({
       ecosystem: .[0].dependency.package.ecosystem,
       count: length,
       alerts: map({
         number,
         package: .dependency.package.name,
         severity: .security_vulnerability.severity,
         patched: .security_vulnerability.first_patched_version.identifier,
         cve: .security_advisory.cve_id,
         ghsa: .security_advisory.ghsa_id
       })
     })' /tmp/dependabot-alerts.json
   ```

6. **Cross-reference with local dependencies**:
   - `package.json` (repo root) for root-level npm packages (e.g. dev tools, CLI dependencies)
   - `client/package.json` for frontend npm packages
   - `server/requirements.txt` for pip packages

   Check all three files — some packages (e.g. `@anthropic-ai/claude-code`) live only in the root `package.json` and will be missed if only `client/package.json` is consulted.

7. **Assess breaking changes** by:
   - Reading package changelogs/release notes
   - Checking semantic versioning jumps (major version changes)
   - Noting deprecated APIs or removed features
   - Cross-referencing with codebase usage patterns

8. **Estimate effort** per package:
   - **Low**: Patch version, no API changes, auto-updateable
   - **Medium**: Minor version change, some API updates, manual testing needed
   - **High**: Major version change, significant refactoring, integration changes
   - **Critical**: Multiple dependent packages affected, ecosystem-wide changes

9. **Generate report** with:
   - Executive summary (total alerts, critical count)
   - Vulnerability table (severity, package, version, remediation)
   - Ecosystem breakdown (npm vs pip distributions)
   - Effort estimation matrix
   - Recommended update sequence (dependencies first, breaking changes last)
   - Risk mitigation strategies

### Output

Structured markdown report saved to **`DEPENDABOT-REPORT.md`** at the workspace root with:
- Executive summary table (total alerts, by severity and ecosystem)
- Per-ecosystem vulnerability tables (package, current version, patched version, severity, CVE/GHSA)
- Installation commands for each upgrade
- Breaking changes and effort estimates per package
- Recommended upgrade sequence
- Testing and rollback guidance

## Example Invocation

```
/dependabot-report https://github.com/CBIIT/nci-webtools-dceg-linkage/security/dependabot
```

## Notes

- **`gh api` vs `curl`**: Always use `gh api` — it handles auth injection, pagination, and avoids 401s from stale `GITHUB_TOKEN` values silently.
- **Pagination**: Use `--paginate` on `gh api` calls. Repos with many alerts will exceed the default 30-item page limit — without pagination, results will be silently incomplete.
- **Large responses**: API responses can exceed 30KB. Always write to a temp file (`/tmp/dependabot-alerts.json`) before parsing; do not attempt inline pipe processing.
- **`jq` required**: All JSON filtering and extraction should use `jq`. The Dependabot alert schema does not require jq's `//` null-coalescing operator for the standard queries, so inline `jq '...'` works. Avoid Python heredoc scripts in-shell — they fail with multiline strings, special characters, and terminal echo interference.
- **`#` comment lines break terminal blocks**: Shell comment lines (`# some comment`) cannot appear at the start of a command in a single terminal invocation — they produce "command not found: #". Run each command separately or omit comments from runnable examples.
- **`gh auth status` exit code is unreliable with multiple accounts**: When multiple GitHub accounts are configured and one has an expired token, `gh auth status` exits with code 1 even if the active account is valid. Always inspect the output text for `✓ Logged in` and `- Active account: true` rather than relying on the exit code. Only abort if no active account shows a valid session.
- **Root `package.json` matters**: npm alerts may reference packages declared in the repo root `package.json` (e.g. dev tools), not just `client/package.json`. Always check both.
- **State filter at the API level**: Pass `?state=open` as a query parameter to the API rather than filtering client-side. This reduces response size and avoids processing thousands of fixed/dismissed alerts.
- **URL parsing**: The input URL (`https://github.com/OWNER/REPO/security/dependabot`) is a web UI URL. Extract `OWNER/REPO` from it before constructing the API path — do not pass the full URL to `gh api`.
- **Stale data**: Dependabot alerts refresh on schedule. For real-time status, check GitHub UI directly.
- **Dependabot settings**: Ensure the repository has Dependabot enabled in Settings > Security & analysis.
- **Private repositories**: Requires proper permissions; verify your token has `security_events:read` scope.

## Related Resources

- [GitHub Dependabot documentation](https://docs.github.com/en/code-security/managing-vulnerabilities)
- [Repository dependency files](../../)
  - [Frontend dependencies](../../../client/package.json)
  - [Backend dependencies](../../../server/requirements.txt)
