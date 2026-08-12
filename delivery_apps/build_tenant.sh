#!/usr/bin/env bash
# Build a tenant web build from shared source + tenant config/assets.
# Usage: build_tenant.sh <tenant_id> <deploy_dir>
#   <tenant_id>   e.g. dona_soco | tortas_las_originales
#   <deploy_dir>  repo-relative destination, e.g. delivery_apps/dona_soco_app/app
set -euo pipefail

TENANT_ID="${1:?tenant id required}"
DEPLOY_DIR="${2:?deploy dir required}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TENANT_DIR="$SCRIPT_DIR/tenants/$TENANT_ID"
SHARED_SRC="$SCRIPT_DIR/app/src"

# Staging area: prefer RUNNER_TEMP on GitHub Actions, else a tmp dir
TMP_BASE="${RUNNER_TEMP:-$(mktemp -d)}"
STAGE="$TMP_BASE/build_${TENANT_ID}"
rm -rf "$STAGE"
mkdir -p "$STAGE/src/assets"

rsync -a "$SHARED_SRC/" "$STAGE/src/"
cp "$TENANT_DIR/config.py" "$STAGE/src/config.py"
rsync -a "$TENANT_DIR/assets/" "$STAGE/src/assets/"
cp "$TENANT_DIR/pyproject.toml" "$STAGE/pyproject.toml"
if [ -f "$REPO_ROOT/$DEPLOY_DIR/README.md" ]; then
    cp "$REPO_ROOT/$DEPLOY_DIR/README.md" "$STAGE/README.md"
fi

cd "$STAGE"
export CI=true
export FLET_TEMPLATE_REF=0.82.0
flet build web -vv

rm -rf "$REPO_ROOT/$DEPLOY_DIR/build/web"
mkdir -p "$REPO_ROOT/$DEPLOY_DIR/build"
cp -r "$STAGE/build/web" "$REPO_ROOT/$DEPLOY_DIR/build/web"
echo "build_tenant: $TENANT_ID -> $DEPLOY_DIR/build/web"
