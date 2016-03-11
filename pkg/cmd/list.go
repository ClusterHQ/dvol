package cmd

import (
	"fmt"
	"io"
	"os"
	"strings"
	"text/tabwriter"

	"github.com/ClusterHQ/dvol/pkg/api"
	"github.com/spf13/cobra"
)

func NewCmdList(out io.Writer) *cobra.Command {
	cmd := &cobra.Command{
		Use:     "list",
		Aliases: []string{"ls"},
		Short:   "List all dvol volumes",
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
	dvol := api.NewDvolAPI(basePath)
	if len(args) > 0 {
		return fmt.Errorf("Wrong number of arguments.")
	}

	headers := []string{"  VOLUME", "BRANCH", "CONTAINERS"}

	// These numbers have been picked to make the tests pass and will probably need
	// to be changed.
	writer := tabwriter.NewWriter(out, 2, 4, 3, ' ', 0)
	if _, err := fmt.Fprintf(writer, "%s\n", strings.Join(headers, "\t")); err != nil {
		return err
	}

	volumes, err := dvol.AllVolumes()
	if err != nil {
		return err
	}

	for _, volume := range volumes {
		activeVolume, err := dvol.ActiveVolume()
		if err != nil {
			return err
		}
		prefix := "  "
		if activeVolume == volume.Name {
			prefix = "* "
		}
		branch, err := dvol.CurrentBranch(volume.Name)
		if err != nil {
			return err
		}
		if _, err := fmt.Fprintf(writer, "%s%s\t%s\t\n", prefix, volume.Name, branch); err != nil {
			return err
		}
	}
	writer.Flush()
	return nil
}
