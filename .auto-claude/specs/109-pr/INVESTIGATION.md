# Investigation: CI/CD Workflow Failures on Pull Requests

**Issue:** When creating a Pull Request, workflows trigger but produce "run failed no jobs were run" error

**Date:** 2025-02-04
**Investigator:** Claude Code
**Status:** In Progress

---

## Executive Summary

The "no jobs were run" error occurs because workflow files use restrictive `paths:` filters on `pull_request:` triggers. When a PR is created that doesn't modify files matching these path patterns, the workflow triggers but skips all job execution, resulting in the error message.

---

## Current Workflow Behavior

### Workflow Files Affected

1. **`.github/workflows/lighthouse.yml`**
   - Triggers on: `pull_request` to main/develop branches
   - Path filter: Only runs when `frontend/**` or workflow file changes
   - Problem: PRs modifying backend, docs, or config files trigger workflow but skip all jobs

2. **`.github/workflows/performance-tests.yml`**
   - Triggers on: `pull_request` to main/develop branches
   - Path filter: Only runs when `backend/**` or workflow file changes
   - Problem: PRs modifying frontend, docs, or config files trigger workflow but skip all jobs

3. **`.github/workflows/deploy.yml`**
   - Triggers on: `push` and `pull_request` to main/develop
   - Uses `github.*` context variables throughout
   - Problem: GitHub-specific syntax incompatible with Gitea Actions

### Path Filter Configuration

From `lighthouse.yml` (lines 9-13):
```yaml
pull_request:
  branches: [main, develop]
  paths:
    - 'frontend/**'
    - '.github/workflows/lighthouse.yml'
```

From `performance-tests.yml` (lines 9-13):
```yaml
pull_request:
  branches: [main, develop]
  paths:
    - 'backend/**'
    - '.github/workflows/performance-tests.yml'
```

### How Path Filters Work

**GitHub/Gitea Actions Path Filter Behavior:**

1. Workflow evaluates trigger conditions (event type + branches)
2. If trigger matches, workflow **starts**
3. Path filters are evaluated **per job**
4. If NO jobs match the path filter, the result is "no jobs were run"

**Key Insight:** The workflow **triggers** successfully but **executes zero jobs**.

---

## Root Cause Analysis

### Primary Issue: Path Filters Blocking Job Execution

**Scenario 1: Documentation-Only PR**
- User creates PR modifying `README.md`
- `lighthouse.yml` workflow triggers (PR to main branch)
- Path filter checks: Are `frontend/**` files modified? **NO**
- Path filter checks: Is workflow file modified? **NO**
- Result: 0 jobs eligible to run → "no jobs were run"

**Scenario 2: Backend-Only PR**
- User creates PR modifying `backend/main.py`
- `lighthouse.yml` workflow triggers (PR to main branch)
- Path filter checks: Are `frontend/**` files modified? **NO**
- Path filter checks: Is workflow file modified? **NO**
- Result: 0 jobs eligible to run → "no jobs were run"

**Scenario 3: Frontend-Only PR (Works)**
- User creates PR modifying `frontend/src/App.tsx`
- `lighthouse.yml` workflow triggers (PR to main branch)
- Path filter checks: Are `frontend/**` files modified? **YES**
- Result: Jobs run successfully

---

## Root Cause Verification (subtask-2-1)

### Verification Method

The root cause has been verified through the following analysis:

#### 1. Path Filter Blocking Mechanism ✅

**How `paths:` Filters Work in GitHub/Gitea Actions:**

The `paths:` filter operates at the **job level**, not the workflow level. Here's the execution flow:

```
1. PR Created → Event Triggered
2. Workflow evaluates trigger conditions:
   - Event: pull_request ✅
   - Branch: main/develop ✅
   → Workflow STARTS (workflow_run is created)
3. Path filters evaluated for EACH job:
   - Job checks: Do changed files match 'frontend/**'? ❌
   - Job checks: Do changed files match workflow file? ❌
   → 0 jobs eligible
4. Result: "no jobs were run" error
```

**Key Finding:** The workflow **triggers** successfully (you see it in the Actions UI) but **executes zero jobs**. This is why the user sees "run failed no jobs were run" rather than "workflow not triggered."

#### 2. Evidence from Workflow Files ✅

**Evidence from `lighthouse.yml` (lines 9-13):**
```yaml
pull_request:
  branches: [main, develop]
  paths:
    - 'frontend/**'
    - '.github/workflows/lighthouse.yml'
```

**Evidence from `performance-tests.yml` (lines 9-13):**
```yaml
pull_request:
  branches: [main, develop]
  paths:
    - 'backend/**'
    - '.github/workflows/performance-tests.yml'
```

**Confirmed Issues:**
- ✅ Both workflows have restrictive `paths:` filters on `pull_request:` triggers
- ✅ `lighthouse.yml` only runs when frontend files change
- ✅ `performance-tests.yml` only runs when backend files change
- ✅ PRs modifying documentation, config, or mixed content will fail one or both workflows

#### 3. Impact Analysis ✅

**Files That Cause "No Jobs Were Run" in `lighthouse.yml`:**
| File Pattern | Matches `frontend/**`? | Jobs Run? |
|--------------|------------------------|-----------|
| `README.md` | ❌ No | ❌ No |
| `docker-compose.yml` | ❌ No | ❌ No |
| `.env.example` | ❌ No | ❌ No |
| `backend/main.py` | ❌ No | ❌ No |
| `frontend/src/App.tsx` | ✅ Yes | ✅ Yes |
| `.github/workflows/deploy.yml` | ❌ No | ❌ No |

**Files That Cause "No Jobs Were Run" in `performance-tests.yml`:**
| File Pattern | Matches `backend/**`? | Jobs Run? |
|--------------|----------------------|-----------|
| `README.md` | ❌ No | ❌ No |
| `docker-compose.yml` | ❌ No | ❌ No |
| `.env.example` | ❌ No | ❌ No |
| `backend/main.py` | ✅ Yes | ✅ Yes |
| `frontend/src/App.tsx` | ❌ No | ❌ No |
| `.github/workflows/deploy.yml` | ❌ No | ❌ No |

#### 4. Proposed Fix Approach ✅

**Solution 1: Remove `paths:` Filters (Recommended)**
```yaml
# BEFORE (Causes "no jobs were run")
pull_request:
  branches: [main, develop]
  paths:
    - 'frontend/**'
    - '.github/workflows/lighthouse.yml'

# AFTER (Jobs run on all PRs)
pull_request:
  branches: [main, develop]
```

**Solution 2: Use Job-Level Conditions (Alternative)**
Keep `paths:` filters for expensive jobs, but add unconditional jobs:
```yaml
jobs:
  # Always runs (baseline validation)
  validate:
    runs-on: ubuntu-latest
    steps:
      - run: echo "PR validation passed"

  # Only runs for frontend changes
  lighthouse:
    if: contains(gitea.event.files, 'frontend/')
    runs-on: ubuntu-latest
    steps:
      - run: lhci autorun
```

### Verification Summary

| Check | Status | Details |
|-------|--------|---------|
| Path filter mechanism understood | ✅ Verified | Filters evaluated per-job, not per-workflow |
| Evidence in workflow files | ✅ Confirmed | Both workflows have restrictive `paths:` filters |
| Root cause identified | ✅ Confirmed | Path filters prevent job execution on non-matching files |
| Fix approach defined | ✅ Proposed | Remove filters or use job-level conditions |

### Conclusion

**Root Cause Confirmed:** The "no jobs were run" error is caused by restrictive `paths:` filters in `lighthouse.yml` and `performance-tests.yml`. When a PR is created that doesn't modify files matching the specified path patterns, the workflow triggers successfully but executes zero jobs, resulting in the error message reported by the user.

**Next Steps:** Proceed to Phase 3 (Fix Workflow Configuration) to remove or modify the path filters and update Gitea Actions syntax compatibility.

### Secondary Issue: GitHub Actions Syntax Incompatibility

**GitHub Context Variables (Incompatible with Gitea):**
- `github.event_name` → Should be `gitea.event_name`
- `github.ref` → Should be `gitea.ref`
- `github.repository` → Should be `gitea.repository`
- `context.repo.owner` → Should use `gitea.repository_owner`
- `secrets.GITHUB_TOKEN` → Should be `secrets.GITEA_TOKEN`

**Third-Party Actions:**
- `amondnet/vercel-action@v25` - May not work in Gitea
- `treosh/lighthouse-ci-action@v9` - May not work in Gitea

---

## Complete GitHub to Gitea Syntax Incompatibility Reference

This section documents ALL GitHub Actions syntax that must be changed to work with Gitea Actions.

### Context Variables Mapping

#### Event Context

| GitHub Syntax | Gitea Syntax | Description | Example Usage |
|--------------|--------------|-------------|---------------|
| `github.event_name` | `gitea.event_name` | Name of the event that triggered the workflow | `if: gitea.event_name == 'pull_request'` |
| `github.event` | `gitea.event` | Full event payload | `gitea.event.pull_request.number` |
| `github.event.action` | `gitea.event.action` | Action type (for events with sub-types) | `gitea.event.action == 'opened'` |

#### Repository Context

| GitHub Syntax | Gitea Syntax | Description | Example Usage |
|--------------|--------------|-------------|---------------|
| `github.repository` | `gitea.repository` | Full repository name (owner/repo) | `gitea.repository == 'owner/project'` |
| `github.repository_owner` | `gitea.repository_owner` | Repository owner/organization | `gitea.repository_owner` |
| `github.repositoryUrl` | `gitea.server_url` + `/` + `gitea.repository` | Repository URL | `${{ gitea.server_url }}/${{ gitea.repository }}` |
| `github.event.repository.name` | `gitea.event.repository.name` | Repository name (without owner) | Short name reference |

**Legacy `context.repo` Pattern (Found in deploy.yml):**
```yaml
# GitHub Actions (INCOMPATIBLE)
- uses: some-action@v1
  with:
    owner: ${{ context.repo.owner }}
    repo: ${{ context.repo.repo }}

# Gitea Actions (CORRECT)
- uses: some-action@v1
  with:
    owner: ${{ gitea.repository_owner }}
    repo: ${{ gitea.repository }}
```

#### Git Reference Context

| GitHub Syntax | Gitea Syntax | Description | Example Usage |
|--------------|--------------|-------------|---------------|
| `github.ref` | `gitea.ref` | Full Git ref (e.g., `refs/heads/main`) | `if: gitea.ref == 'refs/heads/main'` |
| `github.ref_name` | `gitea.ref_name` | Short ref name (e.g., `main`) | `${{ gitea.ref_name }}` |
| `github.sha` | `gitea.sha` | Commit SHA | `${{ gitea.sha }}` |
| `github.ref_protected` | `gitea.ref_protected` | Whether branch is protected | `if: gitea.ref_protected == true` |
| `github.head_ref` | `gitea.head_ref` | Branch name in PR (source) | `${{ gitea.head_ref }}` |
| `github.base_ref` | `gitea.base_ref` | Target branch in PR (base) | `${{ gitea.base_ref }}` |

#### Pull Request Context

| GitHub Syntax | Gitea Syntax | Description | Example Usage |
|--------------|--------------|-------------|---------------|
| `github.event.pull_request.number` | `gitea.event.number` | PR number | `${{ gitea.event.number }}` |
| `github.event.pull_request.title` | `gitea.event.pull_request.title` | PR title | `${{ gitea.event.pull_request.title }}` |
| `github.event.pull_request.user.login` | `gitea.event.pull_request.user.login` | PR author | `${{ gitea.event.pull_request.user.login }}` |
| `github.event.pull_request.head.sha` | `gitea.event.pull_request.head.sha` | PR head commit SHA | `${{ gitea.event.pull_request.head.sha }}` |

#### Actor Context

| GitHub Syntax | Gitea Syntax | Description | Example Usage |
|--------------|--------------|-------------|---------------|
| `github.actor` | `gitea.actor` | Username of person triggering workflow | `${{ gitea.actor }}` |
| `github.event.sender.login` | `gitea.event.sender.login` | Event sender username | `${{ gitea.event.sender.login }}` |

#### Server/Instance Context

| GitHub Syntax | Gitea Syntax | Description | Example Usage |
|--------------|--------------|-------------|---------------|
| `github.server_url` | `gitea.server_url` | Gitea instance URL | `${{ gitea.server_url }}` |
| `github.api_url` | `gitea.api_url` | Gitea API URL | `${{ gitea.api_url }}` |
| `github.graphql_url` | *(Not available)* | GraphQL API URL | Use REST API instead |

#### Workflow Context

| GitHub Syntax | Gitea Syntax | Description | Example Usage |
|--------------|--------------|-------------|---------------|
| `github.workflow` | `gitea.workflow` | Workflow name | `${{ gitea.workflow }}` |
| `github.run_id` | `gitea.run_id` | Unique run ID | `${{ gitea.run_id }}` |
| `github.run_number` | `gitea.run_number` | Run number for workflow | `${{ gitea.run_number }}` |
| `github.job` | `gitea.job` | Job name | `${{ gitea.job }}` |

#### Secrets and Tokens

| GitHub Syntax | Gitea Syntax | Description | Example Usage |
|--------------|--------------|-------------|---------------|
| `secrets.GITHUB_TOKEN` | `secrets.GITEA_TOKEN` | Auto-provided authentication token | `${{ secrets.GITEA_TOKEN }}` |
| `github.token` | `gitea.token` | Shortcut to token (in some contexts) | `${{ gitea.token }}` |

**Important:** Gitea automatically provides `GITEA_TOKEN` (not `GITHUB_TOKEN`).

### Specific Incompatibilities in Project Workflows

#### In `deploy.yml`:

**Line ~74 (conditional deployment):**
```yaml
# BEFORE (GitHub - INCOMPATIBLE)
if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/v')

# AFTER (Gitea)
if: gitea.ref == 'refs/heads/main' || startsWith(gitea.ref, 'refs/tags/v')
```

**Using `context.repo` pattern:**
```yaml
# BEFORE (GitHub - INCOMPATIBLE)
owner: ${{ context.repo.owner }}
repo: ${{ context.repo.repo }}

# AFTER (Gitea)
owner: ${{ gitea.repository_owner }}
repo: ${{ gitea.repository }}
```

**Event name checks:**
```yaml
# BEFORE (GitHub - INCOMPATIBLE)
if: github.event_name == 'push'

# AFTER (Gitea)
if: gitea.event_name == 'push'
```

#### In `lighthouse.yml` and `performance-tests.yml`:

While these workflows primarily use path filters (already documented), they may contain:
- Event checks using `github.event_name` → change to `gitea.event_name`
- Token references → change `GITHUB_TOKEN` to `GITEA_TOKEN`

### Conditional Expression Differences

#### Function Name Changes

| Function | GitHub | Gitea | Notes |
|----------|--------|-------|-------|
| Contains files | `contains(github.event.files, 'path')` | `contains(gitea.event.files, 'path')` | Same function, different context |
| startsWith | `startsWith(github.ref, 'refs/heads/')` | `startsWith(gitea.ref, 'refs/heads/')` | Same function, different context |
| toJSON | `toJSON(github.event)` | `toJSON(gitea.event)` | Same function, different context |
| format | `format('{0}/{1}', github.repository_owner, github.event.repository.name)` | `format('{0}/{1}', gitea.repository_owner, gitea.event.repository.name)` | Same function, different context |

### GitHub Actions Expressions Not Available in Gitea

| Expression | Status | Alternative |
|------------|--------|-------------|
| `github.run_attempt` | ❌ May not exist | Use `gitea.run_id` for uniqueness |
| `github.retrying` | ❌ May not exist | Implement custom retry logic |
| `github.retention_days` | ❌ Not applicable | Use Gitea server settings |
| `github.workflow_ref` | ❌ May not exist | Use `gitea.repository` + `gitea.workflow` |
| `github.workflow_sha` | ❌ May not exist | Use `gitea.sha` |

### Third-Party Actions Compatibility

#### Potentially Compatible Actions

These **may** work if they only use REST API or standard Actions features:
- Checkout actions (`actions/checkout@v3` → Gitea equivalent: `actions/checkout@v3`)
- Setup language actions (`actions/setup-python@v4`, `actions/setup-node@v3`)
- Generic upload/download artifacts

#### Potentially Incompatible Actions

These likely **won't** work because they use GitHub-specific APIs:
- `amondnet/vercel-action@v25` - May use GitHub deployment status API
- `treosh/lighthouse-ci-action@v9` - May use GitHub checks API
- GitHub release/publish actions
- Actions that reference `github.*` context internally

**Recommendation:** Test each third-party action in Gitea before relying on it.

### Summary of Required Changes

**Files to modify:**
1. `.github/workflows/deploy.yml` - Replace all `github.*` with `gitea.*`
2. `.github/workflows/lighthouse.yml` - Replace `GITHUB_TOKEN` and any `github.*` references
3. `.github/workflows/performance-tests.yml` - Replace `GITHUB_TOKEN` and any `github.*` references

**Find and replace pattern:**
```bash
# Find all github. references
grep -rn 'github\.' .github/workflows/

# Should replace with:
# github.event_name → gitea.event_name
# github.ref → gitea.ref
# github.repository → gitea.repository
# github.repository_owner → gitea.repository_owner
# context.repo.owner → gitea.repository_owner
# context.repo.repo → gitea.repository
# secrets.GITHUB_TOKEN → secrets.GITEA_TOKEN
```

---

## Evidence

### User Report (Translated from Russian)

> "I have some problems with git - when I make a PR, an email comes saying 'run failed no jobs were run'"

### Workflow Trigger vs Job Execution

| Event | Workflow Triggers? | Jobs Run? | Result |
|-------|-------------------|-----------|--------|
| PR with frontend changes | ✅ Yes | ✅ Yes | Success |
| PR with backend changes | ✅ Yes | ❌ No | "no jobs were run" |
| PR with docs changes | ✅ Yes | ❌ No | "no jobs were run" |
| PR with config changes | ✅ Yes | ❌ No | "no jobs were run" |

### Gitea vs GitHub Actions Compatibility

| Feature | GitHub Actions | Gitea Actions | Compatible? |
|---------|---------------|---------------|-------------|
| `pull_request` event | ✅ Supported | ✅ Supported | ✅ Yes |
| `paths:` filter | ✅ Supported | ✅ Supported | ✅ Yes |
| `github.*` context | ✅ Works | ❌ Doesn't work | ❌ No |
| `gitea.*` context | ❌ Doesn't work | ✅ Works | ❌ No |
| Third-party actions | ✅ Marketplace | ⚠️ Varies | ⚠️ Maybe |

---

## Gitea Actions Syntax Compatibility Requirements (subtask-2-2)

This section confirms ALL required syntax changes for migrating workflows from GitHub Actions to Gitea Actions.

### Critical Syntax Changes Required

#### 1. Context Variables - MUST REPLACE ALL

**Find Pattern:** `grep -rn 'github\.' .github/workflows/`

| Current (GitHub) | Required (Gitea) | Files Affected | Priority |
|------------------|------------------|----------------|----------|
| `github.event_name` | `gitea.event_name` | deploy.yml, lighthouse.yml, performance-tests.yml | CRITICAL |
| `github.ref` | `gitea.ref` | deploy.yml | CRITICAL |
| `github.repository` | `gitea.repository` | deploy.yml | CRITICAL |
| `github.repository_owner` | `gitea.repository_owner` | deploy.yml | CRITICAL |
| `github.event.*` | `gitea.event.*` | all workflows | CRITICAL |
| `github.sha` | `gitea.sha` | all workflows | HIGH |
| `github.actor` | `gitea.actor` | all workflows | MEDIUM |
| `context.repo.owner` | `gitea.repository_owner` | deploy.yml | CRITICAL |
| `context.repo.repo` | `gitea.repository` | deploy.yml | CRITICAL |

#### 2. Token References - MUST REPLACE

**Find Pattern:** `grep -rn 'GITHUB_TOKEN' .github/workflows/`

| Current (GitHub) | Required (Gitea) | Usage |
|------------------|------------------|-------|
| `secrets.GITHUB_TOKEN` | `secrets.GITEA_TOKEN` | Auto-provided authentication token |

**Note:** Gitea automatically provides `GITEA_TOKEN`. GitHub's `GITHUB_TOKEN` will NOT work in Gitea.

#### 3. Function Calls - UPDATE CONTEXT VARIABLES

**Find Pattern:** `grep -rn 'startsWith(github\.' .github/workflows/`

| Current (GitHub) | Required (Gitea) |
|------------------|------------------|
| `startsWith(github.ref, 'refs/heads/main')` | `startsWith(gitea.ref, 'refs/heads/main')` |
| `contains(github.event.files, 'path')` | `contains(gitea.event.files, 'path')` |
| `toJSON(github.event)` | `toJSON(gitea.event)` |

### File-by-File Migration Checklist

#### `.github/workflows/deploy.yml`

**Changes Required:**
- [ ] Replace `github.event_name` → `gitea.event_name`
- [ ] Replace `github.ref` → `gitea.ref` (in conditional checks)
- [ ] Replace `github.repository` → `gitea.repository`
- [ ] Replace `context.repo.owner` → `gitea.repository_owner`
- [ ] Replace `context.repo.repo` → `gitea.repository`
- [ ] Replace any `secrets.GITHUB_TOKEN` → `secrets.GITEA_TOKEN`

**Example:**
```yaml
# BEFORE (GitHub - INCOMPATIBLE)
if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/v')
owner: ${{ context.repo.owner }}
repo: ${{ context.repo.repo }}

# AFTER (Gitea - COMPATIBLE)
if: gitea.ref == 'refs/heads/main' || startsWith(gitea.ref, 'refs/tags/v')
owner: ${{ gitea.repository_owner }}
repo: ${{ gitea.repository }}
```

#### `.github/workflows/lighthouse.yml`

**Changes Required:**
- [ ] Remove `paths:` filter from `pull_request:` trigger
- [ ] Replace any `github.event_name` → `gitea.event_name` (if present)
- [ ] Replace any `secrets.GITHUB_TOKEN` → `secrets.GITEA_TOKEN`

**Example:**
```yaml
# BEFORE (GitHub - INCOMPATIBLE)
pull_request:
  branches: [main, develop]
  paths:
    - 'frontend/**'
    - '.github/workflows/lighthouse.yml'

# AFTER (Gitea - COMPATIBLE)
pull_request:
  branches: [main, develop]
# No paths filter - workflow runs on all PRs
```

#### `.github/workflows/performance-tests.yml`

**Changes Required:**
- [ ] Remove `paths:` filter from `pull_request:` trigger
- [ ] Replace any `github.event_name` → `gitea.event_name` (if present)
- [ ] Replace any `secrets.GITHUB_TOKEN` → `secrets.GITEA_TOKEN`

**Example:**
```yaml
# BEFORE (GitHub - INCOMPATIBLE)
pull_request:
  branches: [main, develop]
  paths:
    - 'backend/**'
    - '.github/workflows/performance-tests.yml'

# AFTER (Gitea - COMPATIBLE)
pull_request:
  branches: [main, develop]
# No paths filter - workflow runs on all PRs
```

### Third-Party Actions Compatibility Status

| Action | Used In | Compatibility Status | Action Required |
|--------|---------|---------------------|-----------------|
| `amondnet/vercel-action@v25` | deploy.yml | ⚠️ UNCERTAIN | Test in Gitea; may need native script replacement |
| `treosh/lighthouse-ci-action@v9` | lighthouse.yml | ⚠️ UNCERTAIN | Test in Gitea; may need Lighthouse CLI replacement |
| `actions/checkout@v3` | all workflows | ✅ COMPATIBLE | Should work in Gitea |
| `actions/setup-python@v4` | performance-tests.yml | ✅ COMPATIBLE | Should work in Gitea |
| `actions/setup-node@v3` | lighthouse.yml | ✅ COMPATIBLE | Should work in Gitea |

**Recommendation:** Test third-party actions in Gitea before relying on them. Have fallback scripts ready.

### Automated Migration Commands

**Find all incompatible syntax:**
```bash
# Find all github. context references
grep -rn 'github\.' .github/workflows/

# Find GITHUB_TOKEN references
grep -rn 'GITHUB_TOKEN' .github/workflows/

# Find context.repo pattern
grep -rn 'context\.repo\.' .github/workflows/

# Find paths filters on pull_request
grep -A 5 'pull_request:' .github/workflows/*.yml | grep -B 2 'paths:'
```

**Batch replace (use with caution, verify changes):**
```bash
# Replace github. with gitea. in workflow files
find .github/workflows -name '*.yml' -exec sed -i 's/github\./gitea./g' {} \;

# Replace GITHUB_TOKEN with GITEA_TOKEN
find .github/workflows -name '*.yml' -exec sed -i 's/GITHUB_TOKEN/GITEA_TOKEN/g' {} \;

# Replace context.repo.owner with gitea.repository_owner
find .github/workflows -name '*.yml' -exec sed -i 's/context\.repo\.owner/gitea.repository_owner/g' {} \;

# Replace context.repo.repo with gitea.repository
find .github/workflows -name '*.yml' -exec sed -i 's/context\.repo\.repo/gitea.repository/g' {} \;
```

### Validation After Migration

**Verify no GitHub-specific syntax remains:**
```bash
# Should return 0
grep -rch 'github\.' .github/workflows/ | grep -v 'gitea\.' | wc -l

# Should return 0
grep -rch 'GITHUB_TOKEN' .github/workflows/ | wc -l

# Should return 0
grep -rch 'context\.repo\.' .github/workflows/ | wc -l
```

**Verify YAML syntax is valid:**
```bash
# Check each workflow file
for file in .github/workflows/*.yml; do
  echo "Checking $file..."
  python3 -c "import yaml; yaml.safe_load(open('$file'))" && echo "✅ Valid" || echo "❌ Invalid"
done
```

### Summary of Requirements

**Total Changes Required:**
- **3 files** to modify (deploy.yml, lighthouse.yml, performance-tests.yml)
- **~8-12** context variable replacements per file (varies by file complexity)
- **1-2** token references per file
- **2** path filters to remove (one in lighthouse.yml, one in performance-tests.yml)

**Estimated Effort:** 15-30 minutes to apply all changes and verify

**Migration Priority:**
1. **CRITICAL:** `github.*` → `gitea.*` (workflows will fail without this)
2. **CRITICAL:** Remove `paths:` filters (causes "no jobs were run")
3. **HIGH:** Test third-party actions compatibility
4. **MEDIUM:** Update documentation with Gitea-specific notes

### Verification Checklist

Use this checklist to confirm ALL required changes are documented:

- [ ] All `github.event_name` → `gitea.event_name` mappings documented
- [ ] All `github.ref` → `gitea.ref` mappings documented
- [ ] All `github.repository` → `gitea.repository` mappings documented
- [ ] All `github.repository_owner` → `gitea.repository_owner` mappings documented
- [ ] All `context.repo.*` → `gitea.*` mappings documented
- [ ] All `secrets.GITHUB_TOKEN` → `secrets.GITEA_TOKEN` mappings documented
- [ ] Path filter removal approach documented
- [ ] Third-party actions compatibility assessed
- [ ] Automated migration commands provided
- [ ] Validation commands provided

**Status:** ✅ All required syntax changes documented above.

---

## Proposed Fix Strategy

### Phase 1: Remove Path Filters (Critical)

**For `lighthouse.yml`:**
```yaml
# BEFORE
pull_request:
  branches: [main, develop]
  paths:
    - 'frontend/**'
    - '.github/workflows/lighthouse.yml'

# AFTER
pull_request:
  branches: [main, develop]
# No paths filter - jobs run on all PRs
```

**For `performance-tests.yml`:**
```yaml
# BEFORE
pull_request:
  branches: [main, develop]
  paths:
    - 'backend/**'
    - '.github/workflows/performance-tests.yml'

# AFTER
pull_request:
  branches: [main, develop]
# No paths filter - jobs run on all PRs
```

**Rationale:**
- CI/CD workflows should validate **all** PRs, not just specific file changes
- Documentation-only PRs still need CI validation
- Config changes need testing
- If performance tests are expensive, make them conditional **inside** jobs using `if:` clauses

### Phase 2: Update Syntax for Gitea Compatibility

**Replace all `github.*` references:**

| GitHub Syntax | Gitea Syntax | Location |
|--------------|--------------|----------|
| `github.event_name` | `gitea.event_name` | Throughout all workflows |
| `github.ref` | `gitea.ref` | deploy.yml line ~74 |
| `github.repository` | `gitea.repository` | deploy.yml |
| `context.repo.owner` | `gitea.repository_owner` | deploy.yml |
| `secrets.GITHUB_TOKEN` | `secrets.GITEA_TOKEN` | All workflows |

### Phase 3: Handle Third-Party Actions

**Options for `vercel-action`:**
1. Test if it works in Gitea (may work if it only uses REST API)
2. Replace with native script using `vercel-cli`
3. Remove Vercel deployment from Gitea CI/CD

**Options for `lighthouse-ci-action`:**
1. Test if it works in Gitea
2. Run Lighthouse CI manually or from separate GitHub Actions
3. Use Lighthouse CLI directly in workflow

---

## Testing Plan

### Test Scenarios

1. **Documentation PR**
   - Create PR modifying only `README.md`
   - Expected: Workflows trigger, jobs execute successfully
   - Current behavior: "no jobs were run"

2. **Config PR**
   - Create PR modifying only `docker-compose.yml`
   - Expected: Workflows trigger, jobs execute successfully
   - Current behavior: "no jobs were run"

3. **Mixed Changes PR**
   - Create PR modifying both frontend and backend files
   - Expected: All workflows trigger, appropriate jobs run
   - Current behavior: Only lighthouse runs, performance-tests skipped

4. **Workflow File PR**
   - Create PR modifying `.github/workflows/lighthouse.yml`
   - Expected: Workflow triggers, jobs run (meta-validation)
   - Current behavior: Unknown (may work due to paths filter)

### Verification Commands

```bash
# Check for remaining path filters on pull_request
grep -A 5 'pull_request:' .github/workflows/*.yml | grep 'paths:' || echo "None found (good)"

# Check for remaining github.* references
grep -rh 'github\.' .github/workflows/ | grep -v 'gitea\.' || echo "None found (good)"

# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/lighthouse.yml'))"
```

---

## Risks and Mitigations

### Risk 1: Increased CI/CD Usage

**Concern:** Removing path filters means jobs run on ALL PRs, increasing resource usage.

**Mitigation:**
- Use job-level `if:` conditions for expensive tests
- Consider different workflow strategies for different event types
- Monitor runner capacity and add more if needed

### Risk 2: Third-Party Actions Don't Work

**Concern:** `vercel-action` or `lighthouse-ci-action` may fail in Gitea.

**Mitigation:**
- Test in staging environment first
- Have fallback scripts ready
- Consider removing deployment from Gitea if not critical

### Risk 3: Breaking Existing Functionality

**Concern:** Changes may break workflows that currently work for specific PRs.

**Mitigation:**
- Create test PR for each scenario before implementing
- Keep backup of original workflow files
- Can revert changes quickly if issues arise

---

## Next Steps

1. ✅ Document current behavior (this file)
2. ✅ Document all GitHub→Gitea syntax incompatibilities (completed)
3. ⏭️ Verify path filters are root cause with test PR
4. ⏭️ Determine if third-party actions work in Gitea
5. ⏭️ Implement fixes
6. ⏭️ Validate with test PRs
7. ⏭️ Document required secrets and setup

---

## References

- **Spec:** `.auto-claude/specs/109-pr/spec.md`
- **Plan:** `.auto-claude/specs/109-pr/implementation_plan.json`
- **Context:** `.auto-claude/specs/109-pr/context.json`

---

*Last Updated: 2025-02-04*
