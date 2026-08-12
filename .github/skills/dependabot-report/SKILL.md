---
name: dependabot-report
description: "Analyze GitHub Dependabot security alerts for a GitHub repository and generate a comprehensive upgrade report with breaking changes, effort estimates, and recommended versions. Requires gh CLI (preferred) or GITHUB_TOKEN. Uses gh api with --paginate and a state=open filter for reliable, complete data retrieval."
argument-hint: "Dependabot security URL or OWNER/REPO slug"
tags:
  - dependencies
  - security
  - upgrades
  - analysis
---

# Dependabot Alert Analysis & Upgrade Report

## At a glance

| | |
|---|---|
| **Input** | A Dependabot security URL, or an `OWNER/REPO` slug |
| **Output** | `DEPENDABOT-REPORT.md` at the workspace root (overwritten each run) |
| **Requires** | `gh`, `jq`, and a token that can read security alerts |
| **Reads** | Dependency manifests named in each alert's `manifest_path` (e.g. `package.json`, `requirements.txt`) |

## Overview

This skill fetches and analyzes only open GitHub Dependabot security alerts from the repository's security page, then generates a detailed report including:

- **Vulnerability summary** by severity and ecosystem
- **Affected packages** with current vs. recommended versions
- **Breaking changes** identified per package
- **Upgrade effort estimates** (low/medium/high)
- **Recommended upgrade path** (sequencing, compatibility)
- **Risk assessment** for each dependency

## Prerequisites

See [Security Report Skills — setup](../README.md) for tool installation, authentication options, token
handling, and troubleshooting. In short: install `gh` and `jq`, then run `gh auth login` — or export a
`GITHUB_TOKEN` carrying the `security_events` scope.

**Security note:** never commit a token. Use environment variables or CI/CD secrets.

## Workflow

### Input

A Dependabot security URL or an `OWNER/REPO` slug, passed as the slash-command argument.
- URL format: `https://github.com/OWNER/REPO/security/dependabot`
- Example: `https://github.com/OWNER/REPO/security/dependabot`
- A target is **required**. If none is given, ask for one rather than assuming a repository. Always write the result to `DEPENDABOT-REPORT.md` at the workspace root.

### Steps

1. **Verify authentication** before fetching any data:
   ```bash
   gh api user --jq .login
   ```
   This must print a username before continuing. Use it rather than `gh auth status`, whose exit code is unreliable when multiple accounts are configured — one stale token makes it exit non-zero even though the active account is valid. Stop and report the failure rather than falling back silently: an expired token returns HTTP 401 with no useful error body.

2. **Parse the input URL** to extract `OWNER` and `REPO`:
   - Input format: `https://github.com/OWNER/REPO/security/dependabot`
   - Derived API slug: `OWNER/REPO`
   - Do **not** pass the full HTML URL to the API — extract the slug first.

3. **Fetch only open Dependabot alerts** using `gh api` with the `state=open` filter, plus `--paginate` to handle repos with more than 100 alerts:
   ```bash
   gh api --paginate \
     "repos/OWNER/REPO/dependabot/alerts?state=open&per_page=100" \
     > /tmp/dependabot-alerts.json
   ```
   The page size defaults to 30 and caps at 100, so `--paginate` is mandatory — without it the report is silently truncated. For array-returning REST endpoints like this one, `gh` merges the pages into a single JSON array, so the file is ready for `jq` as-is. Do **not** add `--slurp`; that flag is for GraphQL and object-returning endpoints, and here it would nest the results one level deeper.

   Using `gh api` is strongly preferred over raw `curl` because it injects auth headers automatically, follows pagination, and returns clean JSON regardless of response size. Always redirect to the temp file rather than piping the response onward — it can exceed 30KB and gets truncated or mishandled in-shell.

4. **Parse with `jq`.** Do not place `#` comment lines inside runnable command blocks; they produce **"command not found: #"** in zsh. Run each command individually or omit the comments.

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

5. **Cross-reference with local dependencies** — only when the scanned repo is the one checked out in the workspace. Each alert's `dependency.manifest_path` is the source of truth for which manifest declares the package; local files are a best-effort convenience.

   When the target repo matches the workspace, open the manifest named in each alert's `manifest_path` (e.g. `package.json`, `requirements.txt`) to confirm whether the package is a direct or transitive dependency. A package may appear in more than one manifest, so check each path the alerts reference.

6. **Assess breaking changes** by:
   - Reading package changelogs/release notes
   - Checking semantic versioning jumps (major version changes)
   - Noting deprecated APIs or removed features
   - Cross-referencing with codebase usage patterns

7. **Estimate effort** per package:
   - **Low**: Patch version, no API changes, auto-updateable
   - **Medium**: Minor version change, some API updates, manual testing needed
   - **High**: Major version change, significant refactoring, integration changes
   - **Critical**: Multiple dependent packages affected, ecosystem-wide changes

8. **Generate report** with:
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

Ask in plain language (the agent auto-loads this skill by description):

> Generate a Dependabot report for OWNER/REPO

Or invoke its slash command directly:

```
/dependabot-report https://github.com/OWNER/REPO/security/dependabot
```

> Alerts are a snapshot: Dependabot rescans on a schedule, so the report reflects the last scan, not live state — date any report you circulate.

## Troubleshooting

See the [shared troubleshooting table](../README.md#troubleshooting) for auth, permission, and rate-limit
errors. Two issues are specific to this skill:

| Symptom | Fix |
|---------|-----|
| `HTTP 404` on a repository you can browse | Dependabot alerts are disabled. Enable them under Settings → Advanced Security. |
| Report lists fewer alerts than the GitHub UI | The fetch dropped `--paginate`, or a severity filter was left on the query string. |

## Related Resources

- [GitHub Dependabot documentation](https://docs.github.com/en/code-security/dependabot)
- [Dependabot alerts REST API](https://docs.github.com/en/rest/dependabot/alerts)
- Dependency manifests are discovered per alert via `dependency.manifest_path`; common examples are `package.json` and `requirements.txt`. Nothing is hardcoded to a specific repository.
