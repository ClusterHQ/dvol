package cmd

import (
	"fmt"
	"io"
	"os"

	"github.com/ClusterHQ/dvol/pkg/api"
	"github.com/spf13/cobra"
)

var commitMessage string

func NewCmdCommit(out io.Writer) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "commit",
		Short: "Create a commit on the active volume and branch",
		Run: func(cmd *cobra.Command, args []string) {
			err := commitVolume(cmd, commitMessage, out)
			if err != nil {
				fmt.Fprintln(os.Stderr, err.Error())
				os.Exit(1)
			}
		},
	}
	cmd.PersistentFlags().StringVarP(&commitMessage, "message", "m", "",
		"Commit message")
	return cmd
}

func commitVolume(cmd *cobra.Command, commitMessage string, out io.Writer) error {
	// TODO need to add user's name and email adddress
	dvol := api.NewDvolAPI(basePath)
	activeVolume, err := dvol.ActiveVolume()
	if err != nil {
		return err
	}
	activeBranch, err := dvol.ActiveBranch(activeVolume)
	if err != nil {
		return err
	}
	commitId, err := dvol.Commit(activeVolume, activeBranch, commitMessage)
	if err != nil {
		return err
	}
	fmt.Printf("%s\n", commitId)
	return nil
}
