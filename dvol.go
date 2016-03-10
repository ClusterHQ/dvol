package main

import (
	"fmt"
	"os"

	"github.com/ClusterHQ/dvol/pkg/cmd"
	//	"github.com/nu7hatch/gouuid"
)

func main() {
	if err := cmd.RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(-1)
	}
	/*
		u4, err := uuid.NewV4()
		if err != nil {
			fmt.Println("error:", err)
			return
		}
		fmt.Println(u4)
	*/
}
