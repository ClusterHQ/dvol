package cmd

import (
	"fmt"
	"io"
	"os"

	"github.com/ClusterHQ/dvol/pkg/datalayer"
	"github.com/spf13/cobra"
)

func NewCmdSwitch() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "switch",
		Short: "Switch active volume for commands below (commit, log etc)",
		Run: func(cmd *cobra.Command, args []string) {
			switchVolume(cmd, args, os.Stdout)
		},
	}
	return cmd
}

func switchVolume(cmd *cobra.Command, args []string, out io.Writer) error {

	if len(args) == 0 {
		fmt.Println("Please specify a volume name.")
		os.Exit(1)
	}
	if len(args) > 1 {
		fmt.Println("Wrong number of arguments.")
		os.Exit(1)
	}
	volumeName := args[0]
	if !datalayer.ValidVolumeName(volumeName) {
		fmt.Println("Error: " + volumeName + " is not a valid name")
		os.Exit(1)
	}
	if !datalayer.VolumeExists(basePath, volumeName) {
		fmt.Println("Error: " + volumeName + " does not exist")
		os.Exit(1)
	}
	err := datalayer.SwitchVolume(basePath, volumeName)
	if err != nil {
		fmt.Println("Error switching volume")
		os.Exit(1)
	}
	return nil
}
