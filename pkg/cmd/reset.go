package cmd

import (
	"fmt"
	"io"
	"os"

	"github.com/ClusterHQ/dvol/pkg/api"
	"github.com/spf13/cobra"
)

var hardReset bool

func NewCmdReset(out io.Writer) *cobra.Command {
	cmd := &cobra.Command{
		// TODO: Improve the usage string to include a volume name to remove
		Use:   "reset",
		Short: "Reset active branch to a commit, destroying later unreferenced commits",
		Run: func(cmd *cobra.Command, args []string) {
			err := resetVolume(cmd, args, out)
			if err != nil {
				fmt.Fprintln(os.Stderr, err.Error())
				os.Exit(1)
			}
		},
	}
	cmd.Flags().BoolVarP(&hardReset, "hard", "", false, "Force removal of newer data (must be set)")
	return cmd
}

func resetVolume(cmd *cobra.Command, args []string, out io.Writer) error {
	dvol := api.NewDvolAPI(dvolAPIOptions)
	if len(args) != 1 {
		return fmt.Errorf("Must specify one and only one commit identifier.")
	}
	commit := args[0]
	if err := dvol.ResetActiveVolume(commit); err != nil {
		return err
	}
	return nil
}
