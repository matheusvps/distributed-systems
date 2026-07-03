#!/usr/bin/env bash
# Run unit tests without loading third-party pytest plugins (e.g. ROS launch_testing).
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
exec python -m pytest server/tests "$@"
