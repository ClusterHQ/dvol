package cmd

import (
	"path/filepath"
	"fmt"
	"io"
	"net/http"
	"net/http/cgi"
	"os"

	"github.com/spf13/cobra"
)

// TODO: use dvol terminology
// TODO: 'dvol serve' not 'dvol server'

func NewCmdServer(out io.Writer) *cobra.Command {
	var gitBinaryPath string
	cmd := &cobra.Command{
		Use:   "server",
		Short: "Serve a single data set",
		Run: func(cmd *cobra.Command, args []string) {
			if len(args) != 1 {
				fmt.Fprintln(os.Stderr, "Must specify git repository to serve")
				os.Exit(1)
			}
			gitRepoPath, err := filepath.Abs(args[0])
			if err != nil {
				fmt.Fprintf(os.Stderr, "Could not find path to repo: %s\n", args[0])
				os.Exit(1)
			}

			runServer(gitBinaryPath, gitRepoPath)
		},
	}
	cmd.Flags().StringVar(&gitBinaryPath, "git-binary", "/usr/bin/git", "Path to the git binary")
	return cmd
}

func serveData(w http.ResponseWriter, req *http.Request) {
}


func makeCGIHandler(gitBinaryPath, repoPath string) cgi.Handler {
	return cgi.Handler{
		Path: gitBinaryPath,
		Root: "/metadata",
		Dir: repoPath,
		Env: []string{fmt.Sprintf("GIT_PROJECT_ROOT=%s", repoPath)},
		InheritEnv: []string{},
		Logger: nil,
		Args: []string{"http-backend"},
		PathLocationHandler: nil,
	}
}

func serveMetadata(gitBinaryPath, gitRepoPath string, w http.ResponseWriter, req *http.Request) {
	handler := makeCGIHandler(gitBinaryPath, gitRepoPath)
	handler.ServeHTTP(w, req)
}


// XXX: port as arg?
// XXX: git repo path as arg
// XXX: git binary path as arg
func runServer(gitBinaryPath, gitRepoPath string) {
	http.HandleFunc("/data", serveData)
	http.HandleFunc("/metadata/", func(w http.ResponseWriter, r *http.Request) {
		serveMetadata(gitBinaryPath, gitRepoPath, w, r)
	})
	// XXX: this is broken for tests, because we cannot rely on port 8080
	// being open. Instead, listen on 0 (or a UNIX socket?) and print the
	// listening port.
	fmt.Println("Not yet listening on http://localhost:8080 but just about to")
	http.ListenAndServe(":8080", nil)
}
