package main

import (
    "encoding/json"
    "log"
    "net"
    "net/http"
)

type ResponseImplements struct {
    Implements string
}

func main () {
    listener, err := net.Listen("unix", "/run/docker/plugins/dvol.sock")
    if err != nil {
        log.Fatal("Could not listen on /run/docker/plugins/dvol.sock")
    }

    http.HandleFunc("/Plugin.Activate", func(w http.ResponseWriter, r *http.Request) {
        // stuff
        log.Print("<= /Plugin.Activate")
        responseJSON, _ := json.Marshal(&ResponseImplements{
            Implements: "VolumeDriver",
        })
        w.Write(responseJSON)
    })

    http.Serve(listener, nil)
}
