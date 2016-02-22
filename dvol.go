package main

import (
    "fmt"
    "os"
    "github.com/clusterhq/dvol/cmd"
//    "github.com/clusterhq/dvol/dockercontainers"
//    "github.com/clusterhq/dvol/plugin"
)

func main() {
    if err := cmd.RootCmd.Execute(); err != nil {
        fmt.Println(err)
        os.Exit(-1)
    }
}
