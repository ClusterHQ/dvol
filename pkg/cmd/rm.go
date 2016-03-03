package cmd

import (
	"fmt"
	"io"
	"os"
	"strings"

	"github.com/ClusterHQ/dvol/pkg/datalayer"
	"github.com/spf13/cobra"
)

var forceRemoveVolume bool

func userIsSure(extraMessage string) bool {
	message := fmt.Sprintf("Are you sure? %s (y/n): ", extraMessage)
	fmt.Print(message)
	var response string
	_, err := fmt.Scanln(&response)
	if err != nil {
		fmt.Println("Error reading response.")
		return false
	}
	response = strings.ToLower(response)
	if response == "y" || response == "yes" {
		return true
	}
	return false
}

func NewCmdRm(out io.Writer) *cobra.Command {
	cmd := &cobra.Command{
		// TODO: Improve the usage string to include a volume name to remove
		Use:   "rm",
		Short: "Destroy a dvol volume",
		Run: func(cmd *cobra.Command, args []string) {
			err := removeVolume(cmd, args, out)
			if err != nil {
				fmt.Fprintln(os.Stderr, err.Error())
				os.Exit(1)
			}
		},
	}
	cmd.Flags().BoolVarP(&forceRemoveVolume, "force", "f", false, "Force remove")
	return cmd
}

func removeVolume(cmd *cobra.Command, args []string, out io.Writer) error {

	if len(args) == 0 {
		return fmt.Errorf("Please specify a volume name.")
	}
	if len(args) > 1 {
		return fmt.Errorf("Wrong number of arguments.")
	}
	volumeName := args[0]
	if !datalayer.ValidVolumeName(volumeName) {
		return fmt.Errorf("Error: " + volumeName + " is not a valid name")
	}
	if !datalayer.VolumeExists(basePath, volumeName) {
		msg := fmt.Sprintf("Volume '%s' does not exist, cannot remove it", volumeName)
		return fmt.Errorf(msg)
	}
	if forceRemoveVolume || userIsSure("This will remove all containers using the volume") {
		s := fmt.Sprintf("Deleting volume '%s'", volumeName)
		fmt.Fprintln(out, s)
		err := datalayer.RemoveVolume(basePath, volumeName)
		if err != nil {
			return fmt.Errorf("Error removing volume")
		}
	} else {
		fmt.Fprintln(out, "Aborting.")
	}
	return nil
}
