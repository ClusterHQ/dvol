package cmd
import (
    "fmt"
    "path/filepath"
    "os"
    "github.com/spf13/cobra"
)

var basePath string
var echoTimes int
var disableDockerIntegration bool

var RootCmd = &cobra.Command {
    Use: "dvol",
    Short: "dvol is a version control system for your development data in Docker",
    Long: `dvol
====
dvol lets you commit, reset and branch the containerized databases
running on your laptop so you can easily save a particular state
and come back to it later.`,
}

var cmdTimes = &cobra.Command{
        Use:   "init",
        Short: "Create a volume and its default master branch, then switch to it",
        Run: func(cmd *cobra.Command, args []string) {
            if(len(args) == 0) {
                fmt.Println("Please specify a volume name.")
                return
            }
            fmt.Println("Created volume", args[0])
            fmt.Println("Created branch " + args[0] + "/master")
            // TODO Factor this into a data layer object.
            os.MkdirAll(filepath.FromSlash(
                basePath + "/" + args[0]), 0777) // XXX SEC
            os.MkdirAll(filepath.FromSlash(
                basePath + "/" + args[0] + "/branches/master"), 0777) // XXX SEC
        },
    }

func init() {
    // cobra.OnInitialize(initConfig)
    // TODO support: dvol -p <custom_path> init <volume_name>
    RootCmd.AddCommand(cmdTimes)

    RootCmd.PersistentFlags().StringVarP(&basePath, "path", "p", "/var/lib/dvol/volumes",
        "The name of the directory to use")
    RootCmd.PersistentFlags().BoolVar(&disableDockerIntegration,
        "disable-docker-integration", false, "Do not attempt to list/stop/start" +
        " docker containers which are using dvol volumes")
}
