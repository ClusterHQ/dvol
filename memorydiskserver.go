package main

// memorydiskserver: the archetypal (worst-case) stateful application. a web
// server, which:
// * loads an integer from a file on disk into memory, if it is present, when
//   it starts up
// * has an endpoint to set the integer, but only sets it in memory
// * writes the integer from memory to disk when asked nicely to shut down (SIGTERM)
// * has an endpoint to read the integer from memory
//
// this allows us to test the following cases:
// * that docker containers stopped and started cleanly around a snapshot operation
// * that switching branches results in container being stopped and started
//   with new on-disk state
// * that resetting results in container being stopped and started with new
//   on-disk state
//
// this application can be built and copied into a docker image "FROM scratch"
// (which involves no network operation)

import (
    "fmt"
    "net/http"
)

func getHandler(w http.ResponseWriter, r *http.Request) {
    fmt.Fprintf(w, "Hi there, I love %s!", r.URL.Path[1:])
}

//func setHandler(w http.ResponseWriter, r *http.Request) {
//    fmt.Fprintf(w, "Hi there, I love %s!", r.URL.Path[1:])
//}

//func signalHandler(chan c) {
//    // block until we receive a SIGTERM
//    s := <-c
//    writeIntegerToDisk()
//    os.Exit(0)
//}

func main() {
    http.HandleFunc("/get", getHandler)
    //http.HandleFunc("/set", setHandler)

//    c := make(chan os.Signal, 1)
//    signal.Notify(c, os.Interrupt)
//    go signalHandler(c)

    http.ListenAndServe(":8080", nil)
}
