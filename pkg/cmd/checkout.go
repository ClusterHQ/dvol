package cmd

import (
	"fmt"
	"io"
	"os"

	"github.com/ClusterHQ/dvol/pkg/api"
	"github.com/spf13/cobra"
)

var createBranch bool

func NewCmdCheckout(out io.Writer) *cobra.Command {
	cmd := &cobra.Command{
		// TODO: Improve the usage string to include a volume name to remove
		Use:   "checkout",
		Short: "TODO",
		Run: func(cmd *cobra.Command, args []string) {
			err := checkoutBranch(cmd, args, out)
			if err != nil {
				fmt.Fprintln(os.Stderr, err.Error())
				os.Exit(1)
			}
		},
	}
	cmd.Flags().BoolVarP(&createBranch, "branch", "b", false, "TODO MSG")
	return cmd
}

func checkoutBranch(cmd *cobra.Command, args []string, out io.Writer) error {
	dvol := api.NewDvolAPI(dvolAPIOptions)
	if len(args) != 1 {
		return fmt.Errorf("Must specify a branch name.")
	}
	branchName := args[0]
	activeVolume, err := dvol.ActiveVolume()
	if err != nil {
		return err
	}
	activeBranch, err := dvol.ActiveBranch(activeVolume)
	if err != nil {
		return err
	}
	if err := dvol.CheckoutBranch(activeVolume, activeBranch, branchName, createBranch); err != nil {
		return err
	}
	return nil
}
