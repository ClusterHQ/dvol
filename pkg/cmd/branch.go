package cmd

import (
	"fmt"
	"io"
	"os"

	"github.com/ClusterHQ/dvol/pkg/api"
	"github.com/spf13/cobra"
)

func NewCmdBranch(out io.Writer) *cobra.Command {
	cmd := &cobra.Command{
		// TODO: Improve the usage string to include a volume name to remove
		Use:   "branch",
		Short: "List branches on the active volume.",
		Run: func(cmd *cobra.Command, args []string) {
			err := listBranches(out)
			if err != nil {
				fmt.Fprintln(os.Stderr, err.Error())
				os.Exit(1)
			}
		},
	}
	return cmd
}

func listBranches(out io.Writer) error {
	dvol := api.NewDvolAPI(basePath)
	activeVolume, avErr := dvol.ActiveVolume()
	if avErr != nil {
		return avErr
	}
	activeBranch, abErr := dvol.ActiveBranch(activeVolume)
	if abErr != nil {
		return abErr
	}
	allBranches, allErr := dvol.AllBranches(activeVolume)
	if allErr != nil {
		return allErr
	}
	for _, branch := range allBranches {
		if branch == activeBranch {
			branch = "* " + branch
		}
		fmt.Fprintln(out, branch)
	}
	return nil
}
