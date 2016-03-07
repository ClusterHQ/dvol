package cmd

import (
	"fmt"
	"io"
	"os"
	"strings"
	"text/tabwriter"

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

	headers := []string{"  VOLUME", "BRANCH", "CONTAINERS"}

	// These numbers have been picked to make the tests pass and will probably need
	// to be changed.
	writer := tabwriter.NewWriter(out, 8, 0, 3, ' ', 0)
	if _, err := fmt.Fprintf(writer, "%s\n", strings.Join(headers, "\t")); err != nil {
		return err
	}
	writer.Flush()
	return nil
}
