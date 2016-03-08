package main

import (
    "encoding/json"
    "log"
    "net"
    "net/http"
    "os"
)

const DVOL_SOCKET = "/run/docker/plugins/dvol.sock"

type ResponseImplements struct {
    Implements string
}

func main () {
    if _, err := os.Stat(DVOL_SOCKET); err == nil {
        if err = os.Remove(DVOL_SOCKET); err == nil {
            log.Fatalf("Could not clean up existing socket at %s", DVOL_SOCKET)
        }
    }
    listener, err := net.Listen("unix", DVOL_SOCKET)
    if err != nil {
        log.Fatalf("Could not listen on %s", DVOL_SOCKET)
    }

    http.HandleFunc("/Plugin.Activate", func(w http.ResponseWriter, r *http.Request) {
        log.Print("<= /Plugin.Activate")
        responseJSON, _ := json.Marshal(&ResponseImplements{
            Implements: "VolumeDriver",
        })
        w.Write(responseJSON)
    })

    http.HandleFunc("/VolumeDriver.Create", func(w http.ResponseWriter, r *http.Request) {
    })

    http.HandleFunc("/VolumeDriver.Remove", func(w http.ResponseWriter, r *http.Request) {
    })

    http.HandleFunc("/VolumeDriver.Path", func(w http.ResponseWriter, r *http.Request) {
    })

    http.HandleFunc("/VolumeDriver.Mount", func(w http.ResponseWriter, r *http.Request) {
    })

    http.HandleFunc("/VolumeDriver.Unmount", func(w http.ResponseWriter, r *http.Request) {
    })

    http.Serve(listener, nil)
}
