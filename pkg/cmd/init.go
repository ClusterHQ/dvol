package cmd

import (
	"fmt"
	"os"

	"github.com/ClusterHQ/dvol/pkg/datalayer"
	"github.com/spf13/cobra"
)

func NewCmdInit() *cobra.Command {
	cmd := &cobra.Command{
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
	return cmd
}
