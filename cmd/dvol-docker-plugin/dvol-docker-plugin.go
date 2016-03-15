package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net"
	"net/http"
	"os"

	"github.com/ClusterHQ/dvol/pkg/api"
)

const PLUGINS_DIR = "/run/docker/plugins"
const DVOL_SOCKET = PLUGINS_DIR + "/dvol.sock"
const VOL_DIR = "/var/lib/dvol/volumes"

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
	Err        string
}

type ResponseListVolume struct {
	// Used in the JSON representation of ResponseList
	Name       string
	Mountpoint string
}
type ResponseList struct {
	// A response which enumerates volumes for VolumeDriver.List
	Volumes []ResponseListVolume
	Err     string
}

func main() {
	log.Print("Starting dvol plugin")

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
		dvol := api.NewDvolAPI(api.DvolAPIOptions{
			BasePath: VOL_DIR,
		})
		if dvol.VolumeExists(name) {
			log.Print("Volume already exists ", name)
		} else {
			err := dvol.CreateVolume(name)
			if err != nil {
				writeResponseErr(fmt.Errorf("Could not create volume %s: %v", name, err), w)
				return
			}
		}
		writeResponseOK(w)
	})

	http.HandleFunc("/VolumeDriver.Remove", func(w http.ResponseWriter, r *http.Request) {
		/*
			We do not actually want to remove the dvol volume when Docker references to them are removed.

			This is a no-op.
		*/
		writeResponseOK(w)
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

		dvol := api.NewDvolAPI(api.DvolAPIOptions{
			BasePath: VOL_DIR,
		})

		if dvol.VolumeExists(name) {
			err := dvol.SwitchVolume(name)
			if err != nil {
				writeResponseErr(err, w)
			}
			_, err = dvol.ActiveVolume()
			if err != nil {
				writeResponseErr(err, w)
			}
			// mountpoint should be:
			// /var/lib/docker/volumes/<volumename>/running_point
			responseJSON, _ := json.Marshal(&ResponseMount{
				Mountpoint: "/tmp", // TODO: Get the real path
				Err:        "",
			})
			w.Write(responseJSON)
		} else {
			writeResponseErr(fmt.Errorf("Requested to mount unknown volume %s", name), w)
		}
	})

	http.HandleFunc("/VolumeDriver.Unmount", func(w http.ResponseWriter, r *http.Request) {
		writeResponseOK(w)
	})

	http.HandleFunc("/VolumeDriver.List", volumeDriverList)

	listener, err := net.Listen("unix", DVOL_SOCKET)
	if err != nil {
		log.Fatalf("Could not listen on %s: %v", DVOL_SOCKET, err)
	}

	http.Serve(listener, nil)
}

func volumeDriverList(w http.ResponseWriter, r *http.Request) {
	log.Print("<= /VolumeDriver.List")
	dvol := api.NewDvolAPI(api.DvolAPIOptions{
		BasePath: VOL_DIR,
	})

	allVolumes, err := dvol.AllVolumes()
	if err != nil {
		writeResponseErr(err, w)
	}

	var response = ResponseList{
		Err: "",
	}
	for _, volume := range allVolumes {
		response.Volumes = append(response.Volumes, ResponseListVolume{
			Name:       volume.Name,
			Mountpoint: volume.Path,
		})
	}

	responseJSON, _ := json.Marshal(response)
	w.Write(responseJSON)
}

func writeResponseOK(w http.ResponseWriter) {
	// A shortcut to writing a ResponseOK to w
	responseJSON, _ := json.Marshal(&ResponseSimple{Err: ""})
	w.Write(responseJSON)
}

func writeResponseErr(err error, w http.ResponseWriter) {
	// A shortcut to responding with an error, and then log the error
	errString := fmt.Sprintln(err)
	log.Printf("Error: %v", err)
	responseJSON, _ := json.Marshal(&ResponseSimple{Err: errString})
	w.Write(responseJSON)
}
