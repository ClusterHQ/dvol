package cmd
import (
    "fmt"
    "path/filepath"
    "os"
    "github.com/spf13/cobra"
    "../datalayer"
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

DEFAULT_BRANCH := "master"

            // TODO Factor this into a data layer object.
            os.MkdirAll(filepath.FromSlash(
                basePath + "/" + volumeName), 0777) // XXX SEC
            os.MkdirAll(filepath.FromSlash(
                basePath + "/" + volumeName + "/branches/master"), 0777) // XXX SEC

var cmdTimes = &cobra.Command{
        Use:   "init",
        Short: "Create a volume and its default master branch, then switch to it",
        Run: func(cmd *cobra.Command, args []string) {
            if(len(args) == 0) {
                fmt.Println("Please specify a volume name.")
                os.Exit(1)
            }
            volumeName = args[0]
            if(!datalayer.ValidVolumeName(volumeName)) {
                fmt.Println("Error: " + volumeName + " is not a valid name")
                os.Exit(1)
            }
            if datalayer.VolumeExists(volumeName) {
                fmt.Println("Error: volume " + volumeName + " already exists")
                os.Exit(1)
            }
            err := datalayer.CreateVolume(volumeName)
            if(err) {
                fmt.Println("Error creating volume")
                os.Exit(1)
            }
            fmt.Println("Created volume", volumeName)

            err := datalayer.CreateVariant(volumeName, "master")
            if(err) {
                fmt.Println("Error creating branch")
                os.Exit(1)
            }
            fmt.Println("Created branch " + volumeName + "/master")
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
