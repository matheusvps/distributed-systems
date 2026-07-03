package main

import (
	"fmt"
	"log"
	"os"
	"strings"
)

func usage() {
	fmt.Println("uso:")
	fmt.Println("  client publish <key> <value>")
	fmt.Println("  client consume [key] [--node nodeX:600X]")
	fmt.Println("  client interactive")
}

func doConsume(c *Cluster, key, node string) {
	reply, err := c.Consume(key, node)
	if err != nil {
		log.Printf("erro ao consumir: %v", err)
		return
	}
	src := "replica"
	if reply.IsLeader {
		src = "lider"
	}
	fmt.Printf("[%s] committed_index=%d pending(uncommitted)=%d (replicadas=%d, so_lider=%d)\n",
		src, reply.CommittedIndex, reply.PendingCount,
		reply.PendingReplicatedCount, reply.PendingLeaderOnlyCount)
	if len(reply.Items) == 0 {
		fmt.Println("  (sem dados efetivados)")
	}
	for _, it := range reply.Items {
		fmt.Printf("  %s = %s (index=%d)\n", it.Key, it.Value, it.Index)
	}
}

func main() {
	if len(os.Args) < 2 {
		usage()
		return
	}
	c := &Cluster{}
	switch os.Args[1] {
	case "publish":
		if len(os.Args) != 4 {
			usage()
			return
		}
		if err := c.Publish(os.Args[2], os.Args[3]); err != nil {
			log.Fatalf("falha: %v", err)
		}
	case "consume":
		key := ""
		node := ""
		rest := os.Args[2:]
		for i := 0; i < len(rest); i++ {
			if rest[i] == "--node" && i+1 < len(rest) {
				node = rest[i+1]
				i++
			} else {
				key = rest[i]
			}
		}
		doConsume(c, key, node)
	case "interactive":
		interactive(c)
	default:
		usage()
	}
}

func interactive(c *Cluster) {
	fmt.Println("Cliente Raft (gRPC). Comandos: publish <k> <v> | consume [k] | sair")
	var line string
	for {
		fmt.Print("> ")
		if _, err := fmt.Scanln(&line); err != nil {
			return
		}
		_ = strings.TrimSpace(line)
		fmt.Println("use os subcomandos da CLI: publish/consume")
		return
	}
}
