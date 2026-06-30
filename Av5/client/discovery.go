package main

import (
	"context"
	"errors"
	"fmt"
	"log"
	"time"

	pb "av5client/gen"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

var seeds = []string{"node1:6001", "node2:6002", "node3:6003", "node4:6004"}

const maxAttempts = 12

type Cluster struct {
	known string
}

func (c *Cluster) dial(addr string) (pb.ClientServiceClient, *grpc.ClientConn, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	conn, err := grpc.DialContext(
		ctx,
		addr,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithBlock(),
	)
	if err != nil {
		return nil, nil, fmt.Errorf("falha ao conectar em %s: %w", addr, err)
	}
	return pb.NewClientServiceClient(conn), conn, nil
}

func (c *Cluster) candidates() []string {
	if c.known == "" {
		return seeds
	}
	out := []string{c.known}
	for _, s := range seeds {
		if s != c.known {
			out = append(out, s)
		}
	}
	return out
}

func (c *Cluster) Publish(key, value string) error {
	for attempt := 0; attempt < maxAttempts; attempt++ {
		addr := c.candidates()[attempt%len(c.candidates())]
		cli, conn, err := c.dial(addr)
		if err != nil {
			log.Printf("nodo %s indisponivel: %v", addr, err)
			continue
		}
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		reply, err := cli.Publish(ctx, &pb.PublishRequest{Key: key, Value: value})
		cancel()
		conn.Close()
		if err != nil {
			log.Printf("nodo %s indisponivel: %v", addr, err)
			c.known = ""
			continue
		}
		if reply.Success {
			log.Printf("OK publicado %s=%s (index=%d) via lider %s", key, value, reply.Index, addr)
			c.known = addr
			return nil
		}
		switch reply.Message {
		case "not_leader":
			if reply.LeaderHint != "" {
				log.Printf("%s nao e lider; redirecionando para %s", addr, reply.LeaderHint)
				c.known = reply.LeaderHint
			} else {
				log.Printf("%s nao conhece o lider ainda; aguardando eleicao...", addr)
				c.known = ""
				time.Sleep(1 * time.Second)
			}
		case "no_quorum":
			const maxNoQuorumRetries = 2
			for nqRetry := 0; nqRetry < maxNoQuorumRetries; nqRetry++ {
				log.Printf("sem quorum (tentativa %d/%d); aguardando quorum...", nqRetry+1, maxNoQuorumRetries)
				time.Sleep(2 * time.Second)
			}
			log.Printf("sem quorum apos espera; entrada pendente no lider %s", addr)
			return errors.New("pendente — sem quorum no momento; tente novamente mais tarde")
		}
	}
	return errors.New("nao foi possivel publicar (sem lider/quorum)")
}

func (c *Cluster) Consume(key string, addr string) (*pb.ConsumeReply, error) {
	candidates := c.candidates()
	if addr != "" {
		candidates = []string{addr}
	}
	var lastErr error
	for _, a := range candidates {
		cli, conn, err := c.dial(a)
		if err != nil {
			lastErr = err
			continue
		}
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		reply, err := cli.Consume(ctx, &pb.ConsumeRequest{Key: key})
		cancel()
		conn.Close()
		if err != nil {
			lastErr = err
			continue
		}
		return reply, nil
	}
	return nil, lastErr
}
