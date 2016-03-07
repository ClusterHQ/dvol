package cmd

import (
	"fmt"
	"io"
	"os"

	"github.com/ClusterHQ/dvol/pkg/datalayer"
	"github.com/spf13/cobra"
)

func NewCmdInit(out io.Writer) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "init",
		Short: "Create a volume and its default master branch, then switch to it",
		Run: func(cmd *cobra.Command, args []string) {
			err := initVolume(cmd, args, out)
			if err != nil {
				fmt.Fprintln(os.Stderr, err.Error())
				os.Exit(1)
			}
		},
	}
	return cmd
}

func initVolume(cmd *cobra.Command, args []string, out io.Writer) error {
	err := checkVolumeArgs(args)
	if err != nil {
		return err
	}
	volumeName := args[0]
	if !datalayer.ValidName(volumeName) {
		return fmt.Errorf("Error: " + volumeName + " is not a valid name")
	}
	if dl.VolumeExists(volumeName) {
		return fmt.Errorf("Error: volume " + volumeName + " already exists")
	}
	err = dl.CreateVolume(volumeName)
	if err != nil {
		return fmt.Errorf("Error creating volume")
	}
	fmt.Fprintln(out, "Created volume", volumeName)

	err = dl.CreateVariant(volumeName, "master")
	if err != nil {
		return fmt.Errorf("Error creating branch")
	}
	fmt.Fprintln(out, "Created branch "+volumeName+"/master")
	return nil
}
