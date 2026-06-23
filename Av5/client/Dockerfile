FROM golang:1.23-bookworm AS build
RUN apt-get update && apt-get install -y --no-install-recommends protobuf-compiler && \
    rm -rf /var/lib/apt/lists/*
RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.35.1 && \
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.5.1
ENV PATH="/go/bin:${PATH}"

WORKDIR /src
COPY client/go.mod ./client/go.mod
WORKDIR /src/client
RUN go mod download || true

COPY proto /src/proto
COPY client /src/client

# generate Go stubs into ./gen with package raftpb, import path av5client/gen
RUN mkdir -p gen && \
    protoc -I /src/proto \
      --go_out=gen --go_opt=paths=source_relative,Mraft.proto=av5client/gen \
      --go-grpc_out=gen --go-grpc_opt=paths=source_relative,Mraft.proto=av5client/gen \
      /src/proto/raft.proto
RUN go mod tidy && go build -o /client .

FROM debian:bookworm-slim
COPY --from=build /client /client
ENTRYPOINT ["/client"]
