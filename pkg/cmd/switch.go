package cmd

import (
	"fmt"
	"io"
	"os"

	"github.com/ClusterHQ/dvol/pkg/datalayer"
	"github.com/spf13/cobra"
)

func NewCmdSwitch(out io.Writer) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "switch",
		Short: "Switch active volume for commands below (commit, log etc)",
		Run: func(cmd *cobra.Command, args []string) {
			err := switchVolume(cmd, args, out)
			if err != nil {
				fmt.Fprintln(os.Stderr, err.Error())
				os.Exit(1)
			}
		},
	}
	return cmd
}

func switchVolume(cmd *cobra.Command, args []string, out io.Writer) error {
	err := checkVolumeArgs(args)
	if err != nil {
		return err
	}
	volumeName := args[0]
	if !datalayer.ValidVolumeName(volumeName) {
		return fmt.Errorf("Error: " + volumeName + " is not a valid name")
	}
	if !datalayer.VolumeExists(basePath, volumeName) {
		return fmt.Errorf("Error: " + volumeName + " does not exist")
	}
	err = datalayer.SwitchVolume(basePath, volumeName)
	if err != nil {
		return fmt.Errorf("Error switching volume")
	}
	return nil
}
