#!/usr/bin/env bash
# Run unit tests without loading third-party pytest plugins.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
exec python3 -m pytest server/tests "$@"
