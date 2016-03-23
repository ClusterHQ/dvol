package cmd

import (
	"fmt"
	"io"
	"os"

	"github.com/ClusterHQ/dvol/pkg/api"
	"github.com/spf13/cobra"
)

func NewCmdLog(out io.Writer) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "log",
		Short: "Show log",
		Run: func(cmd *cobra.Command, args []string) {
			if err := outputLog(out); err != nil {
				fmt.Fprintln(os.Stderr, err.Error())
				os.Exit(1)
			}
		},
	}
	return cmd
}


func outputLog(out io.Writer) error {
	dvol := api.NewDvolAPI(dvolAPIOptions)
	activeVolume, err := dvol.ActiveVolume()
	if err != nil {
		return err
	}

	activeBranch, err := dvol.ActiveBranch(activeVolume)
	if err != nil {
		return err
	}

	commits, err := dvol.ListCommits(activeVolume, activeBranch)
	if err != nil {
		return err
	}
	for i := len(commits) - 1; i >= 0; i-- {
		commit := commits[i]
		fmt.Fprintf(out, "commit %s\n", commit.Id)
		fmt.Fprint(out, "Author: Who knows <mystery@person>\n")
		fmt.Fprint(out, "Date: Whenever\n\n")
		fmt.Fprintf(out, "    %s\n\n", commit.Message)
	}
	return nil
}
