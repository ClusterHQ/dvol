package cmd

import (
	"fmt"
	"os"

	"github.com/ClusterHQ/dvol/datalayer"
	"github.com/spf13/cobra"
)

var basePath string
var echoTimes int
var disableDockerIntegration bool

const DEFAULT_BRANCH string = "master"

var RootCmd = &cobra.Command{
	Use:   "dvol",
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
		if len(args) == 0 {
			fmt.Println("Please specify a volume name.")
			os.Exit(1)
		}
		volumeName := args[0]
		if !datalayer.ValidVolumeName(volumeName) {
			fmt.Println("Error: " + volumeName + " is not a valid name")
			os.Exit(1)
		}
		if datalayer.VolumeExists(basePath, volumeName) {
			fmt.Println("Error: volume " + volumeName + " already exists")
			os.Exit(1)
		}
		err := datalayer.CreateVolume(basePath, volumeName)
		if err != nil {
			fmt.Println("Error creating volume")
			os.Exit(1)
		}
		fmt.Println("Created volume", volumeName)

		err = datalayer.CreateVariant(basePath, volumeName, "master")
		if err != nil {
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
		"disable-docker-integration", false, "Do not attempt to list/stop/start"+
			" docker containers which are using dvol volumes")
}