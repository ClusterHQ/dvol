package cmd

import (
	"fmt"
	"io"
	"os"

	"github.com/ClusterHQ/dvol/pkg/api"
	"github.com/spf13/cobra"
)

func NewCmdServer(out io.Writer) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "server",
		Short: "Run a dvol server (also known as a 'volume hub')",
		Run: func(cmd *cobra.Command, args []string) {
			err := runServer(cmd, args, out)
			if err != nil {
				fmt.Fprintln(os.Stderr, err.Error())
				os.Exit(1)
			}
		},
	}
	return cmd
}

func runServer() {}
