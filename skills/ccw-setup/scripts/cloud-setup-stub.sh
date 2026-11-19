#!/usr/bin/env bash
# Template for a cloud environment's setup script. Paste it into the environment's
# settings and fill in the values. Personal values live here, never in the repository.
#
# The setup script cannot read the environment's saved variables, so this stub
# exports everything cloud-setup.sh needs, then runs it from a pinned release tag.
# Tags are immutable; a branch URL can serve a stale copy for several minutes.
set -euo pipefail

# Release of cloud-setup.sh to run. Bump it to take a new ccw/ release.
export CCW_RELEASE="ccw/v0.1.0"
# Change this date to rebuild the cached snapshot when only a plugin was released.
export CCW_CACHE_BUST="2026-01-01"

export CCW_AWS_REGION="us-east-1"
export CCW_ROLE_ARN="arn:aws:iam::111122223333:role/ExampleWorker"
# Admin environment only. Its external ID is a saved variable the session applies.
# export CCW_ADMIN_ROLE_ARN="arn:aws:iam::111122223333:role/ExampleWorkerAdmin"

url="https://raw.githubusercontent.com/jpeakai/skills/refs/tags/${CCW_RELEASE}/skills/ccw-setup/scripts/cloud-setup.sh"
script="$(mktemp)"
curl -fsSL "$url" -o "$script"
bash "$script"
rm -f "$script"
