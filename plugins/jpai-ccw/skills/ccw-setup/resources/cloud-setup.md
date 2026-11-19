# Cloud setup: events, environments and releases

## Who runs what, and when

| Event | Runs | Can do |
|---|---|---|
| Setup script | Once per cached snapshot, before Claude starts | Install tools and plugins, write machine-level files |
| Repositories cloned | Every session, after the snapshot | Nothing written into a checkout by the setup script survives |
| Session start or resume | Every session | Read saved variables, run this skill |

- **The setup script works like an image layer.** Its result is cached and reused.
  It reruns only when the script or the network hosts change, or after the cache expires (about seven days).
- **The setup script cannot read saved variables.** Only the session sees them.
  So the stub exports every value the setup script needs.
- **Git identity defaults to the agent.** The global git config sets the agent as user and signer.
  This skill sets only the author, leaving the committer and its signature alone.

## The two scripts

- **`scripts/cloud-setup-stub.sh`:** the template pasted into an environment's setup script.
  It pins a release tag, exports the personal values, downloads `cloud-setup.sh` from that tag and runs it.
- **`scripts/cloud-setup.sh`:** installs the plugins and the AWS CLI, writes the AWS profiles, and records the release in `/etc/ccw/release`.
  A failed plugin install is logged, not fatal.

## Two environments

Each environment carries its own copy of the stub.
They differ only in the values they export and save.

| Value | Where | Developer | Admin |
|---|---|---|---|
| `CCW_RELEASE`, `CCW_CACHE_BUST` | Stub | Yes | Yes |
| `CCW_AWS_REGION` | Stub or saved variable | Yes | Yes |
| `CCW_ROLE_ARN` | Stub or saved variable | Yes | Optional |
| `CCW_ADMIN_ROLE_ARN` | Stub or saved variable | No | Yes |
| `CCW_ADMIN_EXTERNAL_ID` | Saved variable only | No | Yes |
| `CCW_GIT_AUTHOR_NAME`, `CCW_GIT_AUTHOR_EMAIL` | Saved variable | Optional | Optional |

- **The external ID is never in the stub.** The setup script is stored in plain text, and it cannot read the saved variable anyway.
  The `aws-profiles` check writes it into the admin profile each session.
- **A value in both places converges.** The setup script writes it at snapshot time, and the session check corrects it from the saved variable.

## Releases

A release of the setup script is a tag named `ccw/vX.Y.Z`, where `X.Y.Z` is the `jpai-ccw` plugin version at that commit.
The namespace keeps setup-script releases apart from other tags.

- **Download from a tag, never a branch.** A branch URL on the raw content host is cached for minutes, so it can serve a stale script.
  Tags are immutable.
- **Use the `refs/tags/` URL form.** It avoids ambiguity with the slash in the tag name:
  `https://raw.githubusercontent.com/<owner>/<repo>/refs/tags/ccw/vX.Y.Z/skills/ccw-setup/scripts/cloud-setup.sh`

### Cutting a release

1. Merge the change, with the `jpai-ccw` version bumped in its three manifests.
2. Tag the merge commit `ccw/v<version>` and push the tag.
3. In each environment's setup script, set `CCW_RELEASE` to the new tag.

### A plugin-only release

When a plugin changed but the setup script did not, no new tag is needed.
Change `CCW_CACHE_BUST` in each environment's setup script to today's date.
The changed script forces a fresh snapshot, which installs the latest plugins.
