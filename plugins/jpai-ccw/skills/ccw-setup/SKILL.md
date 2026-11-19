---
name: ccw-setup
description: "Check and apply a Claude Code cloud session's per-session setup, then report what changed. Covers the git commit author, the session's AWS profiles (including an admin profile's external ID from a saved variable), and whether the installed plugins and the environment's pinned setup-script release lag the latest release. Safe to rerun: a session already in order changes nothing. Use at the start of a cloud session, after a resume, when AWS profiles fail to assume a role, when commits carry the wrong author, or when asked to check or update the cloud environment's setup script. Skip on a local machine, and for changing the environment itself: that is the user's approval."
argument-hint: "[check | fix] [git-identity | aws-profiles | versions]"
user-invocable: true
---

# ccw-setup

The environment's setup script runs once per cached snapshot and cannot read the environment's saved variables.
This skill applies what only a running session can.
See [resources/cloud-setup.md](resources/cloud-setup.md) for the event model, the two environments and the release steps.

## Run

Default to `fix`, unless the user asked only to check.

```sh
uv run --no-project <skill>/scripts/ccw_check.py [check ...] [--fix] [--json]
```

- **Checks:** `git-identity`, `aws-profiles` and `versions`. Name none to run all three.
- **Exit 0:** nothing is in drift. Exit 1: something is. Exit 2: a usage error.
- **Statuses:** `ok`, `fixed`, `drift` and `skip`. Report each `fixed` and `drift` row, then summarise the `skip` rows in one line.

## What each check means

| Check | Applies | Source |
|---|---|---|
| `git-identity` | Global `author.name` and `author.email` only | `CCW_GIT_AUTHOR_NAME`, then `CCW_GIT_AUTHOR_EMAIL` or `CLAUDE_CODE_USER_EMAIL` |
| `aws-profiles` | `role_arn`, `credential_source`, `region`, `external_id` | `CCW_ROLE_ARN`, `CCW_ADMIN_ROLE_ARN`, `CCW_ADMIN_EXTERNAL_ID`, `CCW_AWS_REGION` |
| `versions` | Never applies | Latest plugin manifests and `ccw/v*` tags, against the release the setup script recorded |

- **The committer is never changed.** It stays the session's signing identity, so commit signatures remain valid.
- **Secrets are never printed.** Results name the keys that changed, not their values.
- **A `skip` is not a failure.** It means that environment does not use that piece.

## After the run

1. When `aws-profiles` passes, confirm each configured profile assumes its role:
   `aws sts get-caller-identity --profile <profile>`.
   Report the role ARN, or the error, per profile.
2. When `versions` reports drift, do not edit the environment.
   Name the change its row gives: a new `CCW_RELEASE` tag, or a new `CCW_CACHE_BUST` date, in the environment's setup script.
   Ask the user to approve that environment change.
3. When a variable is missing, name it and say it belongs in the environment's saved variables.
