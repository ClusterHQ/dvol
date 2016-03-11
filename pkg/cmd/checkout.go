package cmd

import (
	//"fmt"
	"io"
	//"os"

	//"github.com/ClusterHQ/dvol/pkg/api"
	"github.com/spf13/cobra"
)

var createBranch bool

func NewCmdCheckout(out io.Writer) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "checkout",
		Short: "Check out or create branches on the active volume",
		Run: func(cmd *cobra.Command, args []string) {
			/*err := checkoutBranch(cmd, args, out)
			if err != nil {
				fmt.Fprintln(os.Stderr, err.Error())
				os.Exit(1)
			}*/
		},
	}
	cmd.Flags().BoolVarP(&createBranch, "branch", "b", false, "Create branch")
	return cmd
}

/*
func checkoutBranch(cmd *cobra.Command, args []string, out io.Writer) error {
	dvol := api.NewDvolAPI(basePath)
	err := checkBranchArgs(args)
	if err != nil {
		return err
	}
	branchName := args[0]
	if !api.ValidName(branchName) {
		return fmt.Errorf("Error: " + branchName + " is not a valid name")
	}
	err = dvol.CheckoutBranch(branchName)
	fmt.Printf("%s: %s\n", branchName, err)
	return dvol.CheckoutBranch(branchName)
}
*/
