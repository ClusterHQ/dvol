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

const PLUGINS_DIR = "/run/docker/plugins"
const DVOL_SOCKET = PLUGINS_DIR + "/dvol.sock"
const VOL_DIR = "/var/lib/dvol/volumes"
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

type RequestRemove struct {
    // A request to remove a volume for Docker
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
    if _, err := os.Stat(PLUGINS_DIR); err != nil {
        if err := os.MkdirAll(PLUGINS_DIR, 0700); err != nil {
            log.Fatalf("Could not make plugin directory %s: %v", PLUGINS_DIR, err)
        }
    }
    if _, err := os.Stat(DVOL_SOCKET); err == nil {
        if err = os.Remove(DVOL_SOCKET); err != nil {
            log.Fatalf("Could not clean up existing socket at %s: %v", DVOL_SOCKET, err)
        }
    }
    if _, err := os.Stat(VOL_DIR); err != nil {
        if err := os.MkdirAll(VOL_DIR, 0700); err != nil {
            log.Fatalf("Could not make volumes directory %s: %v", VOL_DIR, err)
        }
    }

    listener, err := net.Listen("unix", DVOL_SOCKET)

    if err != nil {
        log.Fatalf("Could not listen on %s: %v", DVOL_SOCKET, err)
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
        log.Print("<= /VolumeDriver.Remove")
        requestJSON, err := ioutil.ReadAll(r.Body)
        if err != nil {
            log.Fatalf("Unable to read response body %s", err)
        }
        request := new(RequestRemove)
        json.Unmarshal(requestJSON, request)
        name := request.Name
        dvol := api.NewDvolAPI(DVOL_BASE_DIR)
        if dvol.VolumeExists(name) {
            err = dvol.RemoveVolume(name)
            if err != nil {
                WriteResponseErr(err, w)
            } else {
                WriteResponseOK(w)
            }
        } else {
            log.Printf("Requested to remove unknown volume %s", name)
            WriteResponseErr(errors.New("Requested to remove unknown volume " + name), w)
        }
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

        if dvol.VolumeExists(name) {
            err := dvol.SwitchVolume(name)
            if err != nil {
                WriteResponseErr(err, w)
            }
            _, err = dvol.ActiveVolume()
            if err != nil {
                WriteResponseErr(err, w)
            }
            // mountpoint should be:
            // /var/lib/docker/volumes/<volumename>/running_point
            responseJSON, _ := json.Marshal(&ResponseMount{
                Mountpoint: "/tmp", // TODO: Get the real path
                Err: "",
            })
            w.Write(responseJSON)
        } else {
            WriteResponseErr(errors.New("Requested to mount unknown volume " + name), w)
        }
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

