FROM python:3.12-slim
WORKDIR /app

COPY server/requirements.txt ./server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

COPY proto ./proto
COPY server ./server

# (re)generate Python stubs at build time
RUN python -m grpc_tools.protoc -I proto \
      --python_out=server/gen --grpc_python_out=server/gen proto/raft.proto && \
    sed -i 's/^import raft_pb2/from . import raft_pb2/' server/gen/raft_pb2_grpc.py

ENV PYTHONUNBUFFERED=1
ENV RAFT_DATA_DIR=/app/data
ENTRYPOINT ["python", "-m", "server.run_node"]
