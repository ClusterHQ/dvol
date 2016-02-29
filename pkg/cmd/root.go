package cmd

import (
	"fmt"
	"os"

	"github.com/ClusterHQ/dvol/pkg/datalayer"
	"github.com/spf13/cobra"
)

var basePath string
var echoTimes int
var disableDockerIntegration bool
var forceRemoveVolume bool

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

var cmdInit = &cobra.Command{
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

var cmdRm = &cobra.Command{
	// TODO: Improve the usage string to include a volume name to remove
	Use:   "rm",
	Short: "Destroy a dvol volume",
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
		if !datalayer.VolumeExists(basePath, volumeName) {
			msg := fmt.Sprintf("Volume '%s' does not exist, cannot remove it", volumeName)
			fmt.Println(msg)
			os.Exit(1)
		}
		err := datalayer.RemoveVolume(basePath, volumeName)
		if err != nil {
			fmt.Println("Error removing volume")
			os.Exit(1)
		}
		s := fmt.Sprintf("Deleting volume '%s'", volumeName)
		fmt.Println(s)
	},
}

func init() {
	// cobra.OnInitialize(initConfig)
	// TODO support: dvol -p <custom_path> init <volume_name>
	RootCmd.AddCommand(cmdInit)
	RootCmd.AddCommand(cmdRm)
	cmdRm.Flags().BoolVarP(&forceRemoveVolume, "force", "f", false, "Force remove")

	RootCmd.PersistentFlags().StringVarP(&basePath, "path", "p", "/var/lib/dvol/volumes",
		"The name of the directory to use")
	RootCmd.PersistentFlags().BoolVar(&disableDockerIntegration,
		"disable-docker-integration", false, "Do not attempt to list/stop/start"+
			" docker containers which are using dvol volumes")
}
