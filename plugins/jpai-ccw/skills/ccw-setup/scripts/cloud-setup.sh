#!/usr/bin/env bash
# Machine-level setup for a Claude Code cloud session.
#
# Downloaded from a tagged release and run by cloud-setup-stub.sh, which is the
# environment's setup script. It runs once per cached snapshot, before Claude
# starts, and cannot read the environment's saved variables: every input below
# is exported by the stub. Per-session state belongs to the ccw-setup skill.
#
# Inputs (all optional):
#   CCW_RELEASE         tag this script was downloaded from, recorded for the version check
#   CCW_CACHE_BUST      date in the stub that forces a fresh snapshot, recorded likewise
#   CCW_AWS_REGION      region written to each AWS profile
#   CCW_ROLE_ARN        role the `ccw` profile assumes
#   CCW_ADMIN_ROLE_ARN  role the `ccw-admin` profile assumes (its external ID is per session)
#   CCW_PLUGINS         plugins to install, default "jpai-essentials jpai-ccw"
#   CCW_RELEASE_FILE    where the release is recorded, default /etc/ccw/release
set -euo pipefail

MARKETPLACE_URL="${CCW_MARKETPLACE_URL:-https://github.com/jpeakai/skills.git}"
MARKETPLACE="${CCW_MARKETPLACE:-jpeakai}"
PLUGINS="${CCW_PLUGINS:-jpai-essentials jpai-ccw}"
RELEASE_FILE="${CCW_RELEASE_FILE:-/etc/ccw/release}"

log() { printf 'cloud-setup: %s\n' "$*"; }

# A failed plugin install is logged, not fatal: the session still starts.
install_plugins() {
  claude plugin marketplace add "$MARKETPLACE_URL" || log "marketplace add failed, it may already exist"
  claude plugin marketplace update "$MARKETPLACE" || log "WARN: marketplace update failed"
  local plugin
  for plugin in $PLUGINS; do
    claude plugin install "$plugin@$MARKETPLACE" || log "WARN: install of $plugin failed"
  done
}

install_aws_cli() {
  if command -v aws >/dev/null 2>&1; then
    log "AWS CLI already installed"
    return
  fi
  local tmp
  tmp="$(mktemp -d)"
  curl -sSfo "$tmp/awscliv2.zip" "https://awscli.amazonaws.com/awscli-exe-linux-$(uname -m).zip"
  unzip -q -o "$tmp/awscliv2.zip" -d "$tmp"
  "$tmp/aws/install" --update
  rm -rf "$tmp"
}

configure_profile() {
  local profile="$1" role_arn="$2"
  [ -n "$role_arn" ] || return 0
  aws configure set "profile.$profile.role_arn" "$role_arn"
  aws configure set "profile.$profile.credential_source" Environment
  if [ -n "${CCW_AWS_REGION:-}" ]; then
    aws configure set "profile.$profile.region" "$CCW_AWS_REGION"
  fi
  log "configured AWS profile $profile"
}

record_release() {
  mkdir -p "$(dirname "$RELEASE_FILE")"
  printf 'CCW_RELEASE=%s\nCCW_CACHE_BUST=%s\n' "${CCW_RELEASE:-}" "${CCW_CACHE_BUST:-}" >"$RELEASE_FILE"
  log "recorded release ${CCW_RELEASE:-unknown} in $RELEASE_FILE"
}

install_plugins
install_aws_cli
configure_profile ccw "${CCW_ROLE_ARN:-}"
configure_profile ccw-admin "${CCW_ADMIN_ROLE_ARN:-}"
record_release
