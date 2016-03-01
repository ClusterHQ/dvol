package cmd

import (
	"fmt"
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

func NewCmdRm() *cobra.Command {
	cmd := &cobra.Command{
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
			if forceRemoveVolume || userIsSure("This will remove all containers using the volume") {
				s := fmt.Sprintf("Deleting volume '%s'", volumeName)
				fmt.Println(s)
				err := datalayer.RemoveVolume(basePath, volumeName)
				if err != nil {
					fmt.Println("Error removing volume")
					os.Exit(1)
				}
			} else {
				fmt.Println("Aborting.")
			}
		},
	}
	cmd.Flags().BoolVarP(&forceRemoveVolume, "force", "f", false, "Force remove")
	return cmd
}
