package main

import (
	"fmt"
	"os"

	"github.com/ClusterHQ/dvol/cmd"
	//    "github.com/ClusterHQ/dvol/dockercontainers"
	//    "github.com/ClusterHQ/dvol/plugin"
)

func main() {
	if err := cmd.RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(-1)
	}
}
