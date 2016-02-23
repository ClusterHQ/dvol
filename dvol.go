package main

import (
	"fmt"
	"github.com/ClusterHQ/dvol/cmd"
	"os"
	//    "github.com/clusterhq/dvol/dockercontainers"
	//    "github.com/clusterhq/dvol/plugin"
)

func main() {
	if err := cmd.RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(-1)
	}
}
