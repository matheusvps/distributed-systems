#!/usr/bin/env bash
# Regenerate Python gRPC stubs locally (Go stubs are generated at Docker build).
# Requires: a Python venv with grpcio-tools installed (see server/requirements.txt).
set -euo pipefail
cd "$(dirname "$0")/.."

python -m grpc_tools.protoc \
  -I proto \
  --python_out=server/gen \
  --grpc_python_out=server/gen \
  proto/raft.proto

# grpc_python_out emits `import raft_pb2` (no package). Make it package-relative.
sed -i 's/^import raft_pb2/from . import raft_pb2/' server/gen/raft_pb2_grpc.py
echo "Python stubs generated in server/gen/"
