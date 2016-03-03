package cmd

import (
	"fmt"
	"io"
	"os"

	"github.com/spf13/cobra"
)

func NewCmdList(out io.Writer) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List all dvol volumes",
		Run: func(cmd *cobra.Command, args []string) {
			err := listVolumes(cmd, args, out)
			if err != nil {
				fmt.Fprintln(os.Stderr, err.Error())
				os.Exit(1)
			}
		},
	}
	return cmd
}

func listVolumes(cmd *cobra.Command, args []string, out io.Writer) error {
	if len(args) > 0 {
		return fmt.Errorf("Wrong number of arguments.")
	}
	return nil
}
