package main

/* memorydiskserver: a testing utility.

the archetypal (worst-case) stateful application. a web server, which:
* loads an integer from a file on disk into memory, if it is present, when
  it starts up
* has an endpoint to set the integer, but only sets it in memory
* writes the integer from memory to disk when asked nicely to shut down (SIGTERM)
* has an endpoint to read the integer from memory

this allows us to test the following cases:
* that docker containers stopped and started cleanly around a commit operation
* that switching branches results in container being stopped and started
  with new on-disk state
* that resetting results in container being stopped and started with new
  on-disk state

this application can be built and copied into a docker image "FROM scratch"
(which involves no network operation)

*/

/*

$ curl -sSL http://localhost/set?value=10
$ curl -sSL http://localhost/get
10
$ dvol commit -m "value=10"
$ curl -sSL http://localhost/set?value=20
$ curl -sSL http://localhost/get
20
$ dvol reset --hard HEAD
$ curl -sSL http://localhost/get
10

*/

import (
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
)

const STORE = "/data/memorydiskserver.dat"

var theValue string

func getHandler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "Value: %s", theValue)
}

func setHandler(w http.ResponseWriter, r *http.Request) {
	theValue = r.URL.Query()["value"][0]
	err := writeValueToDisk()
	if err != nil {
		http.Error(w, fmt.Sprintln(err), http.StatusInternalServerError)
	}
}

func writeValueToDisk() error {
	return ioutil.WriteFile(STORE, []byte(theValue), 0600)
}

//func setHandler(w http.ResponseWriter, r *http.Request) {
//    fmt.Fprintf(w, "Hi there, I love %s!", r.URL.Path[1:])
//}

//func signalHandler(chan c) {
//    // block until we receive a SIGTERM
//    s := <-c
//    writeValueToDisk()
//    os.Exit(0)
//}

func main() {
	// Read the starting value
	dat, err := ioutil.ReadFile(STORE)
	if err != nil {
		f, _ := os.Create(STORE)
		f.Close()
		dat, _ = ioutil.ReadFile(STORE)
	}
	theValue = string(dat)

	http.HandleFunc("/get", getHandler)
	http.HandleFunc("/set", setHandler)

	//    c := make(chan os.Signal, 1)
	//    signal.Notify(c, os.Interrupt)
	//    go signalHandler(c)

	http.ListenAndServe(":80", nil)
}
