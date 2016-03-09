package main

import (
    "fmt"
    "encoding/json"
    "errors"
    "log"
    "net"
    "net/http"
    "os"
    "io/ioutil"

	"github.com/ClusterHQ/dvol/pkg/api"
)

const DVOL_SOCKET = "/run/docker/plugins/dvol.sock"
const DVOL_BASE_DIR = "/var/run/dvol"

type ResponseImplements struct {
    // A response to the Plugin.Activate request
    Implements []string
}

type RequestCreate struct {
    // A request to create a volume for Docker
    Name string
    Opts map[string]string
}

type RequestMount struct {
    // A request to mount a volume for Docker
    Name string
}

type ResponseSimple struct {
    // A response which only indicates if there was an error or not
    Err string
}

type ResponseMount struct {
    // A response to the VolumeDriver.Mount request
    Mountpoint string
    Err string
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
            Implements: []string{"VolumeDriver"},
        })
        w.Write(responseJSON)
    })

    http.HandleFunc("/VolumeDriver.Create", func(w http.ResponseWriter, r *http.Request) {
        log.Print("<= /VolumeDriver.Create")
        requestJSON, err := ioutil.ReadAll(r.Body)
        if err != nil {
            log.Fatalf("Unable to read response body %s", err)
        }
        request := new(RequestCreate)
        json.Unmarshal(requestJSON, request)
        name := request.Name
        dvol := api.NewDvolAPI(DVOL_BASE_DIR)
        if !dvol.VolumeExists(name) {
            // TODO error handling
            dvol.CreateVolume(name)
        }
        WriteResponseOK(w)
    })

    http.HandleFunc("/VolumeDriver.Remove", func(w http.ResponseWriter, r *http.Request) {
    })

    http.HandleFunc("/VolumeDriver.Path", func(w http.ResponseWriter, r *http.Request) {
    })

    http.HandleFunc("/VolumeDriver.Mount", func(w http.ResponseWriter, r *http.Request) {
        log.Print("<= /VolumeDriver.Mount")
        requestJSON, err := ioutil.ReadAll(r.Body)
        if err != nil {
            log.Fatalf("Unable to read response body %s", err)
        }
        request := new(RequestMount)
        json.Unmarshal(requestJSON, request)
        name := request.Name

        dvol := api.NewDvolAPI(DVOL_BASE_DIR)
        var mountpoint string

        if dvol.VolumeExists(name) {
            err := dvol.SwitchVolume(name)
            if err != nil {
                WriteResponseErr(err, w)
                return
            }
            mountpoint, err = dvol.ActiveVolume()
            if err != nil {
                WriteResponseErr(err, w)
                return
            }
        } else {
            WriteResponseErr(errors.New("Requested to mount unknown volume " + name), w)
            return
        }

        responseJSON, _ := json.Marshal(&ResponseMount{
            Mountpoint: mountpoint,
            Err: "",
        })
        w.Write(responseJSON)
    })

    http.HandleFunc("/VolumeDriver.Unmount", func(w http.ResponseWriter, r *http.Request) {
    })

    http.HandleFunc("/VolumeDriver.List", func(w http.ResponseWriter, r *http.Request) {
    })

    http.Serve(listener, nil)
}

func WriteResponseOK (w http.ResponseWriter) {
    // A shortcut to writing a ResponseOK to w
    responseJSON, _ := json.Marshal(&ResponseSimple{Err: ""})
    w.Write(responseJSON)
}

func WriteResponseErr (err error, w http.ResponseWriter) {
    // A shortcut to responding with an error, and then log the error
    errString := fmt.Sprintln(err)
    log.Printf("Error: %v", err)
    responseJSON, _ := json.Marshal(&ResponseSimple{Err: errString})
    w.Write(responseJSON)
}

