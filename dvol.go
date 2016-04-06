package main

import (
	"os"

	"github.com/ClusterHQ/dvol/pkg/cmd"
)

func main() {
	if err := cmd.RootCmd.Execute(); err != nil {
		os.Exit(-1)
	}
}
